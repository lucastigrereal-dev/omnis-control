"""W167 — KRATOS Bridge Event Stream: real-time event bus between OMNIS and cockpit (mock)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from .models import _new_id, _now_iso


class EventType(str, Enum):
    WAVE_STARTED = "WAVE_STARTED"
    WAVE_COMPLETED = "WAVE_COMPLETED"
    TEST_PASSED = "TEST_PASSED"
    TEST_FAILED = "TEST_FAILED"
    MISSION_CREATED = "MISSION_CREATED"
    MISSION_EXECUTED = "MISSION_EXECUTED"
    ALERT_RAISED = "ALERT_RAISED"
    METRIC_UPDATED = "METRIC_UPDATED"
    SYSTEM_STATUS = "SYSTEM_STATUS"
    COMMAND_RECEIVED = "COMMAND_RECEIVED"
    COMMAND_EXECUTED = "COMMAND_EXECUTED"
    HEALTH_CHANGED = "HEALTH_CHANGED"


EventHandler = Callable[["OmnisEvent"], None]


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------

@dataclass
class OmnisEvent:
    event_id: str = field(default_factory=lambda: _new_id("evt"))
    event_type: EventType = EventType.SYSTEM_STATUS
    source: str = "omnis"
    payload: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    emitted_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source,
            "payload": self.payload,
            "tags": self.tags,
            "emitted_at": self.emitted_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OmnisEvent":
        return cls(
            event_id=data.get("event_id", _new_id("evt")),
            event_type=EventType(data.get("event_type", "SYSTEM_STATUS")),
            source=data.get("source", "omnis"),
            payload=data.get("payload", {}),
            tags=data.get("tags", []),
            emitted_at=data.get("emitted_at", _now_iso()),
        )

    # Convenience factories
    @classmethod
    def wave_completed(cls, wave: str, tests: int) -> "OmnisEvent":
        return cls(event_type=EventType.WAVE_COMPLETED, payload={"wave": wave, "tests": tests}, tags=["wave"])

    @classmethod
    def test_result(cls, passed: bool, count: int) -> "OmnisEvent":
        etype = EventType.TEST_PASSED if passed else EventType.TEST_FAILED
        return cls(event_type=etype, payload={"count": count, "passed": passed}, tags=["test"])

    @classmethod
    def metric_updated(cls, name: str, value: float) -> "OmnisEvent":
        return cls(event_type=EventType.METRIC_UPDATED, payload={"name": name, "value": value})

    @classmethod
    def alert_raised(cls, message: str, level: str = "HIGH") -> "OmnisEvent":
        return cls(event_type=EventType.ALERT_RAISED, payload={"message": message, "level": level}, tags=["alert"])


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------

@dataclass
class Subscription:
    sub_id: str = field(default_factory=lambda: _new_id("sub"))
    event_types: list[EventType] = field(default_factory=list)  # empty = all
    tags: list[str] = field(default_factory=list)              # empty = all tags
    handler: Optional[EventHandler] = None
    active: bool = True

    def matches(self, event: OmnisEvent) -> bool:
        if not self.active:
            return False
        type_match = not self.event_types or event.event_type in self.event_types
        tag_match = not self.tags or any(t in event.tags for t in self.tags)
        return type_match and tag_match


# ---------------------------------------------------------------------------
# Event stream
# ---------------------------------------------------------------------------

class KratosEventStream:
    """Mock event bus: emit OmnisEvents, route to subscribed handlers."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self._events: list[OmnisEvent] = []
        self._subscriptions: dict[str, Subscription] = {}

    # ------------------------------------------------------------------
    def subscribe(
        self,
        handler: EventHandler,
        event_types: Optional[list[EventType]] = None,
        tags: Optional[list[str]] = None,
    ) -> Subscription:
        sub = Subscription(
            event_types=event_types or [],
            tags=tags or [],
            handler=handler,
        )
        self._subscriptions[sub.sub_id] = sub
        return sub

    def unsubscribe(self, sub_id: str) -> bool:
        sub = self._subscriptions.get(sub_id)
        if sub:
            sub.active = False
            return True
        return False

    # ------------------------------------------------------------------
    def emit(self, event: OmnisEvent) -> int:
        """Emit event and return number of handlers invoked."""
        self._events.append(event)
        count = 0
        for sub in self._subscriptions.values():
            if sub.matches(event) and sub.handler is not None:
                if not self.dry_run:
                    sub.handler(event)
                count += 1
        return count

    def emit_many(self, events: list[OmnisEvent]) -> list[int]:
        return [self.emit(e) for e in events]

    # ------------------------------------------------------------------
    def replay(self, event_type: Optional[EventType] = None) -> list[OmnisEvent]:
        if event_type is None:
            return list(self._events)
        return [e for e in self._events if e.event_type == event_type]

    def latest(self, count: int = 10) -> list[OmnisEvent]:
        return list(self._events[-count:])

    def clear(self) -> None:
        self._events.clear()

    # ------------------------------------------------------------------
    def stats(self) -> dict:
        by_type: dict[str, int] = {}
        for e in self._events:
            by_type[e.event_type.value] = by_type.get(e.event_type.value, 0) + 1
        return {
            "total_events": len(self._events),
            "active_subscriptions": sum(1 for s in self._subscriptions.values() if s.active),
            "by_type": by_type,
            "dry_run": self.dry_run,
        }
