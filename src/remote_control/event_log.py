from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.remote_control.models import RemoteCommand, CommandSource


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


class RemoteEventType(str, Enum):
    COMMAND_RECEIVED = "COMMAND_RECEIVED"
    SECURITY_CHECKED = "SECURITY_CHECKED"
    WHITELIST_CHECKED = "WHITELIST_CHECKED"
    CHALLENGE_ISSUED = "CHALLENGE_ISSUED"
    CHALLENGE_RESOLVED = "CHALLENGE_RESOLVED"
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass
class RemoteEvent:
    event_id: str = field(default_factory=lambda: _new_id("re_"))
    event_type: RemoteEventType = RemoteEventType.COMMAND_RECEIVED
    command_id: str = ""
    source: str = ""
    detail: dict = field(default_factory=dict)
    recorded_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "command_id": self.command_id,
            "source": self.source,
            "detail": self.detail,
            "recorded_at": self.recorded_at,
        }


class RemoteEventLog:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._events: list[RemoteEvent] = []

    def record(self, event_type: RemoteEventType, cmd: RemoteCommand, detail: dict | None = None) -> RemoteEvent:
        event = RemoteEvent(
            event_type=event_type,
            command_id=cmd.command_id,
            source=cmd.source.value,
            detail=detail or {},
        )
        self._events.append(event)
        return event

    def query(self, command_id: str = "", event_type: str = "", source: str = "") -> list[RemoteEvent]:
        results = self._events
        if command_id:
            results = [e for e in results if e.command_id == command_id]
        if event_type:
            results = [e for e in results if e.event_type.value == event_type]
        if source:
            results = [e for e in results if e.source == source]
        return results

    def command_timeline(self, command_id: str) -> list[dict]:
        return [e.to_dict() for e in self._events if e.command_id == command_id]

    @property
    def last_event(self) -> RemoteEvent | None:
        return self._events[-1] if self._events else None

    @property
    def event_count(self) -> int:
        return len(self._events)
