import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class SkillEventType(str, Enum):
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    PERMISSION_CHECKED = "PERMISSION_CHECKED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    EXECUTION_BLOCKED = "EXECUTION_BLOCKED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    ARTIFACT_GENERATED = "ARTIFACT_GENERATED"


@dataclass
class SkillExecutionEvent:
    event_id: str = field(default_factory=lambda: _new_id("see"))
    event_type: SkillEventType = SkillEventType.REQUEST_RECEIVED
    request_id: str = ""
    skill_id: str = ""
    detail: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "request_id": self.request_id,
            "skill_id": self.skill_id,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SkillExecutionEvent":
        return cls(
            event_id=data.get("event_id", ""),
            event_type=SkillEventType(data.get("event_type", "REQUEST_RECEIVED")),
            request_id=data.get("request_id", ""),
            skill_id=data.get("skill_id", ""),
            detail=data.get("detail", {}),
            timestamp=data.get("timestamp", ""),
        )


class SkillEventBus:
    def __init__(self):
        self._events: list[SkillExecutionEvent] = []
        self._subscribers: dict[str, list[callable]] = {}

    def emit(self, event: SkillExecutionEvent) -> None:
        self._events.append(event)
        handlers = self._subscribers.get(event.event_type.value, [])
        for handler in handlers:
            handler(event)

    def subscribe(self, event_type: SkillEventType, handler: callable) -> None:
        key = event_type.value
        if key not in self._subscribers:
            self._subscribers[key] = []
        self._subscribers[key].append(handler)

    def query(self, event_type: str = "", skill_id: str = "") -> list[SkillExecutionEvent]:
        results = self._events
        if event_type:
            results = [e for e in results if e.event_type.value == event_type]
        if skill_id:
            results = [e for e in results if e.skill_id == skill_id]
        return results

    @property
    def event_count(self) -> int:
        return len(self._events)

    def to_dict(self) -> dict:
        return {
            "events": [e.to_dict() for e in self._events],
        }
