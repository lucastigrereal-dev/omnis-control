"""W191 — Mission Event Emitter: bridges first_missions to OmnisEvent bus."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from src.first_missions.models import Mission, MissionStatus

if TYPE_CHECKING:
    from src.omnis_os.event_bus import EventBus


# ---------------------------------------------------------------------------
# Standalone event model (no dependency on omnis_os)
# ---------------------------------------------------------------------------

@dataclass
class MissionEvent:
    """Lightweight mission lifecycle event — works without omnis_os."""
    event_id: str
    event_type: str
    mission_id: str
    mission_name: str
    mission_type: str
    status: str
    timestamp: str
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "mission_id": self.mission_id,
            "mission_name": self.mission_name,
            "mission_type": self.mission_type,
            "status": self.status,
            "timestamp": self.timestamp,
            "data": self.data,
        }


def _mission_event_id(prefix: str = "mev") -> str:
    from uuid import uuid4
    return f"{prefix}_{uuid4().hex[:8]}"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# MissionEventEmitter
# ---------------------------------------------------------------------------

class MissionEventEmitter:
    """Emits mission lifecycle events, optionally to an OmnisEventBus."""

    def __init__(self, dry_run: bool = True, bus: Optional["EventBus"] = None) -> None:
        self.dry_run = dry_run
        self._bus = bus
        self._events: list[MissionEvent] = []

    def _emit(self, event_type: str, mission: Mission, extra: Optional[dict] = None) -> MissionEvent:
        event = MissionEvent(
            event_id=_mission_event_id(),
            event_type=event_type,
            mission_id=mission.mission_id,
            mission_name=mission.name,
            mission_type=mission.mission_type.value,
            status=mission.status.value,
            timestamp=_now_iso(),
            data=extra or {},
        )
        self._events.append(event)

        # Bridge to OmnisEventBus if available
        if self._bus is not None and not self.dry_run:
            try:
                self._bus.emit_new(
                    event_type=f"mission.{event_type}",
                    source_module="first_missions",
                    data=event.to_dict(),
                )
            except Exception:
                pass

        return event

    def mission_started(self, mission: Mission) -> MissionEvent:
        return self._emit("started", mission)

    def mission_completed(self, mission: Mission) -> MissionEvent:
        return self._emit("completed", mission, extra={"result": mission.result})

    def mission_failed(self, mission: Mission) -> MissionEvent:
        return self._emit("failed", mission, extra={"error": mission.error})

    def mission_dry_run(self, mission: Mission) -> MissionEvent:
        return self._emit("dry_run", mission, extra={"result": mission.result})

    def emit_for(self, mission: Mission) -> MissionEvent:
        """Emit the appropriate event based on mission status."""
        if mission.status == MissionStatus.COMPLETED:
            return self.mission_completed(mission)
        elif mission.status == MissionStatus.FAILED:
            return self.mission_failed(mission)
        elif mission.status == MissionStatus.DRY_RUN:
            return self.mission_dry_run(mission)
        elif mission.status == MissionStatus.RUNNING:
            return self.mission_started(mission)
        else:
            return self._emit("status_change", mission)

    def history(self) -> list[MissionEvent]:
        return list(self._events)

    def stats(self) -> dict:
        by_type: dict[str, int] = {}
        for e in self._events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
        return {"total": len(self._events), "by_type": by_type}
