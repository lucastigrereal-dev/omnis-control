"""execute_node — executes the current step of a mission."""
from __future__ import annotations

from ..mission_state import MissionGraphState, should_retry


def execute_node(state: MissionGraphState) -> dict:
    """Execute current step. Returns partial update.

    Before executing, consults AuroraGuardrail to check whether the action
    identified by state["action"] is permitted. If blocked, returns
    status=failed with an error message. Aurora errors degrade gracefully —
    the pipeline continues without Aurora if the guardrail is unavailable.

    If an error was set on retry: increment the attempt counter for 'execute'
    and clear the error before continuing.
    """
    action = state.get("action", "execute_step")

    # --- AuroraGuardrail check (graceful degradation) ---
    try:
        from src.aurora.guardrail import AuroraGuardrail  # noqa: PLC0415

        result = AuroraGuardrail().check(action)
        if result.is_blocked:
            return {
                "error": f"Guardrail bloqueou '{action}': {result.reason}",
                "status": "failed",
            }
    except Exception:
        pass  # graceful degradation: guardrail indisponível, continua

    if state.get("error"):
        from src.mission_graph.mission_state import record_attempt  # noqa: PLC0415

        attempt_patch = record_attempt(state, "execute")
        return {**attempt_patch, "error": None, "current_step": state["current_step"] + 1}
    return {"current_step": state["current_step"] + 1}


def route_after_execute(state: MissionGraphState) -> str:
    """Conditional edge: retry | checkpoint | fail

    If status is already 'failed' (e.g. guardrail blocked), go directly to fail
    without retry to avoid infinite loops.
    """
    node = "execute"
    if state.get("status") == "failed":
        return "fail"
    if state.get("error"):
        if should_retry(state, node):
            return "retry"
        return "fail"
    if state["current_step"] >= 3:  # stub: 3 steps = done
        return "checkpoint"
    return "checkpoint"
