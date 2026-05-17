"""W161 — KRATOS Bridge models: structured cockpit payloads."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


class PayloadType(str, Enum):
    STATUS_UPDATE = "STATUS_UPDATE"
    MISSION_RESULT = "MISSION_RESULT"
    ALERT = "ALERT"
    METRIC = "METRIC"
    WAVE_PROGRESS = "WAVE_PROGRESS"
    COMMAND_ECHO = "COMMAND_ECHO"
    ERROR = "ERROR"


class PayloadPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PayloadStatus(str, Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    DROPPED = "DROPPED"


@dataclass
class KratosPayload:
    payload_id: str = field(default_factory=lambda: _new_id("kpl"))
    payload_type: PayloadType = PayloadType.STATUS_UPDATE
    priority: PayloadPriority = PayloadPriority.NORMAL
    source_module: str = "omnis"
    target_view: str = ""          # cockpit view/route to update
    title: str = ""
    body: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    dry_run: bool = True
    status: PayloadStatus = PayloadStatus.QUEUED
    created_at: str = field(default_factory=_now_iso)
    sent_at: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "payload_id": self.payload_id,
            "payload_type": self.payload_type.value,
            "priority": self.priority.value,
            "source_module": self.source_module,
            "target_view": self.target_view,
            "title": self.title,
            "body": self.body,
            "tags": self.tags,
            "dry_run": self.dry_run,
            "status": self.status.value,
            "created_at": self.created_at,
            "sent_at": self.sent_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KratosPayload":
        return cls(
            payload_id=data.get("payload_id", _new_id("kpl")),
            payload_type=PayloadType(data.get("payload_type", "STATUS_UPDATE")),
            priority=PayloadPriority(data.get("priority", "NORMAL")),
            source_module=data.get("source_module", "omnis"),
            target_view=data.get("target_view", ""),
            title=data.get("title", ""),
            body=data.get("body", {}),
            tags=data.get("tags", []),
            dry_run=data.get("dry_run", True),
            status=PayloadStatus(data.get("status", "QUEUED")),
            created_at=data.get("created_at", _now_iso()),
            sent_at=data.get("sent_at", ""),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def status_update(cls, title: str, body: dict, view: str = "dashboard") -> "KratosPayload":
        return cls(payload_type=PayloadType.STATUS_UPDATE, title=title, body=body, target_view=view)

    @classmethod
    def alert(cls, title: str, message: str, priority: PayloadPriority = PayloadPriority.HIGH) -> "KratosPayload":
        return cls(payload_type=PayloadType.ALERT, priority=priority, title=title, body={"message": message})

    @classmethod
    def metric(cls, name: str, value: float, unit: str = "") -> "KratosPayload":
        return cls(payload_type=PayloadType.METRIC, title=name, body={"value": value, "unit": unit})

    @classmethod
    def wave_progress(cls, wave: str, complete: int, total: int) -> "KratosPayload":
        return cls(
            payload_type=PayloadType.WAVE_PROGRESS,
            title=f"{wave} progress",
            body={"wave": wave, "complete": complete, "total": total, "pct": round(complete / total * 100, 1)},
            target_view="progress",
        )
