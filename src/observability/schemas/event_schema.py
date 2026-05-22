"""Unified event envelope — the canonical OMNIS event schema.

All events flowing through the OMNIS nervous system use this envelope.
Append-only, immutable, idempotent, replay-safe.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """Canonical event types for the OMNIS observability layer."""

    # Mission lifecycle
    MISSION_STARTED = "mission_started"
    MISSION_FAILED = "mission_failed"
    MISSION_COMPLETED = "mission_completed"
    MISSION_CANCELLED = "mission_cancelled"
    MISSION_PAUSED = "mission_paused"
    MISSION_RESUMED = "mission_resumed"

    # Task / wave execution
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_SKIPPED = "task_skipped"
    WAVE_STARTED = "wave_started"
    WAVE_COMPLETED = "wave_completed"
    WAVE_FAILED = "wave_failed"

    # Recovery
    RETRY_TRIGGERED = "retry_triggered"
    RETRY_EXHAUSTED = "retry_exhausted"
    ROLLBACK_TRIGGERED = "rollback_triggered"
    ROLLBACK_COMPLETED = "rollback_completed"
    CIRCUIT_BREAKER_OPENED = "circuit_breaker_opened"
    CIRCUIT_BREAKER_CLOSED = "circuit_breaker_closed"

    # Provider observability
    PROVIDER_CALLED = "provider_called"
    PROVIDER_FAILED = "provider_failed"
    PROVIDER_RECOVERED = "provider_recovered"

    # Memory / knowledge
    MEMORY_RETRIEVAL = "memory_retrieval"
    MEMORY_STORED = "memory_stored"
    MEMORY_EVICTED = "memory_evicted"

    # Resource tracking
    TOKEN_USAGE = "token_usage"
    COST_INCURRED = "cost_incurred"
    LATENCY_RECORDED = "latency_recorded"

    # Quality / safety
    HALLUCINATION_DETECTED = "hallucination_detected"
    HALLUCINATION_RESOLVED = "hallucination_resolved"
    GUARDRAIL_TRIGGERED = "guardrail_triggered"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RESOLVED = "approval_resolved"

    # System
    HEALTH_CHECK = "health_check"
    ANOMALY_DETECTED = "anomaly_detected"
    CHECKPOINT_CREATED = "checkpoint_created"
    EVIDENCE_RECORDED = "evidence_recorded"


ALL_EVENT_TYPES = sorted([e.value for e in EventType])


class EventEnvelope(BaseModel):
    """Canonical event envelope — the only event format on the OMNIS bus.

    All fields are immutable after creation. The envelope wraps payload-specific
    data and provides tracing, idempotency, and replay guarantees.

    Replay safety:
        - sequence number enables total order
        - idempotency_key prevents duplicate processing
        - timestamp is wall-clock (not processed-at) for determinism
    """

    model_config = {"frozen": True}

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = Field(..., description="Component that emitted this event")
    sequence: int = Field(..., ge=0, description="Monotonic sequence number")

    # Tracing
    trace_id: str | None = Field(default=None, description="Distributed trace ID")
    span_id: str | None = Field(default=None, description="Span within trace")
    parent_span_id: str | None = Field(default=None)

    # Correlation
    mission_id: str | None = Field(default=None)
    task_id: str | None = Field(default=None)
    wave_id: str | None = Field(default=None)

    # Payload
    payload: dict[str, Any] = Field(default_factory=dict)
    payload_schema_version: str = Field(default="1.0.0")

    # Idempotency
    idempotency_key: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique key to detect duplicates",
    )

    # Resource tracking
    delta_tokens: int | None = Field(default=None, ge=0)
    delta_cost_usd: float | None = Field(default=None, ge=0.0)
    latency_ms: float | None = Field(default=None, ge=0.0)

    # Metadata
    tags: dict[str, str] = Field(default_factory=dict)
    severity: Literal["debug", "info", "warning", "error", "critical"] = "info"

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, v: str) -> str:
        UUID(v)  # raises if invalid
        return v

    def to_jsonl(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_jsonl(cls, line: str) -> "EventEnvelope":
        return cls.model_validate_json(line)
