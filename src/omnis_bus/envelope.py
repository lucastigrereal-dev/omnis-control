"""Canonical Event Envelope — unified contract across OMNIS, AKASHA, and KRATOS."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

import uuid

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Source Badge — identifies the originating system
# ---------------------------------------------------------------------------
class SourceBadge(str, Enum):
    OMNIS = "omnis"
    AKASHA = "akasha"
    KRATOS = "kratos"
    PUBLISHER_OS = "publisher-os"
    CRM = "crm"
    FINANCE = "finance"
    UNKNOWN = "unknown"


# Source metadata (service + version + badge)
class SourceInfo(BaseModel):
    service: str
    version: str
    badge: SourceBadge = SourceBadge.UNKNOWN
    instance: str | None = None


# ---------------------------------------------------------------------------
# Severity & Status enums
# ---------------------------------------------------------------------------
class Severity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


class EventStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    FAILED = "failed"
    PENDING = "pending"


# ---------------------------------------------------------------------------
# Canonical Envelope (10 fields)
# ---------------------------------------------------------------------------
class CanonicalEnvelope(BaseModel):
    """Unified event envelope for all OMNIS Bus communication.

    Fields:
        event_id:   Unique event identifier (generated if not provided)
        type:       Event type (e.g. system.heartbeat, mission.created)
        source:     Originating system info (service, version, badge)
        timestamp:  UTC timestamp of event creation
        payload:    Event-specific data
        correlation_id: Links related events across systems
        mission_id: Associated mission (if any)
        trace_id:   Distributed trace ID for E2E observability
        severity:   Event severity level
        status:     Event status
        source_badge: Short identifier for the source system
    """

    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    type: str
    source: SourceInfo
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = Field(default_factory=lambda: f"corr-{uuid.uuid4().hex[:8]}")
    mission_id: str | None = None
    trace_id: str | None = None
    severity: Severity = Severity.INFO
    status: EventStatus = EventStatus.OK
    source_badge: SourceBadge = SourceBadge.UNKNOWN

    @model_validator(mode="after")
    def sync_source_badge(self) -> "CanonicalEnvelope":
        """If source_badge is UNKNOWN, derive from source.badge."""
        if self.source_badge == SourceBadge.UNKNOWN and self.source.badge != SourceBadge.UNKNOWN:
            self.source_badge = self.source.badge
        return self

    def to_redis_payload(self) -> dict[str, Any]:
        """Serialize to Redis-compatible dict with source expanded."""
        return self.model_dump(mode="json")

    @classmethod
    def from_redis_payload(cls, data: dict[str, Any]) -> "CanonicalEnvelope":
        """Deserialize from Redis message dict.

        Handles legacy V2 envelopes by mapping event_type -> type
        and extracting source_badge from source.service.
        """
        normalized = dict(data)

        # Map legacy V2 field names
        if "type" not in normalized and "event_type" in normalized:
            normalized["type"] = normalized.pop("event_type")

        # Normalize source: extract badge from service name if missing
        src = normalized.get("source", {})
        if isinstance(src, dict):
            if "badge" not in src:
                src["badge"] = _infer_badge(src.get("service", ""))
            normalized["source"] = src

        # Normalize source_badge
        if "source_badge" not in normalized:
            normalized["source_badge"] = _infer_badge(
                normalized.get("source", {}).get("service", "")
            )

        return cls(**normalized)


# ---------------------------------------------------------------------------
# Validation (replaces legacy validate_envelope)
# ---------------------------------------------------------------------------
def validate_envelope(data: dict[str, Any]) -> list[str]:
    """Validate an event dict against the canonical envelope contract.

    Returns a list of error messages. Empty list = valid.
    Backward-compatible with V2 envelope format.
    """
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["Event is not a dict"]

    # Required fields (accept both legacy event_type and new type)
    event_type_key = "type" if "type" in data else "event_type"
    required = {"event_id", event_type_key, "timestamp", "source", "severity", "status", "payload"}
    missing = required - set(data.keys())
    if missing:
        errors.append(f"Missing fields: {sorted(missing)}")

    # Validate severity
    valid_severities = {s.value for s in Severity}
    sev = data.get("severity")
    if sev is not None and sev not in valid_severities:
        errors.append(f"Invalid severity: {sev!r} (valid: {sorted(valid_severities)})")

    # Validate status
    valid_statuses = {s.value for s in EventStatus}
    st = data.get("status")
    if st is not None and st not in valid_statuses:
        errors.append(f"Invalid status: {st!r} (valid: {sorted(valid_statuses)})")

    # Validate source
    src = data.get("source")
    if isinstance(src, dict):
        if "service" not in src:
            errors.append("Missing source.service")
        if "version" not in src:
            errors.append("Missing source.version")
    elif src is not None:
        errors.append(f"source must be a dict, got {type(src).__name__}")

    return errors


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _infer_badge(service: str) -> str:
    """Infer source badge from service name."""
    service_lower = service.lower()
    if "kratos" in service_lower:
        return SourceBadge.KRATOS.value
    if "omnis" in service_lower:
        return SourceBadge.OMNIS.value
    if "akasha" in service_lower:
        return SourceBadge.AKASHA.value
    if "publisher" in service_lower:
        return SourceBadge.PUBLISHER_OS.value
    if "crm" in service_lower:
        return SourceBadge.CRM.value
    if "finance" in service_lower or "gringotts" in service_lower:
        return SourceBadge.FINANCE.value
    return SourceBadge.UNKNOWN.value


def make_envelope(
    event_type: str,
    payload: dict[str, Any],
    source_service: str,
    source_version: str,
    source_badge: SourceBadge | None = None,
    severity: Severity = Severity.INFO,
    status: EventStatus = EventStatus.OK,
    correlation_id: str | None = None,
    mission_id: str | None = None,
    trace_id: str | None = None,
) -> CanonicalEnvelope:
    """Factory for creating canonical envelopes with sensible defaults."""
    badge = source_badge or _infer_badge(source_service)
    return CanonicalEnvelope(
        type=event_type,
        source=SourceInfo(
            service=source_service,
            version=source_version,
            badge=SourceBadge(badge) if isinstance(badge, str) else badge,
        ),
        payload=payload,
        severity=severity,
        status=status,
        correlation_id=correlation_id or f"corr-{uuid.uuid4().hex[:8]}",
        mission_id=mission_id,
        trace_id=trace_id,
        source_badge=SourceBadge(badge) if isinstance(badge, str) else badge,
    )
