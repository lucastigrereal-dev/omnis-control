"""Mission Package Builder — orquestrador de missao completa via P10 API publica."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src.mission.models import MissionContext, MissionPackage
from src.mission.adapter import MissionToWorkOrderAdapter
from src.mission_builder.models import MissionPlan
from src.missions.models import MissionContract


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log_entry(level: str, message: str) -> dict:
    return {
        "timestamp": _now_iso(),
        "level": level,
        "message": message,
    }


class MissionPackageBuilder:
    """Orquestrador de missao completa.

    USA P10 como motor de output. NUNCA reimplementa writers, manifest,
    validacao ou batch.
    """

    def __init__(
        self,
        packages_root: Path | None = None,
        work_orders_root: Path | None = None,
        outputs_root: Path | None = None,
        approvals_log: Path | None = None,
        mission_log: Path | None = None,
    ):
        self.packages_root = packages_root or Path("exports/mission_packages")
        self.work_orders_root = work_orders_root or Path("exports/work_orders")
        self.outputs_root = outputs_root or Path("exports/generated_outputs")
        self.approvals_log = approvals_log or Path("exports/approvals/approvals.jsonl")
        self.mission_log = mission_log or Path("exports/mission_packages/mission.log.jsonl")

        self._adapter = MissionToWorkOrderAdapter(work_orders_root=self.work_orders_root)

    # ── Fase 1: Entrada ──

    def from_mission_plan(self, plan: MissionPlan) -> MissionPackage:
        """Cria MissionPackage a partir de um MissionPlan (P2).

        Extrai account_handle, intent, steps e gera Work Orders.
        """
        ctx = MissionContext(
            mission_id=plan.mission_id,
            plan=plan.to_dict(),
        )
        work_orders = self._adapter.plan_to_work_orders(plan)

        package = MissionPackage(
            mission_id=plan.mission_id,
            context=ctx,
            work_orders=work_orders,
            status="draft",
        )
        package.logs.append(_log_entry("INFO", f"MissionPackage criado a partir de MissionPlan: {plan.mission_id}"))
        return package

    def from_mission_contract(self, contract: MissionContract) -> MissionPackage:
        """Cria MissionPackage a partir de um MissionContract (P3).

        Le acceptance_criteria, expected_deliverables, budget, sector.
        """
        mission_id = f"mc_{contract.content_hash()[:12]}"
        ctx = MissionContext(
            mission_id=mission_id,
            contract=contract.model_dump(mode="json"),
        )
        work_orders = self._adapter.contract_to_work_orders(contract)

        package = MissionPackage(
            mission_id=mission_id,
            context=ctx,
            work_orders=work_orders,
            status="draft",
        )
        package.logs.append(_log_entry("INFO", f"MissionPackage criado a partir de MissionContract: {mission_id}"))
        return package

    # ── Fase 2: Execucao ──

    def build(self, package: MissionPackage, dry_run: bool = True) -> MissionPackage:
        """Orquestra a geracao de todos os outputs da missao.

        1. Escreve work_orders em disco (formato P10)
        2. Itera sobre work_orders do MissionPackage
        3. Para cada WO: chama self._adapter.execute_work_order() → P10.orchestrate()
        4. Coleta resultados em output_packages
        5. Se !dry_run: chama prepare_submission() para cada WO
        6. Atualiza status do MissionPackage
        """
        if not package.work_orders:
            package.logs.append(_log_entry("WARN", "Nenhuma Work Order para build"))
            package.status = "done"
            return package

        package.status = "generating"
        package.logs.append(_log_entry("INFO", f"Iniciando build para {len(package.work_orders)} Work Orders (dry_run={dry_run})"))

        self._adapter.write_work_orders(package.work_orders)

        package.output_packages = []
        package.manifest_registry_entries = []
        package.approval_requests = []

        for wo in package.work_orders:
            wo_id = wo["work_order_id"]

            try:
                result = self._adapter.execute_work_order(wo_id, outputs_root=self.outputs_root)
                package.output_packages.append(result)
                package.logs.append(_log_entry("INFO", f"WO {wo_id}: valid={result.get('valid')}, registered={result.get('registered')}"))

                for entry_dict in result.get("validation_checks", []):
                    if isinstance(entry_dict, dict):
                        package.manifest_registry_entries.append(entry_dict)

            except Exception as e:
                package.logs.append(_log_entry("ERROR", f"WO {wo_id} falhou: {e}"))
                package.output_packages.append({
                    "work_order_id": wo_id,
                    "error": str(e),
                    "valid": False,
                })

            if not dry_run:
                try:
                    approval_result = self._submit_single_approval(wo_id)
                    package.approval_requests.append(approval_result)
                except Exception as e:
                    package.logs.append(_log_entry("ERROR", f"Aprovacao WO {wo_id} falhou: {e}"))

        package.updated_at = _now_iso()
        package.status = "validating"
        package.logs.append(_log_entry("INFO", f"Build concluido: {len(package.output_packages)} outputs gerados"))

        return package

    def _submit_single_approval(self, work_order_id: str) -> dict:
        """Submete um unico WO para aprovacao usando P10.prepare_submission()."""
        from src.output_generator.approval_bridge import prepare_submission
        from src.output_generator.manifest_registry import ManifestRegistry

        registry = ManifestRegistry(registry_path=self.outputs_root / "output_registry.jsonl")
        return prepare_submission(
            work_order_id=work_order_id,
            registry=registry,
            approvals_log=self.approvals_log,
            dry_run=False,
        )

    # ── Fase 3: Validacao ──

    def validate(self, package: MissionPackage) -> dict:
        """Validacao agregada de todos os outputs da missao.

        Retorna: {mission_id, overall_valid, wo_count, wo_valid_count,
                  wo_failed_count, checks_aggregated, issues, warnings}
        """
        wo_count = len(package.output_packages)
        wo_valid_count = sum(1 for o in package.output_packages if o.get("valid"))
        wo_failed_count = wo_count - wo_valid_count

        all_checks = []
        all_issues = []
        all_warnings = []

        for op in package.output_packages:
            for check in op.get("validation_checks", []):
                if isinstance(check, dict):
                    all_checks.append(check)
            for issue in op.get("validation_issues", []):
                all_issues.append(issue)
            for warning in op.get("validation_warnings", []):
                all_warnings.append(warning)

        result = {
            "mission_id": package.mission_id,
            "overall_valid": wo_failed_count == 0 and wo_count > 0,
            "wo_count": wo_count,
            "wo_valid_count": wo_valid_count,
            "wo_failed_count": wo_failed_count,
            "checks_aggregated": all_checks,
            "issues": all_issues,
            "warnings": all_warnings,
        }

        package.logs.append(_log_entry("INFO", f"Validacao: overall_valid={result['overall_valid']}, {wo_valid_count}/{wo_count} WOs validas"))
        package.status = "approved" if result["overall_valid"] else "draft"
        package.updated_at = _now_iso()

        return result

    # ── Fase 4: Aprovacao ──

    def submit_for_approval(self, package: MissionPackage, dry_run: bool = True) -> dict:
        """Submete TODOS os outputs ao approval_center.

        Agrega resultados de prepare_submission() por WO.
        Retorna: {mission_id, submissions: [...], all_approved, dry_run}
        """
        submissions = []
        for wo in package.work_orders:
            wo_id = wo["work_order_id"]
            try:
                from src.output_generator.approval_bridge import prepare_submission
                from src.output_generator.manifest_registry import ManifestRegistry

                registry = ManifestRegistry(registry_path=self.outputs_root / "output_registry.jsonl")
                sub = prepare_submission(
                    work_order_id=wo_id,
                    registry=registry,
                    approvals_log=self.approvals_log,
                    dry_run=dry_run,
                )
                submissions.append(sub)
            except Exception as e:
                submissions.append({
                    "work_order_id": wo_id,
                    "error": str(e),
                    "dry_run": dry_run,
                })

        all_approved = all(
            s.get("approval_request") is not None or s.get("valid")
            for s in submissions
        )

        result = {
            "mission_id": package.mission_id,
            "submissions": submissions,
            "all_approved": all_approved,
            "dry_run": dry_run,
        }

        package.approval_requests = submissions
        package.logs.append(_log_entry("INFO", f"Aprovacao submetida: {len(submissions)} WOs, all_approved={all_approved}"))
        package.updated_at = _now_iso()

        return result

    # ── Fase 5: Relatorio ──

    def closeout(self, package: MissionPackage) -> dict:
        """Compila relatorio final da missao.

        Retorna: {mission_id, total_wo, total_outputs, total_files,
                  total_approvals, duration_seconds, status, issues, learning_notes}
        """
        total_wo = len(package.work_orders)
        total_outputs = len(package.output_packages)
        total_files = sum(
            len(op.get("outputs", []))
            for op in package.output_packages
        )
        total_approvals = len(package.approval_requests)

        all_issues = []
        for op in package.output_packages:
            for issue in op.get("validation_issues", []):
                all_issues.append(issue)
            for blocker in op.get("blockers", []):
                if blocker:
                    all_issues.append(blocker)

        try:
            start_ts = datetime.fromisoformat(package.created_at.replace("Z", "+00:00"))
            end_ts = datetime.fromisoformat(package.updated_at.replace("Z", "+00:00"))
            duration = (end_ts - start_ts).total_seconds()
        except Exception:
            duration = 0.0

        report = {
            "mission_id": package.mission_id,
            "total_wo": total_wo,
            "total_outputs": total_outputs,
            "total_files": total_files,
            "total_approvals": total_approvals,
            "duration_seconds": duration,
            "status": package.status,
            "issues": all_issues,
            "learning_notes": [],
        }

        package.closeout = report
        package.status = "done"
        package.updated_at = _now_iso()
        package.logs.append(_log_entry("INFO", f"Closeout: {total_wo} WOs, {total_files} files, status={package.status}"))

        return report

    # ── Persistencia ──

    def save(self, package: MissionPackage) -> Path:
        """Persiste MissionPackage completo em disco.

        Escreve mission_package.json + approvals.jsonl + mission.log.jsonl
        Retorna o path do diretorio do pacote.
        """
        pkg_dir = self.packages_root / package.mission_id
        pkg_dir.mkdir(parents=True, exist_ok=True)

        pkg_json = pkg_dir / "mission_package.json"
        package.to_json(pkg_json)

        if package.approval_requests:
            approvals_path = pkg_dir / "approvals.jsonl"
            with open(approvals_path, "a", encoding="utf-8") as f:
                for req in package.approval_requests:
                    f.write(json.dumps(req, ensure_ascii=False) + "\n")

        log_path = pkg_dir / "mission.log.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            for log in package.logs:
                f.write(json.dumps(log, ensure_ascii=False) + "\n")

        package.logs.append(_log_entry("INFO", f"MissionPackage salvo em {pkg_dir}"))
        package.updated_at = _now_iso()

        return pkg_dir

    def load(self, mission_id: str, packages_root: Path | None = None) -> MissionPackage:
        """Carrega MissionPackage do disco."""
        root = packages_root or self.packages_root
        pkg_path = root / mission_id / "mission_package.json"
        if not pkg_path.exists():
            raise FileNotFoundError(f"MissionPackage nao encontrado: {pkg_path}")
        return MissionPackage.from_json(pkg_path)
