"""checkpoint_node — persists checkpoint state."""
from __future__ import annotations

from ..mission_state import MissionGraphState


def checkpoint_node(state: MissionGraphState) -> dict:
    """Persist checkpoint via CheckpointStore (real JsonlRepository)."""
    from src.mission_graph.checkpoint_store import CheckpointStore
    store = CheckpointStore()
    checkpoint_id = store.save(state)
    return {"run_checkpoint_id": checkpoint_id}
