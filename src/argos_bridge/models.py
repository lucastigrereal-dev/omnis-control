"""Modelos de dados do Argos Draft Bridge."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


class ArgosStatus:
    LOCAL_DRAFT = "local_draft"
    READY_FOR_ARGOS = "ready_for_argos"
    EXPORTED = "exported"
    BLOCKED = "blocked"


class WarnCode:
    """Códigos controlados de warning."""
    NO_ASSET_ATTACHED = "NO_ASSET_ATTACHED"
    CAPTION_MODIFIED_AFTER_EXPORT = "CAPTION_MODIFIED_AFTER_EXPORT"
    QUEUE_ITEM_MISSING = "QUEUE_ITEM_MISSING"
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    PLACEHOLDER_DETECTED = "PLACEHOLDER_DETECTED"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ArgosDraft:
    draft_id: str
    queue_id: str
    caption_draft_id: str
    account_handle: str
    platform: str = "instagram"
    post_type: str = "feed"
    caption_text: str = ""
    hashtags: list[str] = field(default_factory=list)
    cta: str = ""
    asset_id: str | None = None
    media_path: str | None = None
    scheduled_date: str | None = None
    scheduled_time: str | None = None
    status: str = ArgosStatus.LOCAL_DRAFT
    warnings: list[str] = field(default_factory=list)
    notes: str | None = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ArgosDraft":
        return cls(**data)
