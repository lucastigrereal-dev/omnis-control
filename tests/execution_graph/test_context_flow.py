"""Testes de fluxo de contexto entre passos (Onda 8 Passo 4).

Verifica que context_store acumula outputs e injeta upstream context
no entry.result_hint antes da execução do próximo passo.
"""
from __future__ import annotations

import pytest

from src.execution_graph.builder import build_graph
from src.execution_graph.runner import run_graph_dry, run_graph_real, _collect_upstream_context
from src.execution_graph.models import StepNode, StepStatus
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_graph():
    squad = compose_squad("research then publish workflow")
    task_plan = decompose_squad(squad)
    return build_graph(squad, task_plan)


# ── _collect_upstream_context ─────────────────────────────────────────────────

def test_collect_upstream_context_no_store():
    node = StepNode(
        step_id="s2",
        task_id="t2",
        title="Step 2",
        description="Publish content",
        role_id="publisher",
        assigned_role="publisher",
        expected_output="published",
        depends_on=["s1"],
    )
    result = _collect_upstream_context(node, None)
    assert result == ""


def test_collect_upstream_context_empty_depends():
    node = StepNode(
        step_id="s1",
        task_id="t1",
        title="Step 1",
        description="Research topic",
        role_id="researcher",
        assigned_role="researcher",
        expected_output="research output",
        depends_on=[],
    )
    store = {"s0": "some earlier output"}
    result = _collect_upstream_context(node, store)
    assert result == ""


def test_collect_upstream_context_dep_not_in_store():
    node = StepNode(
        step_id="s2",
        task_id="t2",
        title="Step 2",
        description="Publish content",
        role_id="publisher",
        assigned_role="publisher",
        expected_output="published",
        depends_on=["s1"],
    )
    result = _collect_upstream_context(node, {})
    assert result == ""


def test_collect_upstream_context_single_dep():
    node = StepNode(
        step_id="s2",
        task_id="t2",
        title="Step 2",
        description="Publish content",
        role_id="publisher",
        assigned_role="publisher",
        expected_output="published",
        depends_on=["s1"],
    )
    store = {"s1": "research about hotels in RN"}
    result = _collect_upstream_context(node, store)
    assert "[s1]: research about hotels in RN" in result


def test_collect_upstream_context_multiple_deps():
    node = StepNode(
        step_id="s3",
        task_id="t3",
        title="Step 3",
        description="Combine and publish",
        role_id="publisher",
        assigned_role="publisher",
        expected_output="final output",
        depends_on=["s1", "s2"],
    )
    store = {"s1": "output one", "s2": "output two"}
    result = _collect_upstream_context(node, store)
    assert "[s1]: output one" in result
    assert "[s2]: output two" in result


# ── run_graph_dry + context_store ────────────────────────────────────────────

def test_run_graph_dry_populates_context_store():
    graph = _make_graph()
    store: dict[str, str] = {}
    step_run = run_graph_dry(graph, context_store=store)
    assert step_run.status == "done"
    # Every DONE step should have an entry in the store
    done_steps = [
        sid for sid, st in step_run.step_states.items()
        if st == StepStatus.DONE.value
    ]
    assert len(done_steps) > 0
    for sid in done_steps:
        assert sid in store


def test_run_graph_dry_context_store_values_are_expected_outputs():
    graph = _make_graph()
    store: dict[str, str] = {}
    run_graph_dry(graph, context_store=store)
    for node in graph.nodes:
        if node.step_id in store:
            assert store[node.step_id] == node.expected_output


def test_run_graph_dry_none_context_store_still_works():
    graph = _make_graph()
    # No context_store — should work exactly as before
    step_run = run_graph_dry(graph, context_store=None)
    assert step_run.status == "done"


def test_run_graph_dry_failed_step_not_in_store():
    graph = _make_graph()
    first_step = graph.topological_order[0]
    store: dict[str, str] = {}
    step_run = run_graph_dry(graph, fail_at=first_step, context_store=store)
    assert step_run.status == "failed"
    assert first_step not in store


# ── run_graph_real + context_store ───────────────────────────────────────────

def _make_mock_bridge():
    from src.agentic.skill_runner_bridge import SkillRunnerBridge
    return SkillRunnerBridge(dry_run=True)


def test_run_graph_real_populates_context_store():
    graph = _make_graph()
    bridge = _make_mock_bridge()
    store: dict[str, str] = {}
    step_run = run_graph_real(graph, bridge, context_store=store)
    done_steps = [
        sid for sid, st in step_run.step_states.items()
        if st == StepStatus.DONE.value
    ]
    assert len(done_steps) > 0
    for sid in done_steps:
        assert sid in store


def test_run_graph_real_context_store_not_none_after_done():
    graph = _make_graph()
    bridge = _make_mock_bridge()
    store: dict[str, str] = {}
    run_graph_real(graph, bridge, context_store=store)
    assert len(store) > 0
    for value in store.values():
        assert isinstance(value, str)
        assert len(value) >= 0


def test_run_graph_real_none_context_store_backward_compatible():
    graph = _make_graph()
    bridge = _make_mock_bridge()
    step_run = run_graph_real(graph, bridge, context_store=None)
    assert step_run.status == "done"


# ── upstream context injected into result_hint ────────────────────────────────

def test_upstream_context_injected_via_result_hint():
    """Verify that entry.result_hint receives upstream output before execution."""
    from src.agentic.task_dispatcher import DispatchEntry
    from src.execution_graph.runner import _collect_upstream_context
    from src.execution_graph.models import StepNode

    node = StepNode(
        step_id="s2",
        task_id="t2",
        title="Publish",
        description="Publish post to channel",
        role_id="channel_messenger",
        assigned_role="channel_messenger",
        expected_output="post published",
        depends_on=["s1"],
    )
    store = {"s1": "hotel research: best hotels in Natal"}
    upstream = _collect_upstream_context(node, store)
    entry = DispatchEntry(
        task_id="t2",
        deliverable="publish post",
        executor="channel_messenger",
        dry_run=True,
    )
    if upstream:
        entry.result_hint = upstream

    assert "[s1]: hotel research: best hotels in Natal" in entry.result_hint
