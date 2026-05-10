"""Tests for P9.4 — Execution Graph -> Work Order Integration."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.execution_graph.models import (
    ExecutionGraph,
    StepNode,
    StepRun,
    StepRunLog,
    StepStatus,
    _make_graph_id,
    _make_step_id,
)
from src.work_order.graph_integration import (
    build_and_persist_work_orders,
    find_work_order_ids_for_run,
    load_work_orders_for_run,
    run_graph_with_work_orders,
    sync_all_work_orders_from_run,
    sync_work_order_status,
)
from src.work_order.models import (
    OutputContract,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    make_work_order_id,
)


def make_graph(**overrides) -> ExecutionGraph:
    step_a = StepNode(
        step_id=_make_step_id(),
        task_id="task_01",
        role_id="copywriter",
        title="Criar legenda",
        description="Escrever legenda do post",
        expected_output="Legenda em markdown",
        depends_on=[],
        assigned_role="copywriter",
    )
    step_b = StepNode(
        step_id=_make_step_id(),
        task_id="task_02",
        role_id="designer",
        title="Criar imagem",
        description="Criar asset visual",
        expected_output="Imagem finalizada",
        depends_on=[step_a.step_id],
        assigned_role="designer",
    )

    kwargs = dict(
        graph_id=_make_graph_id(),
        request="Criar post de viagem",
        squad_id="squad_a",
        task_plan_id="plan_01",
        nodes=[step_a, step_b],
        edges=[(step_a.step_id, step_b.step_id)],
        topological_order=[step_a.step_id, step_b.step_id],
        created_at="2026-05-09T00:00:00Z",
    )
    kwargs.update(overrides)
    return ExecutionGraph(**kwargs)


def make_step_run(graph, **overrides) -> StepRun:
    from src.execution_graph.runner import run_graph_dry
    kwargs = dict(include_snapshot=True)
    kwargs.update(overrides)
    return run_graph_dry(graph, **kwargs)


@pytest.fixture
def tmp_exports():
    d = tempfile.mkdtemp(prefix="p9_int_")
    yield Path(d)
    import shutil
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def tmp_approvals_log():
    d = tempfile.mkdtemp(prefix="p9_int_app_")
    p = Path(d) / "approvals.jsonl"
    yield p
    import shutil
    shutil.rmtree(d, ignore_errors=True)


class TestBuildAndPersistWorkOrders:
    def test_builds_and_persists(self, tmp_exports):
        graph = make_graph()
        step_run = make_step_run(graph)
        wos = build_and_persist_work_orders(graph, step_run, tmp_exports)
        assert len(wos) == 2
        assert wos[0].graph_step_id == graph.nodes[0].step_id

        manifest = tmp_exports / wos[0].work_order_id / "work_order.json"
        assert manifest.exists()

    def test_topological_order_preserved(self, tmp_exports):
        graph = make_graph()
        step_run = make_step_run(graph)
        wos = build_and_persist_work_orders(graph, step_run, tmp_exports)
        assert wos[0].graph_step_id == graph.topological_order[0]
        assert wos[1].graph_step_id == graph.topological_order[1]


class TestSyncWorkOrderStatus:
    def test_running_sets_in_progress_future(self):
        wo = WorkOrder(make_work_order_id(), "step_a", "grun_x", "copywriter", "Criar", status=WorkOrderStatus.DRAFT, contracts=[])
        log = StepRunLog("step_a", "copywriter", StepStatus.RUNNING.value, "started", "")
        result = sync_work_order_status(wo, log)
        assert result.status == WorkOrderStatus.IN_PROGRESS_FUTURE

    def test_done_sets_output_pending(self):
        wo = WorkOrder(make_work_order_id(), "step_a", "grun_x", "copywriter", "Criar", status=WorkOrderStatus.IN_PROGRESS_FUTURE, contracts=[])
        log = StepRunLog("step_a", "copywriter", StepStatus.DONE.value, "done", "")
        result = sync_work_order_status(wo, log)
        assert result.status == WorkOrderStatus.OUTPUT_PENDING

    def test_failed_sets_rejected(self):
        wo = WorkOrder(make_work_order_id(), "step_a", "grun_x", "copywriter", "Criar", status=WorkOrderStatus.IN_PROGRESS_FUTURE, contracts=[])
        log = StepRunLog("step_a", "copywriter", StepStatus.FAILED.value, "failed", "")
        result = sync_work_order_status(wo, log)
        assert result.status == WorkOrderStatus.REJECTED

    def test_skipped_sets_closed(self):
        wo = WorkOrder(make_work_order_id(), "step_a", "grun_x", "copywriter", "Criar", status=WorkOrderStatus.DRAFT, contracts=[])
        log = StepRunLog("step_a", "copywriter", StepStatus.SKIPPED.value, "skipped", "")
        result = sync_work_order_status(wo, log)
        assert result.status == WorkOrderStatus.CLOSED

class TestSyncAllWorkOrdersFromRun:
    def test_syncs_both_work_orders(self, tmp_exports):
        graph = make_graph()
        step_run = make_step_run(graph)
        wos = build_and_persist_work_orders(graph, step_run, tmp_exports)
        wos = sync_all_work_orders_from_run(wos, step_run)
        assert wos[0].status == WorkOrderStatus.OUTPUT_PENDING
        assert wos[1].status == WorkOrderStatus.OUTPUT_PENDING


class TestRunGraphWithWorkOrders:
    def test_runs_and_returns_work_orders(self, tmp_exports):
        graph = make_graph()
        step_run, wos = run_graph_with_work_orders(graph, exports_root=tmp_exports)
        assert step_run.status == "done"
        assert len(wos) == 2
        assert wos[0].status == WorkOrderStatus.OUTPUT_PENDING

    def test_persists_work_orders_to_disk(self, tmp_exports):
        graph = make_graph()
        step_run, wos = run_graph_with_work_orders(graph, exports_root=tmp_exports)
        for wo in wos:
            manifest = tmp_exports / wo.work_order_id / "work_order.json"
            assert manifest.exists()

    def test_fail_at_step_rejects_work_order(self, tmp_exports):
        graph = make_graph()
        step_run, wos = run_graph_with_work_orders(
            graph, exports_root=tmp_exports, fail_at=graph.nodes[0].step_id,
        )
        assert step_run.status == "failed"
        assert wos[0].status == WorkOrderStatus.REJECTED

    def test_approval_blocked_without_squad_approval(self, tmp_exports, tmp_approvals_log):
        graph = make_graph()

        class FakeSquadPlan:
            approval_required = True
            risk_level = "high"

        step_run, wos = run_graph_with_work_orders(
            graph, squad_plan=FakeSquadPlan(),
            exports_root=tmp_exports, approvals_log=tmp_approvals_log,
        )
        assert step_run.status == "blocked_pending_approval"
        assert step_run.approval_id is not None
        assert wos[0].status == WorkOrderStatus.BLOCKED
        assert wos[0].approval_id == step_run.approval_id

    def test_approval_not_required_runs_normally(self, tmp_exports):
        graph = make_graph()

        class FakeSquadPlan:
            approval_required = False
            risk_level = "low"

        step_run, wos = run_graph_with_work_orders(
            graph, squad_plan=FakeSquadPlan(), exports_root=tmp_exports,
        )
        assert step_run.status == "done"

    def test_approved_runs_normally(self, tmp_exports, tmp_approvals_log):
        graph = make_graph()

        from src.approval_center.service import request_approval, approve
        req = request_approval(
            subject="Graph run",
            capability_id=graph.graph_id,
            risk_level="low",
            approvals_log=tmp_approvals_log,
        )
        approve(req.request_id, note="LGTM", approvals_log=tmp_approvals_log)

        class FakeSquadPlan:
            approval_required = True
            risk_level = "low"

        step_run, wos = run_graph_with_work_orders(
            graph, squad_plan=FakeSquadPlan(),
            approval_id=req.request_id,
            exports_root=tmp_exports, approvals_log=tmp_approvals_log,
        )
        assert step_run.status == "done"


class TestFindWorkOrderIdsForRun:
    def test_finds_ids_after_run(self, tmp_exports):
        graph = make_graph()
        step_run, wos = run_graph_with_work_orders(graph, exports_root=tmp_exports)
        ids = find_work_order_ids_for_run(step_run.graph_run_id, tmp_exports)
        assert len(ids) == 2
        assert graph.nodes[0].step_id in ids

    def test_returns_empty_for_unknown_run(self, tmp_exports):
        ids = find_work_order_ids_for_run("nonexistent", tmp_exports)
        assert ids == {}


class TestLoadWorkOrdersForRun:
    def test_loads_after_run(self, tmp_exports):
        graph = make_graph()
        step_run, _ = run_graph_with_work_orders(graph, exports_root=tmp_exports)
        wos = load_work_orders_for_run(step_run.graph_run_id, tmp_exports)
        assert len(wos) == 2
        assert wos[0].graph_run_id == step_run.graph_run_id

    def test_returns_empty_for_unknown_run(self, tmp_exports):
        wos = load_work_orders_for_run("nonexistent", tmp_exports)
        assert wos == []
