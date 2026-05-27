from __future__ import annotations
from typing import TypedDict, Annotated
import operator


class MissionGraphState(TypedDict):
    mission_id: str
    status: str  # MissionStatus value
    current_step: int
    attempts_by_node: dict[str, int]
    max_retries: int
    events: Annotated[list[dict], operator.add]  # append-only via LangGraph channel
    artifacts: list[dict]
    error: str | None
    run_checkpoint_id: str | None  # renamed: 'checkpoint_id' is reserved by LangGraph


def initial_state(mission_id: str, max_retries: int = 3) -> MissionGraphState:
    """Create the initial state for a mission graph run."""
    return MissionGraphState(
        mission_id=mission_id,
        status="draft",
        current_step=0,
        attempts_by_node={},
        max_retries=max_retries,
        events=[],
        artifacts=[],
        error=None,
        run_checkpoint_id=None,
    )


def should_retry(state: MissionGraphState, node: str) -> bool:
    """Return True if the node has not exhausted its retry budget."""
    attempts = state["attempts_by_node"].get(node, 0)
    return attempts < state["max_retries"]


def record_attempt(state: MissionGraphState, node: str) -> dict:
    """Return a partial state dict that increments the attempt counter for node."""
    current = state["attempts_by_node"].get(node, 0)
    updated = dict(state["attempts_by_node"])
    updated[node] = current + 1
    return {"attempts_by_node": updated}
