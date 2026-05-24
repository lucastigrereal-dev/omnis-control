"""Testes do Validator Node (Onda 8 Passo 5).

Verifica que _validate_step_output() bloqueia outputs ruins e que
o runner emite log de 'validator' quando output não passa.
"""
from __future__ import annotations

import pytest

from src.execution_graph.runner import _validate_step_output, run_graph_dry
from src.execution_graph.models import ExecutionGraph, StepNode
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad
from src.execution_graph.builder import build_graph


def _single_node_graph(step_id: str, expected_output: str) -> ExecutionGraph:
    node = StepNode(
        step_id=step_id,
        task_id=f"t_{step_id}",
        title=f"Node {step_id}",
        description="test node",
        role_id="researcher",
        assigned_role="researcher",
        expected_output=expected_output,
        depends_on=[],
    )
    return ExecutionGraph(
        graph_id=f"g_{step_id}",
        squad_id=f"sq_{step_id}",
        task_plan_id=f"tp_{step_id}",
        request="test request",
        nodes=[node],
        edges=[],
        topological_order=[step_id],
        created_at="2026-01-01T00:00:00Z",
    )


# ── _validate_step_output ─────────────────────────────────────────────────────

def test_validate_rejects_empty_string():
    assert _validate_step_output("") is False


def test_validate_rejects_whitespace_only():
    assert _validate_step_output("   ") is False


def test_validate_rejects_too_short():
    assert _validate_step_output("abc") is False


def test_validate_rejects_error_marker():
    assert _validate_step_output("error") is False


def test_validate_rejects_failed_marker():
    assert _validate_step_output("failed") is False


def test_validate_rejects_none_string():
    assert _validate_step_output("none") is False


def test_validate_rejects_null_string():
    assert _validate_step_output("null") is False


def test_validate_accepts_real_output():
    assert _validate_step_output("Research completed: found 10 hotels in Natal") is True


def test_validate_accepts_short_but_long_enough():
    assert _validate_step_output("done!") is True  # exactly 5 chars after strip


def test_validate_case_insensitive_rejection():
    assert _validate_step_output("ERROR") is False
    assert _validate_step_output("FAILED") is False
    assert _validate_step_output("None") is False


# ── validator log emitted when output is empty ────────────────────────────────

def test_validator_log_emitted_for_empty_expected_output():
    """If a step has empty expected_output, validator should emit a log event."""
    graph = _single_node_graph("s_val_test", "ok")  # len 2 < 5 → triggers validator
    store: dict[str, str] = {}
    step_run = run_graph_dry(graph, context_store=store)

    assert step_run.status == "done"
    assert "s_val_test" not in store
    validator_logs = [log for log in step_run.logs if log.role_id == "validator"]
    assert len(validator_logs) == 1
    assert "not propagated" in validator_logs[0].message


def test_validator_does_not_block_step_completion():
    """Validator is a soft check — step is still DONE even if output is bad."""
    graph = _single_node_graph("s_soft", "hi")  # too short
    step_run = run_graph_dry(graph, context_store={})
    assert step_run.step_states["s_soft"] == "done"


def test_validator_passes_good_output():
    """Good output goes into context_store, no validator log."""
    graph = _single_node_graph("s_good", "Research complete: 15 hotels analyzed in Natal RN")
    store: dict[str, str] = {}
    step_run = run_graph_dry(graph, context_store=store)
    assert "s_good" in store
    validator_logs = [log for log in step_run.logs if log.role_id == "validator"]
    assert len(validator_logs) == 0


def test_validator_with_real_graph_no_validator_logs():
    """Real graphs have meaningful expected_output — no validator logs expected."""
    squad = compose_squad("criar carrossel para turismo em Natal")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)

    store: dict[str, str] = {}
    step_run = run_graph_dry(graph, context_store=store)

    validator_logs = [log for log in step_run.logs if log.role_id == "validator"]
    # All expected_outputs in a real graph should pass validation
    assert len(validator_logs) == 0
    # And store should have all done steps
    done_steps = [sid for sid, st in step_run.step_states.items() if st == "done"]
    assert set(done_steps) == set(store.keys())
