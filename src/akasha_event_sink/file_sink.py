import json
from pathlib import Path
from datetime import datetime, timezone

from src.akasha_event_sink.models import SinkEvent, SinkStatus, _now_iso
from src.akasha_event_sink.errors import SinkWriteError


class FileSinkWriter:
    def __init__(self, target_dir: str, dry_run: bool = True):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self._buffer: list[SinkEvent] = []

    def buffer(self, event: SinkEvent) -> None:
        self._buffer.append(event)

    def flush(self) -> list[SinkEvent]:
        flushed = []
        for event in self._buffer:
            if self.dry_run:
                event.status = SinkStatus.FLUSHED
                flushed.append(event)
            else:
                self.target_dir.mkdir(parents=True, exist_ok=True)
                filepath = self.target_dir / f"{event.event_id}.json"
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(event.to_dict(), f, indent=2)
                event.status = SinkStatus.WRITTEN
                event.written_at = _now_iso()
                flushed.append(event)
        self._buffer.clear()
        return flushed

    @property
    def pending_count(self) -> int:
        return len(self._buffer)
