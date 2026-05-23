"""Modelos de dados da Content Queue."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


class QueueStatus:
    PLANNED = "planned"
    NEEDS_ASSET = "needs_asset"
    NEEDS_CAPTION = "needs_caption"
    CAPTION_READY = "caption_ready"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    SKIPPED = "skipped"


class QueueObjective:
    REACH = "alcance"
    AUTHORITY = "autoridade"
    CONVERSION = "conversao"
    RELATIONSHIP = "relacionamento"
    TEST = "teste"


class QueueFormat:
    REELS = "reels"
    STORIES = "stories"
    FEED = "feed"
    CAROUSEL = "carousel"
    UNKNOWN = "unknown"


class Priority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class QueueItem:
    queue_id: str
    account_handle: str
    date: str          # YYYY-MM-DD
    time: str          # HH:MM
    timezone: str = "America/Sao_Paulo"
    asset_id: str | None = None
    format: str = QueueFormat.UNKNOWN
    objective: str = QueueObjective.REACH
    status: str = QueueStatus.PLANNED
    priority: str = Priority.MEDIUM
    notes: str | None = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "QueueItem":
        return cls(**data)

    @property
    def datetime_iso(self) -> str:
        return f"{self.date}T{self.time}:00-03:00"

    @property
    def is_empty_slot(self) -> bool:
        return self.asset_id is None
