"""D1 — LangGraph StateGraph skeleton for mission execution.

Import guard: langgraph is imported lazily to allow the module to be loaded
even when the langchain_core.messages.utils stub has not been injected yet.
The build_mission_graph() and compile_mission_graph() functions trigger the
real import at call-time; tests must inject the sys.modules stub before
calling these functions (see tests/mission_graph/conftest.py).
"""
from __future__ import annotations

from .mission_state import MissionGraphState


def _validate_node(state: MissionGraphState) -> dict:
    """Validate mission_id and initial state."""
    if not state["mission_id"]:
        return {"status": "failed", "error": "mission_id obrigatório"}
    return {"status": "running", "current_step": 0}


def _execute_node(state: MissionGraphState) -> dict:
    """Stub — execute current step. Returns partial update."""
    return {"current_step": state["current_step"] + 1}


def _checkpoint_node(state: MissionGraphState) -> dict:
    """Persist checkpoint via JsonlRepository (if available)."""
    import uuid
    return {"run_checkpoint_id": str(uuid.uuid4())[:8]}


def _finalize_node(state: MissionGraphState) -> dict:
    """Finalise the mission."""
    if state.get("error"):
        return {"status": "failed"}
    return {"status": "completed"}


def _route_after_validate(state: MissionGraphState) -> str:
    """Conditional edge after validate: proceed to execute or short-circuit to finalize."""
    if state.get("error"):
        return "fail"
    return "execute"


def _route_after_execute(state: MissionGraphState) -> str:
    """Conditional edge: retry | checkpoint | fail"""
    node = "execute"
    if state.get("error"):
        from .mission_state import should_retry
        if should_retry(state, node):
            return "retry"
        return "fail"
    if state["current_step"] >= 3:  # stub: 3 steps = done
        return "checkpoint"
    return "checkpoint"


def build_mission_graph():
    """Build and return a StateGraph for mission execution.

    Imports langgraph at call-time so that the sys.modules stub for
    langchain_core.messages.utils can be injected beforehand by tests.
    """
    from langgraph.graph import StateGraph, END  # noqa: PLC0415

    g = StateGraph(MissionGraphState)
    g.add_node("validate", _validate_node)
    g.add_node("execute", _execute_node)
    g.add_node("checkpoint", _checkpoint_node)
    g.add_node("finalize", _finalize_node)

    g.set_entry_point("validate")
    g.add_conditional_edges("validate", _route_after_validate, {
        "execute": "execute",
        "fail": "finalize",
    })
    g.add_conditional_edges("execute", _route_after_execute, {
        "retry": "execute",
        "checkpoint": "checkpoint",
        "fail": "finalize",
    })
    g.add_edge("checkpoint", "finalize")
    g.add_edge("finalize", END)

    return g


def compile_mission_graph():
    """Build and compile the mission graph."""
    return build_mission_graph().compile()
