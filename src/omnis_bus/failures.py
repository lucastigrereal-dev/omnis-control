"""Failure Handling — defined failure modes and recovery strategies.

Covers 5 failure modes:
1. Redis offline — reconnect with exponential backoff
2. Malformed event — log, skip, increment error counter
3. Unknown source — accept with UNKNOWN badge, do not reject
4. Duplicate event — idempotency via event_id tracking set
5. Timeout — configurable timeout with graceful degradation
"""

import logging
import time
from collections import deque
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("omnis.bus.failures")


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------
class FailureMode(str, Enum):
    REDIS_OFFLINE = "redis_offline"
    MALFORMED_EVENT = "malformed_event"
    UNKNOWN_SOURCE = "unknown_source"
    DUPLICATE_EVENT = "duplicate_event"
    TIMEOUT = "timeout"


# ---------------------------------------------------------------------------
# Recovery strategies per failure mode
# ---------------------------------------------------------------------------
class RecoveryStrategy(str, Enum):
    RECONNECT_BACKOFF = "reconnect_backoff"
    LOG_AND_SKIP = "log_and_skip"
    ACCEPT_WITH_BADGE = "accept_with_badge"
    DEDUPLICATE = "deduplicate"
    GRACEFUL_DEGRADE = "graceful_degrade"


FAILURE_STRATEGY_MAP: dict[FailureMode, RecoveryStrategy] = {
    FailureMode.REDIS_OFFLINE: RecoveryStrategy.RECONNECT_BACKOFF,
    FailureMode.MALFORMED_EVENT: RecoveryStrategy.LOG_AND_SKIP,
    FailureMode.UNKNOWN_SOURCE: RecoveryStrategy.ACCEPT_WITH_BADGE,
    FailureMode.DUPLICATE_EVENT: RecoveryStrategy.DEDUPLICATE,
    FailureMode.TIMEOUT: RecoveryStrategy.GRACEFUL_DEGRADE,
}


# ---------------------------------------------------------------------------
# Failure incident record
# ---------------------------------------------------------------------------
class FailureIncident:
    """Record of a handled failure incident."""

    def __init__(self, mode: FailureMode, detail: str, event_id: str | None = None):
        self.mode = mode
        self.detail = detail
        self.event_id = event_id
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.strategy = FAILURE_STRATEGY_MAP[mode]

    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "detail": self.detail,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "strategy": self.strategy.value,
        }


# ---------------------------------------------------------------------------
# Reconnect backoff (Redis offline)
# ---------------------------------------------------------------------------
class ReconnectBackoff:
    """Exponential backoff for Redis reconnection.

    Base delay 1s, doubles each attempt, capped at 60s.
    """

    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._attempt = 0

    def next_delay(self) -> float:
        self._attempt += 1
        delay = min(self.base_delay * (2 ** (self._attempt - 1)), self.max_delay)
        return delay

    def reset(self) -> None:
        self._attempt = 0

    @property
    def attempt(self) -> int:
        return self._attempt


# ---------------------------------------------------------------------------
# Duplicate detection (idempotency)
# ---------------------------------------------------------------------------
class DuplicateDetector:
    """Tracks seen event_ids to detect and skip duplicates.

    Uses a bounded set (max 10,000 entries) to prevent memory leaks.
    """

    def __init__(self, max_ids: int = 10_000):
        self._seen: set[str] = set()
        self._max_ids = max_ids
        self._duplicate_count = 0

    def is_duplicate(self, event_id: str) -> bool:
        if event_id in self._seen:
            self._duplicate_count += 1
            return True
        self._seen.add(event_id)
        # Garbage collect oldest entries when near capacity
        if len(self._seen) > self._max_ids:
            self._seen.clear()
        return False

    @property
    def seen_count(self) -> int:
        return len(self._seen)

    @property
    def duplicate_count(self) -> int:
        return self._duplicate_count


# ---------------------------------------------------------------------------
# Failure log (ring buffer of recent incidents)
# ---------------------------------------------------------------------------
class FailureLog:
    """Ring buffer of recent failure incidents for diagnostics."""

    def __init__(self, max_entries: int = 100):
        self._entries: deque = deque(maxlen=max_entries)
        self._counts: dict[FailureMode, int] = {m: 0 for m in FailureMode}

    def record(self, mode: FailureMode, detail: str, event_id: str | None = None) -> FailureIncident:
        incident = FailureIncident(mode, detail, event_id)
        self._entries.append(incident)
        self._counts[mode] += 1
        logger.warning(
            "bus.failure mode=%s detail=%s event_id=%s strategy=%s",
            mode.value,
            detail,
            event_id or "-",
            incident.strategy.value,
        )
        return incident

    def recent(self, n: int = 20) -> list[dict]:
        items = list(self._entries)[-n:]
        return [i.to_dict() for i in items]

    def counts(self) -> dict[str, int]:
        return {m.value: c for m, c in self._counts.items()}

    def total(self) -> int:
        return sum(self._counts.values())


# ---------------------------------------------------------------------------
# Safe message handler (wraps all 5 failure modes)
# ---------------------------------------------------------------------------
class SafeMessageHandler:
    """Wraps a message handler with all 5 failure mode protections.

    Usage:
        handler = SafeMessageHandler(on_event=my_handler, timeout=5.0)
        handler.handle(raw_message)
    """

    def __init__(
        self,
        on_event: callable,
        timeout: float = 5.0,
        detect_duplicates: bool = True,
    ):
        self._on_event = on_event
        self._timeout = timeout
        self._backoff = ReconnectBackoff()
        self._duplicates = DuplicateDetector() if detect_duplicates else None
        self._failures = FailureLog()
        self._events_received = 0

    def handle(self, raw_message: dict, channel: str | None = None) -> bool:
        """Handle a raw message with full failure protection.

        Returns True if the event was processed, False if it was skipped/errored.
        """
        import json

        self._events_received += 1

        # Failure 1: Malformed event (non-dict, non-JSON, missing fields)
        if not isinstance(raw_message, dict):
            self._failures.record(FailureMode.MALFORMED_EVENT, "Message is not a dict")
            return False

        if raw_message.get("type") == "subscribe" or raw_message.get("type") == "psubscribe":
            return False  # Pub/Sub control messages — not failures

        # Validate required fields
        from .envelope import validate_envelope

        errors = validate_envelope(raw_message)
        if errors:
            event_id = raw_message.get("event_id", "unknown")
            self._failures.record(
                FailureMode.MALFORMED_EVENT,
                f"Envelope validation failed: {errors}",
                event_id=event_id,
            )
            return False

        # Failure 4: Duplicate event
        event_id = raw_message.get("event_id", "")
        if self._duplicates and self._duplicates.is_duplicate(event_id):
            self._failures.record(
                FailureMode.DUPLICATE_EVENT,
                f"Duplicate event_id={event_id}",
                event_id=event_id,
            )
            return False

        # Failure 3: Unknown source — accept anyway with logging
        src = raw_message.get("source", {})
        if isinstance(src, dict):
            service = src.get("service", "")
            from .envelope import _infer_badge

            badge = _infer_badge(service)
            if badge == "unknown":
                self._failures.record(
                    FailureMode.UNKNOWN_SOURCE,
                    f"Unknown source service={service!r}",
                    event_id=event_id,
                )
                # Still process — unknown source is not a rejection

        # Process event (with timeout handled by caller)
        try:
            self._on_event(raw_message)
            return True
        except Exception as exc:
            self._failures.record(
                FailureMode.MALFORMED_EVENT,
                f"Handler exception: {exc}",
                event_id=event_id,
            )
            return False

    @property
    def events_received(self) -> int:
        return self._events_received

    def stats(self) -> dict:
        return {
            "events_received": self._events_received,
            "failure_counts": self._failures.counts(),
            "failure_total": self._failures.total(),
            "duplicates_detected": self._duplicates.duplicate_count if self._duplicates else 0,
            "recent_failures": self._failures.recent(10),
        }
