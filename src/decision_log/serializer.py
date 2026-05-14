import json
from pathlib import Path
from typing import Optional

from src.decision_log.models import BaseEvent, LogEvent
from src.decision_log.events import EventFactory


class LogSerializer:

    @staticmethod
    def to_json(event: BaseEvent) -> str:
        return event.to_json()

    @staticmethod
    def from_json(data: str) -> BaseEvent:
        raw = json.loads(data)
        return EventFactory.from_raw(raw)

    @staticmethod
    def save(event: BaseEvent, filepath: str):
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(event.to_json(), encoding="utf-8")

    @staticmethod
    def load(filepath: str) -> BaseEvent:
        text = Path(filepath).read_text(encoding="utf-8")
        return LogSerializer.from_json(text)

    @staticmethod
    def save_all(events: list[BaseEvent], dirpath: str):
        d = Path(dirpath)
        d.mkdir(parents=True, exist_ok=True)
        for evt in events:
            fname = f"{evt.event.event_id}.json"
            (d / fname).write_text(evt.to_json(), encoding="utf-8")

    @staticmethod
    def load_all(dirpath: str) -> list[BaseEvent]:
        d = Path(dirpath)
        if not d.exists():
            return []
        events: list[BaseEvent] = []
        for fp in sorted(d.glob("*.json")):
            events.append(LogSerializer.load(str(fp)))
        return events
