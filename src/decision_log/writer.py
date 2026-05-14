import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from src.decision_log.models import BaseEvent, LogEvent


class LogWriter:
    def __init__(self, base_dir: Optional[str] = None):
        self._dir = Path(base_dir) if base_dir else None
        self._memory: list[LogEvent] = []

    @property
    def memory(self) -> list[LogEvent]:
        return list(self._memory)

    def write(self, event: BaseEvent) -> LogEvent:
        log_event = event.event
        self._memory.append(log_event)

        if self._dir:
            self._dir.mkdir(parents=True, exist_ok=True)
            fname = f"{log_event.event_id}.json"
            with open(self._dir / fname, "w", encoding="utf-8") as fh:
                json.dump(event.to_dict(), fh, ensure_ascii=False, indent=2)

        return log_event

    def write_typed(self, event: BaseEvent) -> LogEvent:
        return self.write(event)

    def count(self) -> int:
        return len(self._memory)

    def by_type(self, event_type: str) -> list[LogEvent]:
        return [e for e in self._memory if e.event_type.value == event_type]

    def by_project(self, project: str) -> list[LogEvent]:
        return [e for e in self._memory if e.project == project]

    def last(self) -> Optional[LogEvent]:
        return self._memory[-1] if self._memory else None

    def clear(self):
        self._memory.clear()
