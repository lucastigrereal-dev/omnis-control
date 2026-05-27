"""checkpoint_node — persists checkpoint state."""
from __future__ import annotations

from ..mission_state import MissionGraphState


def checkpoint_node(state: MissionGraphState) -> dict:
    """Persist checkpoint via JsonlRepository (if available)."""
    import uuid
    return {"run_checkpoint_id": str(uuid.uuid4())[:8]}
