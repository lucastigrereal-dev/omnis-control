"""Event Envelope — 25 event types, append-only, Pydantic v2 frozen."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Literal

from pydantic import BaseModel, ConfigDict, Field

EventType = Literal[
    "mission_created",
    "mission_started",
    "plan_drafted",
    "plan_approved",
    "step_started",
    "step_completed",
    "tool_invoked",
    "tool_returned",
    "skill_invoked",
    "skill_returned",
    "approval_requested",
    "approval_granted",
    "approval_rejected",
    "artifact_produced",
    "artifact_linked",
    "error_logged",
    "retry_attempted",
    "budget_exceeded",
    "token_used",
    "cost_incurred",
    "mission_paused",
    "mission_resumed",
    "mission_completed",
    "mission_failed",
    "mission_cancelled",
]

EVENT_TYPES: tuple[EventType, ...] = (
    "mission_created",
    "mission_started",
    "plan_drafted",
    "plan_approved",
    "step_started",
    "step_completed",
    "tool_invoked",
    "tool_returned",
    "skill_invoked",
    "skill_returned",
    "approval_requested",
    "approval_granted",
    "approval_rejected",
    "artifact_produced",
    "artifact_linked",
    "error_logged",
    "retry_attempted",
    "budget_exceeded",
    "token_used",
    "cost_incurred",
    "mission_paused",
    "mission_resumed",
    "mission_completed",
    "mission_failed",
    "mission_cancelled",
)


class EventEnvelope(BaseModel):
    """Append-only event — a linha no diário de bordo da missão."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mission_id: str
    event_type: EventType
    sequence: int
    actor: str
    actor_detail: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)
    delta_tokens: int = 0
    delta_cost_usd: float = 0.0
    cumulative_tokens: int = 0
    cumulative_cost_usd: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    idempotency_key: str = Field(default_factory=lambda: str(uuid.uuid4()))

    def to_jsonl(self) -> str:
        """Serializa como linha JSONL (compacto)."""
        import json

        return json.dumps(self.model_dump(mode="json"), ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)

    @classmethod
    def from_jsonl(cls, line: str) -> "EventEnvelope":
        """Desserializa de linha JSONL."""
        import json

        data = json.loads(line)
        return cls(**data)
