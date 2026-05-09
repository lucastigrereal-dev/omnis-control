"""Tests for WorkOrder builder."""
from __future__ import annotations

import pytest

from src.execution_graph.models import (
    ExecutionGraph,
    StepNode,
    StepRun,
    StepStatus,
    _make_graph_id,
    _make_step_id,
    _make_run_id,
)
from src.work_order.builder import (
    build_work_orders_from_graph,
    build_work_orders_from_step_run,
    _infer_contracts,
)
from src.work_order.errors import WorkOrderBuildError
from src.work_order.models import OutputType, WorkOrderStatus


def make_test_graph(with_order: bool = True) -> ExecutionGraph:
    nodes = [
        StepNode(
            step_id="step_01",
            task_id="task_a",
            role_id="copywriter",
            title="Criar legenda",
            description="Escrever legenda para o post",
            expected_output="Legenda em markdown com hashtags",
            depends_on=[],
            assigned_role="copywriter",
        ),
        StepNode(
            step_id="step_02",
            task_id="task_b",
            role_id="designer",
            title="Criar imagem",
            description="Design do post",
            expected_output="Imagem 1080x1080",
            depends_on=["step_01"],
            assigned_role="designer",
        ),
        StepNode(
            step_id="step_03",
            task_id="task_c",
            role_id="seo_specialist",
            title="Otimizar SEO",
            description="Keywords e metadata",
            expected_output="JSON com keywords e metadata",
            depends_on=["step_01"],
            assigned_role="seo_specialist",
        ),
    ]
    order = ["step_01", "step_02", "step_03"] if with_order else []

    return ExecutionGraph(
        graph_id=_make_graph_id(),
        request="criar post de viagem em natal",
        squad_id="squad_abc",
        task_plan_id="tp_xyz",
        nodes=nodes,
        edges=[("step_01", "step_02"), ("step_01", "step_03")],
        topological_order=order,
        created_at="2026-05-09T00:00:00Z",
    )


def make_test_step_run(graph: ExecutionGraph) -> StepRun:
    return StepRun(
        graph_run_id=_make_run_id(),
        graph_id=graph.graph_id,
        request=graph.request,
        status="done",
        step_states={"step_01": "done", "step_02": "done", "step_03": "done"},
        logs=[],
        started_at="2026-05-09T00:00:00Z",
        finished_at="2026-05-09T00:05:00Z",
        graph_snapshot=graph.to_dict(),
    )


class TestInferContracts:
    def test_copywriter_gets_markdown_and_json(self):
        contracts = _infer_contracts("copywriter", "Legenda")
        types = {c.output_type for c in contracts}
        assert OutputType.MARKDOWN in types
        assert OutputType.JSON in types

    def test_unknown_role_gets_unknown_type(self):
        contracts = _infer_contracts("nonexistent_role", "something")
        assert len(contracts) == 1
        assert contracts[0].output_type == OutputType.UNKNOWN

    def test_contract_descriptions_include_role(self):
        contracts = _infer_contracts("designer", "Imagem")
        for c in contracts:
            assert "designer" in c.description.lower()


class TestBuildWorkOrdersFromGraph:
    def test_creates_one_work_order_per_node(self):
        graph = make_test_graph()
        step_run = make_test_step_run(graph)
        orders = build_work_orders_from_graph(graph, step_run)
        assert len(orders) == 3

    def test_work_orders_use_topological_order(self):
        graph = make_test_graph(with_order=True)
        step_run = make_test_step_run(graph)
        orders = build_work_orders_from_graph(graph, step_run)
        assert orders[0].graph_step_id == "step_01"
        assert orders[1].graph_step_id == "step_02"
        assert orders[2].graph_step_id == "step_03"

    def test_work_orders_have_unique_ids(self):
        graph = make_test_graph()
        step_run = make_test_step_run(graph)
        orders = build_work_orders_from_graph(graph, step_run)
        ids = {wo.work_order_id for wo in orders}
        assert len(ids) == 3

    def test_work_orders_start_as_draft(self):
        graph = make_test_graph()
        step_run = make_test_step_run(graph)
        orders = build_work_orders_from_graph(graph, step_run)
        for wo in orders:
            assert wo.status == WorkOrderStatus.DRAFT

    def test_work_orders_have_graph_run_id(self):
        graph = make_test_graph()
        step_run = make_test_step_run(graph)
        orders = build_work_orders_from_graph(graph, step_run)
        for wo in orders:
            assert wo.graph_run_id == step_run.graph_run_id

    def test_work_orders_have_contracts(self):
        graph = make_test_graph()
        step_run = make_test_step_run(graph)
        orders = build_work_orders_from_graph(graph, step_run)
        copywriter_wo = orders[0]
        assert len(copywriter_wo.contracts) >= 1
        assert copywriter_wo.role == "copywriter"

    def test_work_orders_have_metadata(self):
        graph = make_test_graph()
        step_run = make_test_step_run(graph)
        orders = build_work_orders_from_graph(graph, step_run)
        for wo in orders:
            assert "task_id" in wo.metadata
            assert "expected_output" in wo.metadata
            assert "graph_id" in wo.metadata

    def test_missing_step_in_order_raises(self):
        graph = make_test_graph(with_order=True)
        step_run = make_test_step_run(graph)
        graph.topological_order.append("step_nonexistent")
        with pytest.raises(WorkOrderBuildError, match="not in nodes"):
            build_work_orders_from_graph(graph, step_run)

    def test_no_topological_order_falls_back_to_node_list(self):
        graph = make_test_graph(with_order=False)
        step_run = make_test_step_run(graph)
        orders = build_work_orders_from_graph(graph, step_run)
        assert len(orders) == 3


class TestBuildWorkOrdersFromStepRun:
    def test_rebuilds_from_snapshot(self):
        graph = make_test_graph()
        step_run = make_test_step_run(graph)
        orders = build_work_orders_from_step_run(step_run)
        assert len(orders) == 3

    def test_no_snapshot_raises(self):
        graph = make_test_graph()
        step_run = StepRun(
            graph_run_id=_make_run_id(),
            graph_id=graph.graph_id,
            request="test",
            status="done",
            step_states={},
            logs=[],
            started_at="",
            finished_at="",
            graph_snapshot=None,
        )
        with pytest.raises(WorkOrderBuildError, match="no graph_snapshot"):
            build_work_orders_from_step_run(step_run)
