"""validate_node — validates mission_id and initial state."""
from __future__ import annotations

from ..mission_state import MissionGraphState


def validate_node(state: MissionGraphState) -> dict:
    """Validate mission_id and initial state.

    Also consults AuroraGuardrail to check whether "run_mission" is permitted.
    If guardrail blocks the action, returns status=failed immediately.
    Aurora errors degrade gracefully — the pipeline continues without Aurora.
    """
    if not state["mission_id"]:
        return {"status": "failed", "error": "mission_id obrigatório"}

    # --- AuroraGuardrail check (consultivo, graceful degradation) ---
    try:
        from src.aurora.guardrail import AuroraGuardrail  # noqa: PLC0415

        guardrail = AuroraGuardrail()
        result = guardrail.check("run_mission")
        if result.is_blocked:
            return {
                "status": "failed",
                "error": f"AuroraGuardrail: run_mission bloqueado — {result.reason}",
            }
    except Exception:
        pass  # graceful degradation: Aurora indisponível, continua

    return {"status": "running", "current_step": 0}


def route_after_validate(state: MissionGraphState) -> str:
    """Conditional edge after validate: proceed to execute or short-circuit to finalize."""
    if state.get("error"):
        return "fail"
    return "execute"
