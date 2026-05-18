"""W183 — Mission Scheduler: planned/timed mission queuing."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.first_missions.models import Mission, MissionPriority, MissionStatus, _new_id, _now_iso


class ScheduleStatus(str, Enum):
    WAITING = "WAITING"
    READY = "READY"
    DISPATCHED = "DISPATCHED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass
class ScheduledMission:
    entry_id: str = field(default_factory=lambda: _new_id("sch"))
    mission: Optional[Mission] = None
    run_at: str = ""          # ISO timestamp; empty = run immediately
    status: ScheduleStatus = ScheduleStatus.WAITING
    recurrent: bool = False
    interval_seconds: float = 0.0
    created_at: str = field(default_factory=_now_iso)
    dispatched_at: str = ""

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "mission_id": self.mission.mission_id if self.mission else None,
            "run_at": self.run_at,
            "status": self.status.value,
            "recurrent": self.recurrent,
            "interval_seconds": self.interval_seconds,
            "created_at": self.created_at,
            "dispatched_at": self.dispatched_at,
        }


class MissionScheduler:
    """Queue-based scheduler for missions — dry_run-safe, no real sleep."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self._queue: list[ScheduledMission] = []
        self._dispatched: list[ScheduledMission] = []

    def schedule(
        self,
        mission: Mission,
        run_at: str = "",
        recurrent: bool = False,
        interval_seconds: float = 0.0,
    ) -> ScheduledMission:
        entry = ScheduledMission(
            mission=mission,
            run_at=run_at,
            status=ScheduleStatus.WAITING if run_at else ScheduleStatus.READY,
            recurrent=recurrent,
            interval_seconds=interval_seconds,
        )
        self._queue.append(entry)
        return entry

    def schedule_now(self, mission: Mission) -> ScheduledMission:
        return self.schedule(mission, run_at="")

    def cancel(self, entry_id: str) -> bool:
        for entry in self._queue:
            if entry.entry_id == entry_id and entry.status not in (
                ScheduleStatus.DISPATCHED, ScheduleStatus.CANCELLED, ScheduleStatus.EXPIRED
            ):
                entry.status = ScheduleStatus.CANCELLED
                return True
        return False

    def ready(self, _now: str = "") -> list[ScheduledMission]:
        """Return entries that are ready to dispatch (run_at <= now or empty)."""
        result = []
        for entry in self._queue:
            if entry.status != ScheduleStatus.WAITING and entry.status != ScheduleStatus.READY:
                continue
            if entry.run_at == "":
                result.append(entry)
                continue
            # In dry_run or with _now override, compare as strings (ISO sort order)
            now = _now or _now_iso()
            if entry.run_at <= now:
                entry.status = ScheduleStatus.READY
                result.append(entry)
        return result

    def dispatch_ready(self, _now: str = "") -> list[Mission]:
        """Mark ready entries as dispatched, return their missions."""
        missions = []
        for entry in self.ready(_now=_now):
            if entry.status == ScheduleStatus.CANCELLED:
                continue
            entry.status = ScheduleStatus.DISPATCHED
            entry.dispatched_at = _now_iso()
            self._dispatched.append(entry)
            if entry.mission:
                missions.append(entry.mission)
        # Remove dispatched non-recurrent from queue
        self._queue = [e for e in self._queue if e.status not in (
            ScheduleStatus.DISPATCHED, ScheduleStatus.CANCELLED, ScheduleStatus.EXPIRED
        ) or e.recurrent]
        return missions

    def pending(self) -> list[ScheduledMission]:
        return [e for e in self._queue if e.status in (ScheduleStatus.WAITING, ScheduleStatus.READY)]

    def history(self) -> list[ScheduledMission]:
        return list(self._dispatched)

    def stats(self) -> dict:
        return {
            "queued": len(self._queue),
            "pending": len(self.pending()),
            "dispatched": len(self._dispatched),
            "dry_run": self.dry_run,
        }
