"""W192 — Mission Logger: structured logging for mission lifecycle."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TextIO, Optional

from src.first_missions.models import Mission


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MissionLogEntry:
    """A single structured log entry for a mission event."""
    mission_id: str
    event: str
    status: str
    mission_name: str = ""
    mission_type: str = ""
    duration_ms: float = 0.0
    error: str = ""
    dry_run: bool = True
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "event": self.event,
            "status": self.status,
            "mission_name": self.mission_name,
            "mission_type": self.mission_type,
            "duration_ms": round(self.duration_ms, 2),
            "dry_run": self.dry_run,
            "timestamp": self.timestamp,
        }

    def format_line(self) -> str:
        """Human-readable single-line format."""
        mode = "DRY" if self.dry_run else "LIVE"
        parts = [
            f"[{self.timestamp}]",
            f"[{mode}]",
            f"[{self.event.upper()}]",
            f"mission={self.mission_id[:12]}",
            f"name={self.mission_name[:30]}" if self.mission_name else "",
            f"type={self.mission_type}",
            f"status={self.status}",
        ]
        if self.duration_ms > 0:
            parts.append(f"dur={self.duration_ms:.0f}ms")
        if self.error:
            parts.append(f"error={self.error[:80]}")
        return " ".join(p for p in parts if p)


class MissionLogger:
    """Structured logger for mission execution. In-memory by default."""

    def __init__(self, dry_run: bool = True, stream: Optional[TextIO] = None) -> None:
        self.dry_run = dry_run
        self._stream = stream
        self._entries: list[MissionLogEntry] = []

    def log_start(self, mission: Mission) -> MissionLogEntry:
        entry = MissionLogEntry(
            mission_id=mission.mission_id,
            event="start",
            status=mission.status.value,
            mission_name=mission.name,
            mission_type=mission.mission_type.value,
            dry_run=self.dry_run,
        )
        self._store(entry)
        return entry

    def log_complete(self, mission: Mission, duration_ms: float = 0.0) -> MissionLogEntry:
        entry = MissionLogEntry(
            mission_id=mission.mission_id,
            event="complete",
            status=mission.status.value,
            mission_name=mission.name,
            mission_type=mission.mission_type.value,
            duration_ms=duration_ms,
            error=mission.error,
            dry_run=self.dry_run,
        )
        self._store(entry)
        return entry

    def log_fail(self, mission: Mission, duration_ms: float = 0.0) -> MissionLogEntry:
        entry = MissionLogEntry(
            mission_id=mission.mission_id,
            event="fail",
            status=mission.status.value,
            mission_name=mission.name,
            mission_type=mission.mission_type.value,
            duration_ms=duration_ms,
            error=mission.error,
            dry_run=self.dry_run,
        )
        self._store(entry)
        return entry

    def _store(self, entry: MissionLogEntry) -> None:
        self._entries.append(entry)
        if self._stream and not self.dry_run:
            self._stream.write(entry.format_line() + "\n")
            self._stream.flush()

    def entries(self) -> list[MissionLogEntry]:
        return list(self._entries)

    def stats(self) -> dict:
        by_event: dict[str, int] = {}
        for e in self._entries:
            by_event[e.event] = by_event.get(e.event, 0) + 1
        return {"total": len(self._entries), "by_event": by_event}

    def clear(self) -> None:
        self._entries.clear()
