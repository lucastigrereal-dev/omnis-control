"""P1 Content Queue & Scheduling — Deterministic models (dry-run only)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional


class ContentStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    ASSIGNED = "assigned"
    CONFLICT = "conflict"
    EXPORTED = "exported"


class PublishingChannel(str, Enum):
    INSTAGRAM_FEED = "instagram_feed"
    INSTAGRAM_STORY = "instagram_story"
    INSTAGRAM_REEL = "instagram_reel"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"


class SlotPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ContentItemDraft:
    """A single content draft ready for scheduling (never published automatically)."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    caption: str = ""
    channel: PublishingChannel = PublishingChannel.INSTAGRAM_FEED
    status: ContentStatus = ContentStatus.DRAFT
    priority: SlotPriority = SlotPriority.NORMAL
    tags: list[str] = field(default_factory=list)
    estimated_duration_min: int = 0
    target_slot_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""

    def mark_ready(self) -> None:
        self.status = ContentStatus.READY

    def assign_to(self, slot_id: str) -> None:
        self.target_slot_id = slot_id
        self.status = ContentStatus.ASSIGNED

    def flag_conflict(self) -> None:
        self.status = ContentStatus.CONFLICT


@dataclass
class ContentSlot:
    """A schedulable time window on a specific channel."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    channel: PublishingChannel = PublishingChannel.INSTAGRAM_FEED
    opens_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_min: int = 60
    priority: SlotPriority = SlotPriority.NORMAL
    assigned_item_id: Optional[str] = None
    locked: bool = False
    label: str = ""

    @property
    def closes_at(self) -> datetime:
        return self.opens_at + timedelta(minutes=self.duration_min)

    def is_available(self) -> bool:
        return not self.locked and self.assigned_item_id is None

    def assign(self, item_id: str) -> None:
        if not self.is_available():
            raise ValueError(f"Slot {self.id} is not available")
        self.assigned_item_id = item_id

    def release(self) -> None:
        self.assigned_item_id = None


@dataclass
class ScheduleWindow:
    """A bounded scheduling window with guard-rails."""

    start: datetime
    end: datetime
    allowed_channels: list[PublishingChannel] = field(default_factory=list)
    max_slots_per_day: int = 5
    min_gap_minutes: int = 30
    label: str = ""

    def contains(self, dt: datetime) -> bool:
        return self.start <= dt <= self.end

    def duration_days(self) -> int:
        return (self.end - self.start).days


@dataclass
class CalendarPlan:
    """A calendar plan: collection of slots within a schedule window."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    window: ScheduleWindow = field(default_factory=lambda: ScheduleWindow(
        start=datetime.now(timezone.utc), end=datetime.now(timezone.utc) + timedelta(days=7),
    ))
    slots: list[ContentSlot] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    label: str = ""

    @property
    def slot_count(self) -> int:
        return len(self.slots)

    @property
    def free_slots(self) -> list[ContentSlot]:
        return [s for s in self.slots if s.is_available()]

    @property
    def assigned_slots(self) -> list[ContentSlot]:
        return [s for s in self.slots if s.assigned_item_id is not None]

    def find_conflicts(self) -> list[tuple[ContentSlot, ContentSlot]]:
        conflicts: list[tuple[ContentSlot, ContentSlot]] = []
        for i, a in enumerate(self.slots):
            for b in self.slots[i + 1:]:
                if a.channel == b.channel and a.opens_at == b.opens_at:
                    conflicts.append((a, b))
        return conflicts


@dataclass
class QueuePlan:
    """A queue of content draft items waiting to be assigned to slots."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    items: list[ContentItemDraft] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    label: str = ""

    @property
    def pending(self) -> list[ContentItemDraft]:
        return [i for i in self.items if i.status in (ContentStatus.DRAFT, ContentStatus.READY)]

    @property
    def assigned(self) -> list[ContentItemDraft]:
        return [i for i in self.items if i.status == ContentStatus.ASSIGNED]

    @property
    def conflicts(self) -> list[ContentItemDraft]:
        return [i for i in self.items if i.status == ContentStatus.CONFLICT]

    def add(self, item: ContentItemDraft) -> None:
        self.items.append(item)

    def find_by_channel(self, channel: PublishingChannel) -> list[ContentItemDraft]:
        return [i for i in self.items if i.channel == channel]


@dataclass
class SchedulingDecision:
    """Outcome of assigning ONE item to ONE slot (dry-run — never publishes)."""

    item_id: str = ""
    slot_id: str = ""
    channel: PublishingChannel = PublishingChannel.INSTAGRAM_FEED
    scheduled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = False
    reason: str = ""
    dry_run: bool = True
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "slot_id": self.slot_id,
            "channel": self.channel.value,
            "scheduled_at": self.scheduled_at.isoformat(),
            "success": self.success,
            "reason": self.reason,
            "dry_run": self.dry_run,
            "decided_at": self.decided_at.isoformat(),
        }
