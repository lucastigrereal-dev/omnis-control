"""
OMNIS Bus — Unified event bus foundation.

Canonical envelope, channel taxonomy, event health, replay, and failure handling.
"""

from .envelope import (
    CanonicalEnvelope,
    EventStatus,
    Severity,
    SourceBadge,
    SourceInfo,
    make_envelope,
    validate_envelope,
)
from .channels import CHANNELS, LEGACY_MAP, Channel, channel_for
from .health import BusHealth, HealthCollector, health_to_event_envelope
from .telemetry import TELEMETRY_CHANNEL_MAP, TELEMETRY_PAYLOADS, TelemetryEvent
from .failures import (
    FAILURE_STRATEGY_MAP,
    DuplicateDetector,
    FailureIncident,
    FailureLog,
    FailureMode,
    ReconnectBackoff,
    RecoveryStrategy,
    SafeMessageHandler,
)
from .replay import ReplayBuffer

__all__ = [
    # Envelope
    "CanonicalEnvelope",
    "validate_envelope",
    "make_envelope",
    "SourceBadge",
    "SourceInfo",
    "Severity",
    "EventStatus",
    # Channels
    "Channel",
    "CHANNELS",
    "channel_for",
    "LEGACY_MAP",
    # Health
    "BusHealth",
    "HealthCollector",
    "health_to_event_envelope",
    # Telemetry
    "TelemetryEvent",
    "TELEMETRY_PAYLOADS",
    "TELEMETRY_CHANNEL_MAP",
    # Failures
    "FailureMode",
    "RecoveryStrategy",
    "FAILURE_STRATEGY_MAP",
    "FailureIncident",
    "FailureLog",
    "ReconnectBackoff",
    "DuplicateDetector",
    "SafeMessageHandler",
    # Replay
    "ReplayBuffer",
]
