"""Characterization tests for execution graph dry-run runner helpers."""
from __future__ import annotations

import pytest

from src.execution_graph.errors import ExecutionGraphError
from src.execution_graph.models import ExecutionGraph, StepNode
from src.execution_graph.runner import _resolve_dry_step, _validate_graph_dry


def _node(step_id: str = "s1") -> StepNode:
    return StepNode(
        step_id=step_id,
        task_id=f"task_{step_id}",
        role_id="role_a",
        title=f"Step {step_id}",
        description="Test step",
        expected_output="output.md",
        depends_on=[],
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


def test_validate_graph_dry_rejects_empty_graph():
    with pytest.raises(ExecutionGraphError, match="empty graph"):
        _validate_graph_dry(_graph([]))


def test_resolve_dry_step_returns_node_for_known_step():
    node = _node("s1")
    assert _resolve_dry_step(_graph([node]), "s1") == node


def test_resolve_dry_step_returns_none_for_unknown_step():
    assert _resolve_dry_step(_graph([_node("s1")]), "missing") is None
