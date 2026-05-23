"""Characterization tests for execution graph real-run runner helpers."""
from __future__ import annotations

import pytest

from src.execution_graph.errors import ExecutionGraphError
from src.execution_graph.models import ExecutionGraph, StepNode
from src.execution_graph.runner import _resolve_real_step, _validate_graph_real


class FakeBridge:
    dry_run = True


def _node() -> StepNode:
    return StepNode(
        step_id="s1",
        task_id="task_custom",
        role_id="role_a",
        title="Create caption",
        description="Test step",
        expected_output="caption.md",
        depends_on=[],
        assigned_role="copywriter",
    )


def _graph(nodes: list[StepNode]) -> ExecutionGraph:
    return ExecutionGraph(
        graph_id="graph_test",
        request="test",
        squad_id="sq_test",
        task_plan_id="tp_test",
        nodes=nodes,
        edges=[],
        topological_order=[node.step_id for node in nodes],
        created_at="2026-05-23T00:00:00Z",
    )


def test_validate_graph_real_rejects_empty_graph():
    with pytest.raises(ExecutionGraphError, match="empty graph"):
        _validate_graph_real(_graph([]))


def test_resolve_real_step_builds_dispatch_entry_from_node():
    entry = _resolve_real_step(_node(), FakeBridge())

    assert entry.task_id == "task_custom"
    assert entry.deliverable == "caption.md"
    assert entry.executor == "copywriter"
    assert entry.status == "dispatched"
    assert entry.dry_run is True
