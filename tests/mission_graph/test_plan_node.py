"""Tests for plan_node — D1-W4."""
from __future__ import annotations

import sys
import types

import pytest

from src.mission_graph.mission_state import initial_state
from src.mission_graph.nodes.plan_node import plan_node


# ---------------------------------------------------------------------------
# Unit tests for plan_node in isolation
# ---------------------------------------------------------------------------

def test_plan_node_retorna_steps():
    """plan_node deve retornar dict com chave 'steps' sendo lista não-vazia."""
    state = initial_state("m_test_001")
    result = plan_node(state)
    assert "steps" in result
    assert isinstance(result["steps"], list)
    assert len(result["steps"]) > 0


def test_plan_node_steps_tem_name():
    """Cada step retornado deve ter a chave 'name'."""
    state = initial_state("m_test_002")
    result = plan_node(state)
    for step in result["steps"]:
        assert "name" in step, f"step sem 'name': {step}"


def test_plan_node_fallback():
    """Mesmo sem task_decomposition, plan_node retorna 3 steps via fallback."""
    # Temporarily hide src.missions.task_decomposition to force fallback
    hidden_key = "src.missions.task_decomposition"
    original = sys.modules.pop(hidden_key, None)

    # Also shadow the module at import level by injecting a broken stub
    broken_stub = types.ModuleType(hidden_key)
    broken_stub.TaskDecomposition = None  # will raise on attribute access
    sys.modules[hidden_key] = broken_stub

    try:
        # Re-import plan_node with the broken stub in place
        state = initial_state("m_fallback")
        result = plan_node(state)
    finally:
        # Restore
        if original is not None:
            sys.modules[hidden_key] = original
        else:
            sys.modules.pop(hidden_key, None)

    assert "steps" in result
    assert len(result["steps"]) == 3
    names = {s["name"] for s in result["steps"]}
    assert "validate_input" in names
    assert "execute_main" in names
    assert "finalize_output" in names


def test_steps_no_state():
    """Após plan_node, state['steps'] deve ter items quando merged."""
    state = initial_state("m_state_check")
    assert state["steps"] == []  # initial_state starts empty
    result = plan_node(state)
    # Simulate LangGraph merge: state is updated with returned dict
    state["steps"] = result["steps"]
    assert len(state["steps"]) > 0


# ---------------------------------------------------------------------------
# Integration test: full graph run with plan node
# ---------------------------------------------------------------------------

def test_grafo_com_plan_completa():
    """run_mission_graph com use_langgraph=True deve finalizar com status 'completed'."""
    from src.mission_graph.runner import run_mission_graph

    final = run_mission_graph("m_plan", use_langgraph=True)
    assert final["status"] == "completed"
