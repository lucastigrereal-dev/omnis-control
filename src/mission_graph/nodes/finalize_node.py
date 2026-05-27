"""finalize_node — finalizes a mission run."""
from __future__ import annotations

from ..mission_state import MissionGraphState


def finalize_node(state: MissionGraphState) -> dict:
    """Finalise the mission."""
    if state.get("error"):
        return {"status": "failed"}
    return {"status": "completed"}
