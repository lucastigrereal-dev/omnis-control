"""execute_node — executes the current step of a mission."""
from __future__ import annotations

from ..mission_state import MissionGraphState, should_retry


def execute_node(state: MissionGraphState) -> dict:
    """Stub — execute current step. Returns partial update."""
    return {"current_step": state["current_step"] + 1}


def route_after_execute(state: MissionGraphState) -> str:
    """Conditional edge: retry | checkpoint | fail"""
    node = "execute"
    if state.get("error"):
        if should_retry(state, node):
            return "retry"
        return "fail"
    if state["current_step"] >= 3:  # stub: 3 steps = done
        return "checkpoint"
    return "checkpoint"
