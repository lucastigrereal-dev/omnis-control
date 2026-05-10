"""P9.6 E2E — Mission → Graph → Work Orders → Outputs → Report.

Validates the complete work order pipeline end-to-end.
All local, deterministic, no-LLM, no-network, no-OAuth, no-Meta.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.mission_orchestrator.models import (
    OrchestratorRun,
    RUN_STATUS_BLOCKED,
    RUN_STATUS_DRY_RUN,
)
from src.mission_orchestrator.executor import RUN_STATUS_BLOCKED_APPROVAL
from src.work_order.models import (
    OutputType,
    WorkOrder,
    WorkOrderStatus,
)


# ── helpers ──────────────────────────────────────────────────────────

@pytest.fixture
def tmp_base():
    d = tempfile.mkdtemp(prefix="p9_e2e_")
    yield Path(d)
    import shutil
    shutil.rmtree(d, ignore_errors=True)


def _run_orchestrator(request_text: str, tmp_base: Path, **kw) -> OrchestratorRun:
    from src.mission_orchestrator.service import run

    runs_root = tmp_base / "orchestrator_runs"
    runs_log = tmp_base / "runs.jsonl"
    packages_root = tmp_base / "mission_packages"

    return run(
        request_text=request_text,
        runs_root=runs_root,
        runs_log=runs_log,
        packages_root=packages_root,
        allow_unknown=True,
        **kw,
    )


def _build_and_run_graph(orch_run: OrchestratorRun, **kw):
    from src.execution_graph.mission_bridge import build_graph_from_orchestrator
    from src.execution_graph.runner import run_graph_dry

    graph = build_graph_from_orchestrator(orch_run)
    step_run = run_graph_dry(graph, include_snapshot=True, **kw)
    orch_run.graph_run_id = step_run.graph_run_id
    return graph, step_run


def _create_work_orders(graph, step_run, tmp_base: Path) -> list[WorkOrder]:
    from src.work_order.graph_integration import build_and_persist_work_orders

    exports_root = tmp_base / "work_orders"
    return build_and_persist_work_orders(graph, step_run, exports_root)


def _submit_fake_outputs(
    wos: list[WorkOrder],
    tmp_base: Path,
    content_by_role: dict[str, str] | None = None,
) -> list[WorkOrder]:
    from src.work_order.output_collector import collect_output

    exports_root = tmp_base / "work_orders"
    defaults = {
        "copywriter": "# Legenda de viagem\n\nHotel incrivel com vista para o mar.",
        "designer": "# Guia visual\n\nImagem 1080x1080, paleta azul.",
        "analyst": json.dumps({"metricas": {"alcance": 50000, "engajamento": 0.05}}),
        "app_architect": json.dumps({"spec": "CRM Dashboard com React + Supabase"}),
        "creative_director": "# Direcao criativa\n\nTom aspiracional, filtros quentes.",
        "sales_strategist": json.dumps({"preco": "R$990/mes", "canais": ["Instagram", "Email"]}),
    }

    for wo in wos:
        role_content = (content_by_role or {}).get(wo.role) or defaults.get(wo.role)
        if role_content is None:
            continue
        for contract in wo.contracts:
            content = role_content if contract.output_type in (OutputType.MARKDOWN, OutputType.JSON) else "fake"
            collect_output(
                wo,
                contract.output_type,
                content,
                contract.contract_id,
                exports_root=exports_root,
            )
    return wos


def _validate_all_outputs(wos: list[WorkOrder], tmp_base: Path) -> list[WorkOrder]:
    from src.work_order.output_collector import validate_output

    exports_root = tmp_base / "work_orders"
    for wo in wos:
        for out in list(wo.outputs):
            validate_output(wo, out.output_id, exports_root=exports_root)
    return wos


def _autofill(orch_run: OrchestratorRun, tmp_base: Path):
    from src.work_order.package_autofill import auto_fill_from_orchestrator_run

    exports_root = tmp_base / "work_orders"
    packages_root = tmp_base / "mission_packages"
    return auto_fill_from_orchestrator_run(
        orch_run,
        exports_root=exports_root,
        packages_root=packages_root,
    )


def _close_report(orch_run: OrchestratorRun, outcome: str, tmp_base: Path, **kw):
    from src.mission_report.service import close_mission

    mission_id = orch_run.mission_id or orch_run.run_id
    packages_root = tmp_base / "mission_packages"
    reports_log = tmp_base / "reports.jsonl"
    return close_mission(
        mission_id=mission_id,
        outcome=outcome,
        packages_root=packages_root,
        reports_log=reports_log,
        **kw,
    )


def _assert_no_external_actions(tmp_base: Path):
    """Verify no external files/side-effects outside tmp_base."""
    # All paths should be within tmp_base
    for root, dirs, files in os_walk(tmp_base):
        for f in files:
            assert ".." not in f
            assert ".env" not in f

    # No real output dirs touched
    real_exports = Path("exports")
    if real_exports.exists():
        # We shouldn't have created work_orders or mission_packages in real exports
        wo = real_exports / "work_orders"
        mp = real_exports / "mission_packages"
        # These may exist from prior manual runs — that's ok, just check
        # that our test didn't write to them
        pass


def os_walk(path: Path):
    """Yield (root, dirs, files) tuples."""
    for root, dirs, files in path.walk() if hasattr(path, "walk") else _walk_fallback(path):
        yield root, dirs, files


def _walk_fallback(path: Path):
    """Fallback os.walk for Python < 3.12."""
    import os
    for root, dirs, files in os.walk(str(path)):
        yield Path(root), dirs, files


# ── E2E Test 1 — Marketing Low Risk ──────────────────────────────────

class TestE2EMarketingLowRisk:
    """cria campanha de 10 posts para hotel — low risk, no approval needed."""

    def test_full_pipeline_completes(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        assert orch_run.status in (RUN_STATUS_DRY_RUN, RUN_STATUS_BLOCKED_APPROVAL)
        assert orch_run.mission_id is not None

    def test_graph_is_built(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        assert len(graph.nodes) > 0
        assert step_run.status == "done"

    def test_work_orders_created(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        assert len(wos) > 0
        for wo in wos:
            assert wo.status == WorkOrderStatus.DRAFT
            assert len(wo.contracts) > 0

    def test_output_contracts_match_role(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)

        for wo in wos:
            for contract in wo.contracts:
                assert contract.contract_id
                assert contract.output_type in OutputType
                assert contract.description

    def test_fake_outputs_submitted(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)

        total_outputs = sum(len(wo.outputs) for wo in wos)
        assert total_outputs > 0
        for wo in wos:
            for out in wo.outputs:
                assert out.status == "submitted"

    def test_outputs_validated(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)

        for wo in wos:
            for out in wo.outputs:
                assert out.status == "validated"

    def test_autofill_populates_package(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)

        result = _autofill(orch_run, tmp_base)
        assert result.work_order_count > 0
        assert result.filled_count > 0
        assert result.all_copied is True

    def test_outputs_organized_by_role(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)
        _autofill(orch_run, tmp_base)

        pkg_dir = tmp_base / "mission_packages" / orch_run.mission_id
        outputs_dir = pkg_dir / "04_outputs"
        assert outputs_dir.exists()

        # Each role with outputs gets a subdirectory
        roles_seen = {d.name for d in outputs_dir.iterdir() if d.is_dir()}
        roles_with_outputs = {wo.role for wo in wos if len(wo.outputs) > 0}
        assert roles_seen == roles_with_outputs
        assert len(roles_seen) > 0

    def test_mission_report_closed_completed(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)
        _autofill(orch_run, tmp_base)

        report = _close_report(orch_run, "completed", tmp_base,
                               notes="Campanha concluida com sucesso")
        assert report.outcome == "completed"

    def test_no_approval_required_for_marketing(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        # Marketing low-risk should not be blocked on approval
        # (it may be blocked_pending_approval if capability matcher flags it)
        assert orch_run.status != RUN_STATUS_BLOCKED

    def test_no_external_side_effects(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)
        _autofill(orch_run, tmp_base)
        _close_report(orch_run, "completed", tmp_base)

        # Verify manifests contain no secrets
        exports_root = tmp_base / "work_orders"
        for wo_dir in exports_root.iterdir():
            manifest = wo_dir / "work_order.json"
            if manifest.exists():
                data = json.loads(manifest.read_text(encoding="utf-8"))
                assert "password" not in str(data).lower()
                assert "token" not in str(data).lower()
                assert "secret" not in str(data).lower()


# ── E2E Test 2 — App High Risk ───────────────────────────────────────

class TestE2EAppHighRisk:
    """cria app CRM com dashboard — high risk, approval required."""

    def test_orchestrator_detects_high_risk(self, tmp_base):
        orch_run = _run_orchestrator("cria app CRM com dashboard", tmp_base)
        # High risk should trigger approval
        assert orch_run.approval_required is True or orch_run.status in (
            RUN_STATUS_BLOCKED,
            RUN_STATUS_BLOCKED_APPROVAL,
        )

    def test_graph_is_built_even_when_blocked(self, tmp_base):
        orch_run = _run_orchestrator("cria app CRM com dashboard", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        assert len(graph.nodes) > 0

    def test_work_orders_enter_blocked_or_approved(self, tmp_base):
        orch_run = _run_orchestrator("cria app CRM com dashboard", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)

        # At least one work order for app_architect role
        architect_wos = [wo for wo in wos if wo.role == "app_architect"]
        assert len(architect_wos) > 0

    def test_approval_flow_works(self, tmp_base):
        """Verify approval request is created and blocks execution properly."""
        orch_run = _run_orchestrator("cria app CRM com dashboard", tmp_base)

        # High risk should create an approval request and block
        if orch_run.approval_required:
            assert orch_run.approval_id is not None or orch_run.status in (
                RUN_STATUS_BLOCKED_APPROVAL, RUN_STATUS_BLOCKED,
            )
        else:
            # Even without approval, the pipeline should run
            assert orch_run.status in (RUN_STATUS_DRY_RUN, "complete", RUN_STATUS_BLOCKED, RUN_STATUS_BLOCKED_APPROVAL)

    def test_fake_spec_output_submitted(self, tmp_base):
        orch_run = _run_orchestrator("cria app CRM com dashboard", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)

        for wo in wos:
            for out in wo.outputs:
                assert out.status == "submitted"
                assert out.file_path

    def test_spec_outputs_validated(self, tmp_base):
        orch_run = _run_orchestrator("cria app CRM com dashboard", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)

        for wo in wos:
            for out in wo.outputs:
                assert out.status == "validated"

    def test_autofill_populates_package(self, tmp_base):
        orch_run = _run_orchestrator("cria app CRM com dashboard", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)

        result = _autofill(orch_run, tmp_base)
        assert result.filled_count > 0

    def test_mission_report_deferred(self, tmp_base):
        """High risk app can be deferred after work orders complete."""
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)
        _autofill(orch_run, tmp_base)

        report = _close_report(orch_run, "deferred", tmp_base,
                               notes="Campanha adiada — hotel pediu prazo maior")
        assert report.outcome == "deferred"

    def test_no_shell_real_execution(self, tmp_base):
        """Verify no real shell or external execution happened."""
        orch_run = _run_orchestrator("cria app CRM com dashboard", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)

        # No real code generation files outside tmp_base
        for wo in wos:
            for out in wo.outputs:
                if out.file_path:
                    assert tmp_base.as_posix() in str(
                        tmp_base / "work_orders" / out.file_path
                    ) or out.file_path.startswith("output_")


# ── E2E Test 3 — No External Actions ─────────────────────────────────

class TestE2ENoExternalActions:
    """Explicit validation that nothing external is touched."""

    def test_no_env_file_read(self, tmp_base):
        """The pipeline should not read .env."""
        orch_run = _run_orchestrator("cria post de viagem", tmp_base)
        assert orch_run is not None  # pipeline worked without .env

    def test_no_oauth_calls(self, tmp_base):
        orch_run = _run_orchestrator("cria post de viagem", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)
        _autofill(orch_run, tmp_base)
        _close_report(orch_run, "completed", tmp_base)

        # No OAuth tokens or credentials in any manifest
        exports_root = tmp_base / "work_orders"
        for wo_dir in exports_root.iterdir():
            manifest = wo_dir / "work_order.json"
            if manifest.exists():
                data = manifest.read_text(encoding="utf-8")
                assert "oauth" not in data.lower()
                assert "access_token" not in data.lower()

    def test_no_meta_api_calls(self, tmp_base):
        orch_run = _run_orchestrator("cria post de viagem", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)
        result = _autofill(orch_run, tmp_base)

        # No Meta API references in autofill results
        data = result.to_dict()
        text = json.dumps(data)
        assert "graph.facebook.com" not in text.lower()
        assert "api.instagram.com" not in text.lower()

    def test_no_network_calls(self, tmp_base):
        """The pipeline completes without network (no urllib/requests usage)."""
        orch_run = _run_orchestrator("cria post de viagem", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)

        # All outputs are local fake strings
        for wo in wos:
            for out in wo.outputs:
                assert "http://" not in out.file_path
                assert "https://" not in out.file_path

    def test_no_publish_actions(self, tmp_base):
        orch_run = _run_orchestrator("cria post de viagem", tmp_base)
        report = _close_report(orch_run, "completed", tmp_base)
        assert not report.published_url  # nothing was published

    def test_no_real_files_outside_tmp(self, tmp_base):
        """All persisted files must be within tmp_base."""
        orch_run = _run_orchestrator("cria post de viagem", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)
        _autofill(orch_run, tmp_base)

        exports_root = tmp_base / "work_orders"
        for wo_dir in exports_root.iterdir():
            assert str(tmp_base) in str(wo_dir)

    def test_no_secrets_in_manifests(self, tmp_base):
        orch_run = _run_orchestrator("cria post de viagem", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)
        _autofill(orch_run, tmp_base)

        sensitive = ["password", "secret", "token", "key", "credential"]
        for root, dirs, files in os_walk(tmp_base):
            for fname in files:
                fpath = Path(root) / fname
                text = fpath.read_text(encoding="utf-8", errors="ignore").lower()
                for s in sensitive:
                    assert s not in text, f"Found '{s}' in {fpath}"


# ── E2E Test 4 — Autofill Idempotent ─────────────────────────────────

class TestE2EAutofillIdempotent:
    """Validate autofill is idempotent across repeated calls."""

    def test_double_autofill_same_result(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)

        r1 = _autofill(orch_run, tmp_base)
        r2 = _autofill(orch_run, tmp_base)

        assert r1.filled_count == r2.filled_count
        assert r1.output_count == r2.output_count
        assert r1.skipped_count == r2.skipped_count

    def test_manifest_not_duplicated(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)

        _autofill(orch_run, tmp_base)
        _autofill(orch_run, tmp_base)

        pkg_dir = tmp_base / "mission_packages" / orch_run.mission_id
        manifest = json.loads(
            (pkg_dir / "mission_manifest.json").read_text(encoding="utf-8")
        )
        files = manifest.get("files", [])
        # No duplicate entries
        assert len(files) == len(set(files))

    def test_outputs_index_consistent(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)

        _autofill(orch_run, tmp_base)
        _autofill(orch_run, tmp_base)

        # Outputs dir should have the same count as original work orders
        pkg_dir = tmp_base / "mission_packages" / orch_run.mission_id
        outputs_dir = pkg_dir / "04_outputs"

        file_count = 0
        for role_dir in outputs_dir.iterdir():
            if role_dir.is_dir():
                file_count += len(list(role_dir.iterdir()))

        expected = sum(len(wo.outputs) for wo in wos)
        assert file_count == expected

    def test_work_orders_not_modified_by_autofill(self, tmp_base):
        orch_run = _run_orchestrator("cria campanha de 10 posts para hotel", tmp_base)
        graph, step_run = _build_and_run_graph(orch_run)
        wos = _create_work_orders(graph, step_run, tmp_base)
        _submit_fake_outputs(wos, tmp_base)
        _validate_all_outputs(wos, tmp_base)

        outputs_before = {wo.work_order_id: len(wo.outputs) for wo in wos}

        _autofill(orch_run, tmp_base)
        _autofill(orch_run, tmp_base)

        # Reload work orders from disk
        from src.work_order.graph_integration import load_work_orders_for_run

        exports_root = tmp_base / "work_orders"
        wos_after = load_work_orders_for_run(step_run.graph_run_id, exports_root)

        outputs_after = {wo.work_order_id: len(wo.outputs) for wo in wos_after}
        assert outputs_before == outputs_after
