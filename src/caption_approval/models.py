"""Modelos de dados do Caption Draft + Approval Gate."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


class DraftStatus:
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISED = "revised"
    STALE = "stale"


class ApprovalAction:
    CREATED = "created"
    UPDATED = "updated"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


# Placeholders que bloqueiam aprovação
BLOCKED_PLACEHOLDERS = [
    "[HOOK A REVISAR]",
    "[CORPO DA LEGENDA A REVISAR]",
    "[CTA A DEFINIR]",
]

# Placeholders que geram warning (não bloqueiam)
WARN_PLACEHOLDERS = [
    "[LOCAL]",
    [f"[NOME_DO_HOTEL]"],
    "[LINK]",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class CaptionDraft:
    draft_id: str
    queue_id: str
    account_handle: str
    caption_text: str = ""
    hashtags: list[str] = field(default_factory=list)
    cta: str = ""
    status: str = DraftStatus.DRAFT
    version: int = 1
    objective: str = "alcance"
    format: str = "unknown"
    notes: str = ""
    rejection_reason: Optional[str] = None
    asset_id: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "CaptionDraft":
        return cls(**data)


@dataclass
class CaptionTemplate:
    template_id: str
    name: str
    objective: str
    format: Optional[str]  # None = vale para qualquer formato
    hook_template: str
    body_template: str
    cta_template: str
    hashtag_suggestions: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CaptionTemplate":
        return cls(**data)


@dataclass
class ApprovalLogEntry:
    event_id: str
    draft_id: str
    queue_id: str
    action: str
    actor: str = "local_user"
    reason: Optional[str] = None
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    metadata: Optional[dict] = None
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "ApprovalLogEntry":
        return cls(**data)
