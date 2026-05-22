"""Telemetry Events — consolidated telemetry event types and contracts.

Defines the 6 standard telemetry events that flow through the OMNIS Bus.
All publishers must use these type strings for consistency.
"""

from enum import Enum


class TelemetryEvent(str, Enum):
    """Standard telemetry event types for the OMNIS Bus.

    These 6 events form the core telemetry backbone. All systems
    (OMNIS, AKASHA, KRATOS) publish these standardized types.
    """

    RUNTIME_HEARTBEAT = "runtime.heartbeat"
    """System heartbeat — published by every live service every 30s."""

    MISSION_CREATED = "mission.created"
    """A new mission was created in the system."""

    MISSION_COMPLETED = "mission.completed"
    """A mission completed execution (success or failure)."""

    MEMORY_INGESTED = "memory.ingested"
    """New content was ingested into Akasha memory."""

    COST_RECORDED = "cost.recorded"
    """A cost record was written (LLM usage, provider billing, etc.)."""

    RISK_DETECTED = "risk.detected"
    """A risk was detected by the control tower or operational truth verifier."""


# ---------------------------------------------------------------------------
# Event payload contracts (documentation + validation hints)
# ---------------------------------------------------------------------------
TELEMETRY_PAYLOADS: dict[str, dict[str, str]] = {
    TelemetryEvent.RUNTIME_HEARTBEAT: {
        "service": "str — service name",
        "version": "str — service version",
        "uptime_seconds": "float — seconds since service start",
        "memory_mb": "float — current memory usage (optional)",
        "cpu_percent": "float — current CPU usage (optional)",
    },
    TelemetryEvent.MISSION_CREATED: {
        "mission_id": "str — unique mission identifier",
        "mission_name": "str — human-readable mission name",
        "mission_type": "str — mission category/type",
        "created_by": "str — actor that created the mission",
    },
    TelemetryEvent.MISSION_COMPLETED: {
        "mission_id": "str — unique mission identifier",
        "result": "str — success | failed | cancelled",
        "duration_seconds": "float — total execution time",
        "tokens_used": "int — total LLM tokens consumed (optional)",
        "cost_usd": "float — total cost in USD (optional)",
    },
    TelemetryEvent.MEMORY_INGESTED: {
        "doc_id": "str — document identifier",
        "doc_title": "str — document title",
        "chunk_count": "int — number of chunks created",
        "source_type": "str — md | pdf | docx | txt",
        "source_badge": "str — origin system badge",
    },
    TelemetryEvent.COST_RECORDED: {
        "provider": "str — LLM provider or service name",
        "model": "str — model name",
        "tokens": "int — tokens consumed",
        "cost_usd": "float — cost in USD",
        "mission_id": "str — associated mission (optional)",
    },
    TelemetryEvent.RISK_DETECTED: {
        "risk_id": "str — unique risk identifier",
        "risk_level": "str — low | medium | high | critical",
        "source": "str — system that detected the risk",
        "description": "str — human-readable risk description",
        "action": "str — recommended action",
    },
}


# ---------------------------------------------------------------------------
# Event type to channel mapping (which channel each event type belongs to)
# ---------------------------------------------------------------------------
from .channels import Channel  # noqa: E402

TELEMETRY_CHANNEL_MAP: dict[TelemetryEvent, Channel] = {
    TelemetryEvent.RUNTIME_HEARTBEAT: Channel.OMNIS_RUNTIME,
    TelemetryEvent.MISSION_CREATED: Channel.MISSION_EVENTS,
    TelemetryEvent.MISSION_COMPLETED: Channel.MISSION_EVENTS,
    TelemetryEvent.MEMORY_INGESTED: Channel.AKASHA_MEMORY,
    TelemetryEvent.COST_RECORDED: Channel.FINANCE_COST,
    TelemetryEvent.RISK_DETECTED: Channel.OMNIS_RUNTIME,
}
