"""validate_node — validates mission_id and initial state."""
from __future__ import annotations

from ..mission_state import MissionGraphState


def validate_node(state: MissionGraphState) -> dict:
    """Validate mission_id and initial state."""
    if not state["mission_id"]:
        return {"status": "failed", "error": "mission_id obrigatório"}
    return {"status": "running", "current_step": 0}


def route_after_validate(state: MissionGraphState) -> str:
    """Conditional edge after validate: proceed to execute or short-circuit to finalize."""
    if state.get("error"):
        return "fail"
    return "execute"
