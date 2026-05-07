"""Tool Registry — storage JSONL + operacoes CRUD. P0.8."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.tool_registry.models import ToolRecord, ToolStatus
from src.tool_registry.errors import DuplicateToolError, ToolNotFoundError
from src.tool_registry.healthcheck import (
    ToolHealthResult,
    HealthStatus,
    run_healthcheck_for,
    is_healthcheck_allowed,
    get_checker_name,
)


class ToolRegistry:
    """Storage file-based para Tool Records."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is None:
            base_dir = os.path.expanduser("~/omnis-control/data/tool_registry")
        self.base_dir = Path(base_dir)
        self.tools_path = self.base_dir / "tools.jsonl"
        self.log_path = self.base_dir / "validation_log.jsonl"
        self.healthcheck_log_path = self.base_dir / "healthcheck_log.jsonl"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ── CRUD ────────────────────────────────────────────────────────

    def add_tool(self, record: ToolRecord) -> ToolRecord:
        """Adiciona ferramenta. Levanta DuplicateToolError se tool_id ja existe."""
        if self._exists(record.tool_id):
            raise DuplicateToolError(
                f"Ferramenta '{record.tool_id}' ja registrada. Use update_tool() para modificar."
            )
        self._write_tool(record)
        return record

    def get_tool(self, tool_id: str) -> Optional[ToolRecord]:
        """Busca ferramenta por tool_id. Retorna None se nao encontrada."""
        for r in self._read_all():
            if r.tool_id == tool_id:
                return r
        return None

    def list_tools(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[ToolRecord]:
        """Lista ferramentas com filtros opcionais."""
        results = self._read_all()
        if status:
            results = [r for r in results if r.status == status]
        if category:
            results = [r for r in results if r.category == category]
        return results

    def update_tool(self, tool_id: str, **fields) -> Optional[ToolRecord]:
        """Atualiza campos de uma ferramenta existente."""
        records = self._read_all()
        updated = None
        for r in records:
            if r.tool_id == tool_id:
                data = r.model_dump()
                data.update(fields)
                data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                updated = ToolRecord(**data)
                break

        if updated is None:
            return None

        self._write_all(records, tool_id, updated)
        return updated

    def update_status(
        self,
        tool_id: str,
        status: str,
        validation_status: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[ToolRecord]:
        """Atualiza status com registro em validation_log."""
        fields = {"status": status}
        if validation_status is not None:
            fields["validation_status"] = validation_status
            fields["last_validated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if notes is not None:
            fields["notes"] = notes

        result = self.update_tool(tool_id, **fields)

        # Append to validation log
        if result is not None:
            log_entry = {
                "tool_id": tool_id,
                "previous_status": self._get_previous_status(tool_id, result.status),
                "new_status": status,
                "validation_status": validation_status,
                "notes": notes or "",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=True, separators=(",", ":")) + "\n")

        return result

    def mark_validated(
        self,
        tool_id: str,
        validation_status: str,
        notes: Optional[str] = None,
    ) -> Optional[ToolRecord]:
        """Marca ferramenta como validada (sem alterar status operacional)."""
        record = self.get_tool(tool_id)
        if record is None:
            return None
        return self.update_status(
            tool_id,
            status=record.status,
            validation_status=validation_status,
            notes=notes,
        )

    def tools_by_status(self) -> Dict[str, int]:
        """Contagem de ferramentas por status."""
        counts: Dict[str, int] = {}
        for r in self._read_all():
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts

    def tools_by_category(self) -> Dict[str, int]:
        """Contagem de ferramentas por categoria."""
        counts: Dict[str, int] = {}
        for r in self._read_all():
            counts[r.category] = counts.get(r.category, 0) + 1
        return counts

    def get_validation_log(self, tool_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Retorna entradas do validation log."""
        if not self.log_path.exists():
            return []
        entries: List[Dict[str, Any]] = []
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entry = json.loads(stripped)
                    if tool_id is None or entry.get("tool_id") == tool_id:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue
        return entries[-limit:]

    # ── Healthcheck ──────────────────────────────────────────────────

    def run_healthcheck(self, tool_id: str) -> Optional[ToolHealthResult]:
        """Executa healthcheck read-only para uma ferramenta.

        Atualiza last_validated_at e validation_status no registro.
        Persiste resultado em healthcheck_log.jsonl.
        """
        record = self.get_tool(tool_id)
        if record is None:
            return None

        status_before = record.status
        result = run_healthcheck_for(tool_id, status_before)

        # Determina novo status baseado no healthcheck
        new_status = self._derive_status_from_health(result, record)
        result.status_after = new_status

        # Atualiza registro
        self.update_tool(
            tool_id,
            validation_status=result.health_status,
            last_validated_at=result.checked_at,
            status=new_status,
        )

        # Persiste healthcheck log
        self._write_healthcheck_log(result)

        # Emite metrica
        try:
            from src.metrics import quick_record_metric
            metric_name = (
                "tool_healthcheck_completed"
                if result.health_status == HealthStatus.OK
                else "tool_healthcheck_failed"
            )
            quick_record_metric(
                metric_name, 1,
                tool_id=tool_id,
                event_type=metric_name,
                metadata={
                    "health_status": result.health_status,
                    "duration_ms": result.duration_ms,
                    "status_before": result.status_before,
                    "status_after": result.status_after,
                },
            )
        except Exception:
            pass

        return result

    def run_all_healthchecks(self) -> List[ToolHealthResult]:
        """Executa healthcheck para todas as ferramentas registradas com checker.

        Pula ferramentas sem checker definido (manual/externo).
        """
        results: List[ToolHealthResult] = []
        all_tools = self.list_tools()

        for tool in all_tools:
            tool_id = tool.tool_id
            if not is_healthcheck_allowed(tool_id):
                continue
            if get_checker_name(tool_id) is None:
                # Ferramenta conhecida mas sem checker — registra not_checked
                continue
            result = self.run_healthcheck(tool_id)
            if result is not None:
                results.append(result)

        return results

    def get_last_healthcheck(self, tool_id: str) -> Optional[ToolHealthResult]:
        """Retorna ultimo healthcheck registrado para a ferramenta."""
        if not self.healthcheck_log_path.exists():
            return None

        last_entry = None
        with open(self.healthcheck_log_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entry = json.loads(stripped)
                    if entry.get("tool_id") == tool_id:
                        last_entry = entry
                except json.JSONDecodeError:
                    continue

        if last_entry is None:
            return None

        return ToolHealthResult(**last_entry)

    def get_healthcheck_report(self) -> List[Dict[str, Any]]:
        """Relatorio do ultimo healthcheck para cada ferramenta registrada."""
        report: List[Dict[str, Any]] = []
        all_tools = self.list_tools()

        for tool in all_tools:
            last = self.get_last_healthcheck(tool.tool_id)
            report.append({
                "tool_id": tool.tool_id,
                "name": tool.name,
                "status": tool.status,
                "health_status": last.health_status if last else HealthStatus.NOT_CHECKED,
                "last_checked": last.checked_at if last else None,
                "message": last.message if last else "Nunca verificado",
                "recommendation": last.recommendation if last else "",
            })

        return report

    def _derive_status_from_health(
        self, result: ToolHealthResult, record: ToolRecord
    ) -> str:
        """Deriva novo status operacional baseado no resultado do healthcheck."""
        # Nunca promove para automatic nesta fase
        if result.health_status == HealthStatus.OK:
            if record.status in (ToolStatus.BLOCKED, ToolStatus.NOT_CONFIGURED):
                # So promove se estava bloqueado/nao configurado
                # e o checker confirmou que funciona
                if record.status == ToolStatus.BLOCKED:
                    return ToolStatus.READ_ONLY
            return record.status  # mantem status atual

        if result.health_status == HealthStatus.DEGRADED:
            if record.status in (ToolStatus.READ_ONLY, ToolStatus.DRY_RUN):
                return ToolStatus.BLOCKED
            return record.status

        if result.health_status == HealthStatus.BLOCKED:
            return ToolStatus.BLOCKED

        if result.health_status in (HealthStatus.FAILED,):
            return ToolStatus.BLOCKED

        # not_checked, not_configured — mantem
        return record.status

    def _write_healthcheck_log(self, result: ToolHealthResult) -> None:
        """Append resultado ao healthcheck log JSONL."""
        data = result.model_dump()
        line = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
        with open(self.healthcheck_log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    # ── Internals ───────────────────────────────────────────────────

    def _exists(self, tool_id: str) -> bool:
        return self.get_tool(tool_id) is not None

    def _read_all(self) -> List[ToolRecord]:
        if not self.tools_path.exists():
            return []
        records: List[ToolRecord] = []
        with open(self.tools_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                    records.append(ToolRecord(**data))
                except (json.JSONDecodeError, Exception):
                    continue
        return records

    def _write_tool(self, record: ToolRecord) -> None:
        line = json.dumps(record.model_dump(), ensure_ascii=True, separators=(",", ":"))
        with open(self.tools_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _write_all(self, records: List[ToolRecord], tool_id: str, updated: ToolRecord) -> None:
        """Reescreve arquivo substituindo tool_id por updated."""
        lines = []
        for r in records:
            if r.tool_id == tool_id:
                lines.append(json.dumps(updated.model_dump(), ensure_ascii=True, separators=(",", ":")))
            else:
                lines.append(json.dumps(r.model_dump(), ensure_ascii=True, separators=(",", ":")))
        self.tools_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _get_previous_status(self, tool_id: str, fallback: str) -> str:
        record = self.get_tool(tool_id)
        return record.status if record else fallback
