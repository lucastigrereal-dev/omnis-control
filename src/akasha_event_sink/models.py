import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class SinkStatus(str, Enum):
    QUEUED = "QUEUED"
    WRITTEN = "WRITTEN"
    FAILED = "FAILED"
    FLUSHED = "FLUSHED"


@dataclass
class SinkConfig:
    target_dir: str = ""
    max_file_size: int = 1048576
    batch_size: int = 100
    dry_run: bool = True


@dataclass
class SinkEvent:
    event_id: str = field(default_factory=lambda: _new_id("ske"))
    event_type: str = ""
    source: str = ""
    payload: dict = field(default_factory=dict)
    status: SinkStatus = SinkStatus.QUEUED
    created_at: str = field(default_factory=_now_iso)
    written_at: str = ""

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "payload": self.payload,
            "status": self.status.value,
            "created_at": self.created_at,
            "written_at": self.written_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SinkEvent":
        return cls(
            event_id=data.get("event_id", ""),
            event_type=data.get("event_type", ""),
            source=data.get("source", ""),
            payload=data.get("payload", {}),
            status=SinkStatus(data.get("status", "QUEUED")),
            created_at=data.get("created_at", ""),
            written_at=data.get("written_at", ""),
        )
