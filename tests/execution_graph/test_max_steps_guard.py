"""Testes do max_steps guard — teto anti-caos (Onda 8 Passo 6)."""
from __future__ import annotations

import pytest

from src.execution_graph.runner import run_graph_dry, run_graph_real, _MAX_STEPS_DEFAULT
from src.execution_graph.models import ExecutionGraph, StepNode, StepStatus
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad
from src.execution_graph.builder import build_graph


def _make_graph_n_steps(n: int) -> ExecutionGraph:
    """Build a linear graph with n sequential steps."""
    nodes = [
        StepNode(
            step_id=f"s{i}",
            task_id=f"t{i}",
            title=f"Step {i}",
            description=f"step number {i}",
            role_id="researcher",
            assigned_role="researcher",
            expected_output=f"output of step {i} with enough length",
            depends_on=[f"s{i - 1}"] if i > 0 else [],
        )
        for i in range(n)
    ]
    edges = [(f"s{i}", f"s{i + 1}") for i in range(n - 1)]
    return ExecutionGraph(
        graph_id=f"g_{n}steps",
        squad_id=f"sq_{n}steps",
        task_plan_id=f"tp_{n}steps",
        request=f"{n}-step graph",
        nodes=nodes,
        edges=edges,
        topological_order=[f"s{i}" for i in range(n)],
        created_at="2026-01-01T00:00:00Z",
    )


# ── constant ──────────────────────────────────────────────────────────────────

def test_max_steps_default_is_50():
    assert _MAX_STEPS_DEFAULT == 50


# ── run_graph_dry max_steps ───────────────────────────────────────────────────

def test_dry_default_max_steps_does_not_fire_on_normal_graph():
    squad = compose_squad("criar carrossel")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    assert len(graph.nodes) < _MAX_STEPS_DEFAULT
    step_run = run_graph_dry(graph)
    guard_logs = [log for log in step_run.logs if log.role_id == "guard"]
    assert len(guard_logs) == 0
    assert step_run.status == "done"


def test_dry_max_steps_1_blocks_second_step():
    graph = _make_graph_n_steps(3)
    step_run = run_graph_dry(graph, max_steps=1)
    # Only s0 should run; s1, s2 should be skipped by guard
    assert step_run.step_states.get("s0") == StepStatus.DONE.value
    assert step_run.step_states.get("s1") == StepStatus.SKIPPED.value
    assert step_run.step_states.get("s2") == StepStatus.SKIPPED.value
    guard_logs = [log for log in step_run.logs if log.role_id == "guard"]
    assert len(guard_logs) == 2  # s1 and s2 blocked


def test_dry_max_steps_0_blocks_all():
    graph = _make_graph_n_steps(3)
    step_run = run_graph_dry(graph, max_steps=0)
    for step_id in ["s0", "s1", "s2"]:
        assert step_run.step_states.get(step_id) == StepStatus.SKIPPED.value
    guard_logs = [log for log in step_run.logs if log.role_id == "guard"]
    assert len(guard_logs) == 3


def test_dry_max_steps_equals_graph_length_allows_all():
    graph = _make_graph_n_steps(3)
    step_run = run_graph_dry(graph, max_steps=3)
    for step_id in ["s0", "s1", "s2"]:
        assert step_run.step_states.get(step_id) == StepStatus.DONE.value
    guard_logs = [log for log in step_run.logs if log.role_id == "guard"]
    assert len(guard_logs) == 0


def test_dry_guard_log_message_contains_limit():
    graph = _make_graph_n_steps(2)
    step_run = run_graph_dry(graph, max_steps=1)
    guard_logs = [log for log in step_run.logs if log.role_id == "guard"]
    assert len(guard_logs) == 1
    assert "limit of 1" in guard_logs[0].message


# ── run_graph_real max_steps ──────────────────────────────────────────────────

def _make_mock_bridge():
    from src.agentic.skill_runner_bridge import SkillRunnerBridge
    return SkillRunnerBridge(dry_run=True)


def test_real_default_max_steps_does_not_fire_on_normal_graph():
    squad = compose_squad("criar carrossel")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    bridge = _make_mock_bridge()
    step_run = run_graph_real(graph, bridge)
    guard_logs = [log for log in step_run.logs if log.role_id == "guard"]
    assert len(guard_logs) == 0


def test_real_max_steps_1_blocks_second_step():
    graph = _make_graph_n_steps(3)
    bridge = _make_mock_bridge()
    step_run = run_graph_real(graph, bridge, max_steps=1)
    assert step_run.step_states.get("s0") == StepStatus.DONE.value
    assert step_run.step_states.get("s1") == StepStatus.SKIPPED.value
    assert step_run.step_states.get("s2") == StepStatus.SKIPPED.value


def test_real_max_steps_0_blocks_all():
    graph = _make_graph_n_steps(2)
    bridge = _make_mock_bridge()
    step_run = run_graph_real(graph, bridge, max_steps=0)
    guard_logs = [log for log in step_run.logs if log.role_id == "guard"]
    assert len(guard_logs) == 2
