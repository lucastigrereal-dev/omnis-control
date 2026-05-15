import json
from abc import ABC, abstractmethod
from pathlib import Path

from src.akasha_event_sink.models import SinkEvent, SinkStatus, _now_iso


class AkashaSinkAdapter(ABC):
    @abstractmethod
    def write_event(self, event: SinkEvent) -> bool:
        pass

    @abstractmethod
    def query_events(self, event_type: str = "") -> list[SinkEvent]:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass


class FileAkashaSink(AkashaSinkAdapter):
    def __init__(self, target_dir: str, dry_run: bool = True):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run

    def write_event(self, event: SinkEvent) -> bool:
        if self.dry_run:
            event.status = SinkStatus.QUEUED
            return True
        try:
            self.target_dir.mkdir(parents=True, exist_ok=True)
            filepath = self.target_dir / f"{event.event_id}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(event.to_dict(), f, indent=2)
            event.status = SinkStatus.WRITTEN
            event.written_at = _now_iso()
            return True
        except Exception:
            event.status = SinkStatus.FAILED
            return False

    def query_events(self, event_type: str = "") -> list[SinkEvent]:
        events = []
        if not self.target_dir.exists():
            return events
        for filepath in sorted(self.target_dir.glob("*.json")):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                event = SinkEvent.from_dict(data)
                if not event_type or event.event_type == event_type:
                    events.append(event)
            except Exception:
                pass
        return events

    def health_check(self) -> bool:
        return self.target_dir.exists() or self.dry_run


class MockAkashaSink(AkashaSinkAdapter):
    def __init__(self):
        self._events: list[SinkEvent] = []

    def write_event(self, event: SinkEvent) -> bool:
        event.status = SinkStatus.WRITTEN
        event.written_at = _now_iso()
        self._events.append(event)
        return True

    def query_events(self, event_type: str = "") -> list[SinkEvent]:
        if not event_type:
            return list(self._events)
        return [e for e in self._events if e.event_type == event_type]

    def health_check(self) -> bool:
        return True
