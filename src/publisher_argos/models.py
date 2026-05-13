"""P8 Publisher / ARGOS Export — Deterministic models (dry-run only, stdlib-only)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class PublishChannel(str, Enum):
    INSTAGRAM_FEED = "instagram_feed"
    INSTAGRAM_STORY = "instagram_story"
    INSTAGRAM_REEL = "instagram_reel"


class ExportStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    QUEUED = "queued"
    EXPORTED = "exported"
    BLOCKED = "blocked"


class ReadinessVerdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    PENDING_APPROVAL = "pending_approval"


@dataclass
class PublishTarget:
    """Target Instagram page for publishing."""

    handle: str = ""
    profile: str = ""
    channel: PublishChannel = PublishChannel.INSTAGRAM_FEED
    followers: int = 0
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "handle": self.handle,
            "profile": self.profile,
            "channel": self.channel.value,
            "followers": self.followers,
            "label": self.label,
        }


@dataclass
class ArgosExportItem:
    """A single content item prepared for ARGOS export (never publishes)."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    target: PublishTarget = field(default_factory=PublishTarget)
    caption: str = ""
    media_url: str = ""
    media_type: str = "IMAGE"
    tags: list[str] = field(default_factory=list)
    schedule_iso: Optional[str] = None
    status: ExportStatus = ExportStatus.DRAFT
    approval_required: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""

    def mark_ready(self) -> None:
        self.status = ExportStatus.READY

    def mark_queued(self) -> None:
        self.status = ExportStatus.QUEUED

    def mark_exported(self) -> None:
        self.status = ExportStatus.EXPORTED

    def mark_blocked(self, reason: str = "") -> None:
        self.status = ExportStatus.BLOCKED
        if reason:
            self.notes = reason

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "target": self.target.to_dict(),
            "caption": self.caption,
            "media_url": self.media_url,
            "media_type": self.media_type,
            "tags": self.tags,
            "schedule_iso": self.schedule_iso,
            "status": self.status.value,
            "approval_required": self.approval_required,
            "created_at": self.created_at.isoformat(),
            "notes": self.notes,
        }


@dataclass
class PublishReadinessCheck:
    """Validation result for a single content item before publishing."""

    item_id: str = ""
    verdict: ReadinessVerdict = ReadinessVerdict.PENDING_APPROVAL
    checks: list[dict] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    blocked: int = 0
    reason: str = ""
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_ready(self) -> bool:
        return self.verdict == ReadinessVerdict.PASS and self.failed == 0

    @property
    def requires_approval(self) -> bool:
        return self.verdict == ReadinessVerdict.PENDING_APPROVAL or not self.is_ready

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "verdict": self.verdict.value,
            "checks": self.checks,
            "passed": self.passed,
            "failed": self.failed,
            "blocked": self.blocked,
            "reason": self.reason,
            "checked_at": self.checked_at.isoformat(),
            "is_ready": self.is_ready,
            "requires_approval": self.requires_approval,
        }


@dataclass
class PublishQueuePlan:
    """A queue of ArgosExportItems waiting to be exported to ARGOS."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    items: list[ArgosExportItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    label: str = ""
    dry_run: bool = True

    @property
    def pending(self) -> list[ArgosExportItem]:
        return [i for i in self.items if i.status == ExportStatus.DRAFT]

    @property
    def ready(self) -> list[ArgosExportItem]:
        return [i for i in self.items if i.status == ExportStatus.READY]

    @property
    def queued(self) -> list[ArgosExportItem]:
        return [i for i in self.items if i.status == ExportStatus.QUEUED]

    @property
    def blocked(self) -> list[ArgosExportItem]:
        return [i for i in self.items if i.status == ExportStatus.BLOCKED]

    def add(self, item: ArgosExportItem) -> None:
        self.items.append(item)

    def find_by_handle(self, handle: str) -> list[ArgosExportItem]:
        return [i for i in self.items if i.target.handle == handle]

    def find_by_channel(self, channel: PublishChannel) -> list[ArgosExportItem]:
        return [i for i in self.items if i.target.channel == channel]

    def to_dict(self) -> dict:
        return {
            "queue_id": self.id,
            "label": self.label,
            "dry_run": self.dry_run,
            "created_at": self.created_at.isoformat(),
            "item_count": len(self.items),
            "pending": len(self.pending),
            "ready": len(self.ready),
            "queued": len(self.queued),
            "blocked": len(self.blocked),
            "items": [i.to_dict() for i in self.items],
        }


@dataclass
class ArgosExportPackage:
    """A full ARGOS export package (spec/string/plan only — never writes to disk)."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    queue_plan: PublishQueuePlan = field(default_factory=PublishQueuePlan)
    readiness_checks: list[PublishReadinessCheck] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    label: str = ""
    dry_run: bool = True
    approval_required: bool = True

    @property
    def all_ready(self) -> bool:
        if not self.readiness_checks:
            return False
        return all(c.is_ready for c in self.readiness_checks)

    @property
    def item_count(self) -> int:
        return len(self.queue_plan.items)

    @property
    def blocked_items(self) -> list[ArgosExportItem]:
        return self.queue_plan.blocked

    def to_dict(self) -> dict:
        return {
            "package_id": self.id,
            "label": self.label,
            "dry_run": self.dry_run,
            "approval_required": self.approval_required,
            "generated_at": self.generated_at.isoformat(),
            "all_ready": self.all_ready,
            "item_count": self.item_count,
            "blocked_count": len(self.blocked_items),
            "queue_plan": self.queue_plan.to_dict(),
            "readiness_checks": [c.to_dict() for c in self.readiness_checks],
        }


@dataclass
class PublisherHandoff:
    """Handoff record from Publisher module to ARGOS (dry-run only)."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    package: ArgosExportPackage = field(default_factory=ArgosExportPackage)
    source_module: str = "publisher_argos"
    target_system: str = "ARGOS"
    approval_required: bool = True
    approved_by: Optional[str] = None
    handed_off_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dry_run: bool = True
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "handoff_id": self.id,
            "source_module": self.source_module,
            "target_system": self.target_system,
            "approval_required": self.approval_required,
            "approved_by": self.approved_by,
            "handed_off_at": self.handed_off_at.isoformat(),
            "dry_run": self.dry_run,
            "notes": self.notes,
            "package": self.package.to_dict(),
        }
