"""P1 Content Scheduler Planner — deterministic scheduling engine (dry-run only)."""

from __future__ import annotations

import csv
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from io import StringIO
from typing import Optional

from src.content_scheduler.models import (
    CalendarPlan,
    ContentItemDraft,
    ContentSlot,
    ContentStatus,
    PublishingChannel,
    QueuePlan,
    ScheduleWindow,
    SchedulingDecision,
    SlotPriority,
)


@dataclass
class ContentSchedulerPlanner:
    """Deterministic content scheduler — plans slots and assigns items.

    NEVER publishes, NEVER calls external APIs.
    All operations are pure modeling / dry-run.
    """

    default_channels: list[PublishingChannel] = field(default_factory=lambda: [
        PublishingChannel.INSTAGRAM_FEED,
        PublishingChannel.INSTAGRAM_STORY,
        PublishingChannel.INSTAGRAM_REEL,
    ])
    max_slots_per_day: int = 5
    default_slot_duration_min: int = 60
    min_gap_minutes: int = 30

    # ── calendar ──────────────────────────────────────────────

    def build_calendar_plan(
        self,
        start: datetime,
        days: int = 7,
        channels: Optional[list[PublishingChannel]] = None,
        label: str = "",
    ) -> CalendarPlan:
        """Build a CalendarPlan with evenly distributed slots across days."""
        if days < 1:
            raise ValueError("days must be >= 1")
        channels = channels or self.default_channels
        end = start + timedelta(days=days)
        window = ScheduleWindow(
            start=start,
            end=end,
            allowed_channels=list(channels),
            max_slots_per_day=self.max_slots_per_day,
            min_gap_minutes=self.min_gap_minutes,
        )
        slots: list[ContentSlot] = []
        for day_offset in range(days):
            day = start + timedelta(days=day_offset)
            for ch in channels:
                for slot_idx in range(self.max_slots_per_day):
                    hour = 8 + slot_idx * 3  # 08:00, 11:00, 14:00, 17:00, 20:00
                    opens = day.replace(hour=hour % 24, minute=0, second=0, microsecond=0)
                    slots.append(ContentSlot(
                        channel=ch,
                        opens_at=opens,
                        duration_min=self.default_slot_duration_min,
                        label=f"{ch.value} @ {opens.isoformat()}",
                    ))
        plan = CalendarPlan(window=window, slots=slots, label=label)
        return plan

    # ── assignment ────────────────────────────────────────────

    def assign_content_slots(
        self,
        plan: CalendarPlan,
        queue: QueuePlan,
    ) -> list[SchedulingDecision]:
        """Greedy assignment of ready items to free slots. Returns decisions."""
        decisions: list[SchedulingDecision] = []
        free = [s for s in plan.slots if s.is_available()]
        pending = [i for i in queue.items if i.status in (ContentStatus.DRAFT, ContentStatus.READY)]

        for item in pending:
            matching = [s for s in free if s.channel == item.channel and s.is_available()]
            if not matching:
                decisions.append(SchedulingDecision(
                    item_id=item.id,
                    slot_id="",
                    channel=item.channel,
                    success=False,
                    reason="No free slot for channel",
                ))
                continue
            slot = matching[0]
            slot.assign(item.id)
            item.assign_to(slot.id)
            free.remove(slot)
            decisions.append(SchedulingDecision(
                item_id=item.id,
                slot_id=slot.id,
                channel=slot.channel,
                scheduled_at=slot.opens_at,
                success=True,
                reason="Assigned",
            ))

        return decisions

    # ── validation ────────────────────────────────────────────

    @staticmethod
    def validate_schedule_window(window: ScheduleWindow) -> list[str]:
        """Return list of issues with the window (empty = valid)."""
        issues: list[str] = []
        if window.start >= window.end:
            issues.append("start must be before end")
        if window.max_slots_per_day < 1:
            issues.append("max_slots_per_day must be >= 1")
        if window.min_gap_minutes < 0:
            issues.append("min_gap_minutes must be >= 0")
        if not window.allowed_channels:
            issues.append("at least one channel required")
        return issues

    @staticmethod
    def detect_schedule_conflicts(plan: CalendarPlan) -> list[dict]:
        """Detect overlapping or duplicate slot assignments."""
        conflicts: list[dict] = []
        slots = plan.slots
        for i, a in enumerate(slots):
            for b in slots[i + 1:]:
                if a.channel != b.channel:
                    continue
                a_end = a.closes_at
                b_end = b.closes_at
                if a.opens_at < b_end and b.opens_at < a_end:
                    conflicts.append({
                        "slot_a": a.id,
                        "slot_b": b.id,
                        "channel": a.channel.value,
                        "type": "overlap",
                        "a_opens": a.opens_at.isoformat(),
                        "b_opens": b.opens_at.isoformat(),
                    })
                if (a.assigned_item_id and b.assigned_item_id
                        and a.assigned_item_id == b.assigned_item_id):
                    conflicts.append({
                        "slot_a": a.id,
                        "slot_b": b.id,
                        "channel": a.channel.value,
                        "type": "duplicate_assignment",
                        "item_id": a.assigned_item_id,
                    })
        return conflicts

    # ── exports ───────────────────────────────────────────────

    @staticmethod
    def export_calendar_csv(plan: CalendarPlan) -> str:
        """Export CalendarPlan slots as CSV string."""
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(["slot_id", "channel", "opens_at", "duration_min",
                          "assigned_item_id", "locked", "label"])
        for s in plan.slots:
            writer.writerow([
                s.id, s.channel.value, s.opens_at.isoformat(),
                s.duration_min, s.assigned_item_id or "", s.locked, s.label,
            ])
        return buf.getvalue()

    @staticmethod
    def export_queue_json(queue: QueuePlan, indent: int = 2) -> str:
        """Export QueuePlan items as JSON string."""
        items = []
        for item in queue.items:
            items.append({
                "id": item.id,
                "title": item.title,
                "caption": item.caption,
                "channel": item.channel.value,
                "status": item.status.value,
                "priority": item.priority.value,
                "tags": item.tags,
                "target_slot_id": item.target_slot_id,
                "created_at": item.created_at.isoformat(),
                "notes": item.notes,
            })
        return json.dumps({
            "queue_id": queue.id,
            "label": queue.label,
            "created_at": queue.created_at.isoformat(),
            "items": items,
        }, indent=indent, ensure_ascii=False)
