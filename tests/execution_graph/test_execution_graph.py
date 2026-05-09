"""Tests for Execution Graph Lite — P8.0."""
from __future__ import annotations

import pytest

from src.execution_graph.models import (
    ExecutionGraph,
    StepNode,
    StepStatus,
    _make_graph_id,
    _make_step_id,
)
from src.execution_graph.builder import build_graph, GraphBuildError
from src.execution_graph.validator import validate_graph
from src.execution_graph.errors import (
    ExecutionGraphError,
    InvalidGraphError,
    CycleDetectedError,
)
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad


# ── Unit: StepStatus ──────────────────────────────────────────────

def test_step_status_values():
    assert StepStatus.PENDING.value == "pending"
    assert StepStatus.READY.value == "ready"
    assert StepStatus.RUNNING.value == "running"
    assert StepStatus.DONE.value == "done"
    assert StepStatus.FAILED.value == "failed"
    assert StepStatus.SKIPPED.value == "skipped"


def test_step_node_creation():
    node = StepNode(
        step_id="step_abc123",
        task_id="task_xyz",
        role_id="copywriter",
        title="Write copy",
        description="Write engaging captions",
        expected_output="caption",
        depends_on=["step_parent"],
    )
    assert node.status == StepStatus.PENDING
    assert "step_parent" in node.depends_on
    d = node.to_dict()
    assert d["step_id"] == "step_abc123"
    assert d["status"] == "pending"


def test_step_node_serialization():
    node = StepNode(
        step_id="s1",
        task_id="t1",
        role_id="qa_auditor",
        title="QA",
        description="Review",
        expected_output="report",
        depends_on=["s0"],
        status=StepStatus.RUNNING,
    )
    d = node.to_dict()
    assert d["status"] == "running"
    assert d["role_id"] == "qa_auditor"


def test_execution_graph_properties():
    nodes = [
        StepNode("s1", "t1", "r1", "T1", "D1", "out1", []),
        StepNode("s2", "t2", "r2", "T2", "D2", "out2", ["s1"]),
    ]
    g = ExecutionGraph(
        graph_id="g1",
        request="test",
        squad_id="sq1",
        task_plan_id="tp1",
        nodes=nodes,
        edges=[("s1", "s2")],
        topological_order=["s1", "s2"],
        created_at="2026-01-01T00:00:00",
    )
    assert g.node_map["s1"].title == "T1"
    assert g.node_map["s2"].depends_on == ["s1"]
    d = g.to_dict()
    assert d["nodes"][0]["step_id"] == "s1"
    assert d["edges"] == [["s1", "s2"]]


def test_id_generation():
    gid = _make_graph_id()
    sid = _make_step_id()
    assert gid.startswith("graph_")
    assert sid.startswith("step_")
    assert len(gid) > 6
    assert len(sid) > 5


# ── Integration: Builder from real plans ──────────────────────────

def test_build_graph_marketing_request():
    squad = compose_squad("criar campanha de marketing para Resort Villa do Sol")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    assert graph.graph_id.startswith("graph_")
    assert len(graph.nodes) >= 3  # marketing_strategist, copywriter, visual_director, qa_auditor
    assert graph.squad_id == squad.squad_id
    assert graph.topological_order
    assert isinstance(graph.edges, list)


def test_build_graph_app_request():
    squad = compose_squad("criar app de CRM para hotels")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    assert graph.graph_id.startswith("graph_")
    assert any(n.role_id == "app_architect" for n in graph.nodes)
    assert graph.request == task_plan.request


def test_build_graph_empty_tasks_raises():
    from src.task_decomposer.models import TaskPlan
    squad = compose_squad("post aleatorio generico")

    empty_plan = TaskPlan(
        task_plan_id="tp_empty",
        squad_id=squad.squad_id,
        request=squad.request,
        tasks=[],
        dependency_graph={},
        risk_level="low",
        approval_required=False,
        created_at="2026-01-01T00:00:00",
    )
    with pytest.raises(GraphBuildError, match="no tasks"):
        build_graph(squad, empty_plan)


# ── Validator tests ───────────────────────────────────────────────

def test_validate_valid_graph():
    squad = compose_squad("fazer um post de viagem em natal")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    issues = validate_graph(graph)
    assert issues == [], f"Expected no issues but got: {issues}"


def test_validate_graph_no_nodes():
    g = ExecutionGraph(
        graph_id="g_empty", request="req", squad_id="sq1", task_plan_id="tp1",
        nodes=[], edges=[], topological_order=[], created_at="2026-01-01T00:00:00",
    )
    issues = validate_graph(g)
    assert "no nodes" in issues[0]


def test_validate_duplicate_step_ids():
    n1 = StepNode("s1", "t1", "r1", "A", "D", "out", [])
    n2 = StepNode("s1", "t2", "r1", "B", "D", "out", [])
    g = ExecutionGraph(
        graph_id="gd", request="req", squad_id="sq1", task_plan_id="tp1",
        nodes=[n1, n2], edges=[], topological_order=["s1", "s1"], created_at="2026-01-01T00:00:00",
    )
    issues = validate_graph(g)
    assert any("Duplicate" in i for i in issues)


def test_validate_topological_order_mismatch():
    nodes = [
        StepNode("s1", "t1", "r1", "T1", "D", "out", []),
        StepNode("s2", "t2", "r1", "T2", "D", "out", ["s1"]),
    ]
    g = ExecutionGraph(
        graph_id="g_bad", request="req", squad_id="sq1", task_plan_id="tp1",
        nodes=nodes, edges=[("s1", "s2")], topological_order=["s2", "s1"],
        created_at="2026-01-01T00:00:00",
    )
    issues = validate_graph(g)
    assert any("violates" in i.lower() for i in issues)


# ── CLI smoke ─────────────────────────────────────────────────────

def test_cli_graph_build_runs():
    import subprocess, sys, os
    result = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "build", "criar post de viagem"],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    assert result.returncode == 0
    assert "Execution Graph" in result.stdout


def test_cli_graph_build_json():
    import subprocess, sys, os
    result = subprocess.run(
        [sys.executable, "jarvis.py", "graph", "build", "criar post de viagem", "--json"],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
    assert result.returncode == 0
    data = __import__("json").loads(result.stdout)
    assert "graph_id" in data
    assert "nodes" in data
    assert "edges" in data


# ── Edge cases ────────────────────────────────────────────────────

def test_step_node_all_statuses_to_dict():
    for status in StepStatus:
        node = StepNode(
            step_id="sx", task_id="tx", role_id="rx",
            title="T", description="D", expected_output="O",
            depends_on=[], status=status,
        )
        assert node.to_dict()["status"] == status.value


def test_graph_with_single_node_no_deps():
    n = StepNode("s0", "t0", "r0", "Only", "Only node", "out", [])
    g = ExecutionGraph(
        graph_id="g_solo", request="req", squad_id="sq1",
        task_plan_id="tp1", nodes=[n], edges=[],
        topological_order=["s0"], created_at="2026",
    )
    issues = validate_graph(g)
    assert issues == []
