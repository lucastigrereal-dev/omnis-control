"""Tests for P1 Content Scheduler models."""

from datetime import datetime, timedelta

import pytest

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


class TestContentItemDraft:
    def test_defaults(self):
        item = ContentItemDraft()
        assert item.status == ContentStatus.DRAFT
        assert item.channel == PublishingChannel.INSTAGRAM_FEED
        assert item.priority == SlotPriority.NORMAL
        assert item.id

    def test_mark_ready(self):
        item = ContentItemDraft()
        item.mark_ready()
        assert item.status == ContentStatus.READY

    def test_assign_to(self):
        item = ContentItemDraft()
        item.assign_to("slot-1")
        assert item.status == ContentStatus.ASSIGNED
        assert item.target_slot_id == "slot-1"

    def test_flag_conflict(self):
        item = ContentItemDraft()
        item.flag_conflict()
        assert item.status == ContentStatus.CONFLICT

    def test_custom_values(self):
        item = ContentItemDraft(
            title="Test Post",
            caption="Hello world",
            channel=PublishingChannel.INSTAGRAM_REEL,
            tags=["travel", "family"],
        )
        assert item.title == "Test Post"
        assert item.caption == "Hello world"
        assert item.channel == PublishingChannel.INSTAGRAM_REEL
        assert item.tags == ["travel", "family"]


class TestContentSlot:
    def test_defaults(self):
        slot = ContentSlot()
        assert slot.channel == PublishingChannel.INSTAGRAM_FEED
        assert slot.duration_min == 60
        assert not slot.locked
        assert slot.is_available()

    def test_closes_at(self):
        now = datetime(2026, 5, 12, 10, 0, 0)
        slot = ContentSlot(opens_at=now, duration_min=30)
        assert slot.closes_at == datetime(2026, 5, 12, 10, 30, 0)

    def test_assign_and_release(self):
        slot = ContentSlot()
        assert slot.is_available()
        slot.assign("item-1")
        assert not slot.is_available()
        assert slot.assigned_item_id == "item-1"
        slot.release()
        assert slot.is_available()
        assert slot.assigned_item_id is None

    def test_assign_unavailable_raises(self):
        slot = ContentSlot(locked=True)
        with pytest.raises(ValueError, match="not available"):
            slot.assign("item-1")

    def test_assign_already_taken_raises(self):
        slot = ContentSlot()
        slot.assign("item-1")
        with pytest.raises(ValueError, match="not available"):
            slot.assign("item-2")


class TestScheduleWindow:
    def test_valid_window(self):
        w = ScheduleWindow(
            start=datetime(2026, 5, 12),
            end=datetime(2026, 5, 19),
        )
        assert w.duration_days() == 7

    def test_invalid_window_constructible(self):
        """Invalid windows can be constructed — validation is in planner."""
        w = ScheduleWindow(
            start=datetime(2026, 5, 19),
            end=datetime(2026, 5, 12),
        )
        assert w.duration_days() < 0

    def test_contains(self):
        w = ScheduleWindow(
            start=datetime(2026, 5, 12),
            end=datetime(2026, 5, 19),
        )
        assert w.contains(datetime(2026, 5, 15))
        assert not w.contains(datetime(2026, 5, 10))
        assert not w.contains(datetime(2026, 5, 20))


class TestCalendarPlan:
    def test_empty_plan(self):
        plan = CalendarPlan()
        assert plan.slot_count == 0
        assert plan.free_slots == []
        assert plan.assigned_slots == []

    def test_slot_classification(self):
        now = datetime.utcnow()
        free_slot = ContentSlot(opens_at=now)
        taken_slot = ContentSlot(opens_at=now)
        taken_slot.assign("item-1")
        plan = CalendarPlan(slots=[free_slot, taken_slot])
        assert len(plan.free_slots) == 1
        assert len(plan.assigned_slots) == 1

    def test_find_conflicts_same_time_channel(self):
        now = datetime.utcnow()
        s1 = ContentSlot(opens_at=now, channel=PublishingChannel.INSTAGRAM_FEED)
        s2 = ContentSlot(opens_at=now, channel=PublishingChannel.INSTAGRAM_FEED)
        plan = CalendarPlan(slots=[s1, s2])
        conflicts = plan.find_conflicts()
        assert len(conflicts) == 1


class TestQueuePlan:
    def test_empty_queue(self):
        qp = QueuePlan()
        assert qp.pending == []
        assert qp.assigned == []

    def test_add_and_filter(self):
        qp = QueuePlan()
        item = ContentItemDraft(channel=PublishingChannel.INSTAGRAM_REEL)
        qp.add(item)
        assert len(qp.items) == 1
        assert len(qp.pending) == 1
        assert qp.find_by_channel(PublishingChannel.INSTAGRAM_REEL) == [item]
        assert qp.find_by_channel(PublishingChannel.YOUTUBE) == []

    def test_status_filters(self):
        qp = QueuePlan()
        pending = ContentItemDraft()
        assigned = ContentItemDraft()
        assigned.assign_to("slot-x")
        conflict = ContentItemDraft()
        conflict.flag_conflict()
        qp.add(pending)
        qp.add(assigned)
        qp.add(conflict)
        assert len(qp.pending) == 1
        assert len(qp.assigned) == 1
        assert len(qp.conflicts) == 1


class TestSchedulingDecision:
    def test_success_decision(self):
        d = SchedulingDecision(
            item_id="i1", slot_id="s1",
            channel=PublishingChannel.INSTAGRAM_FEED,
            success=True, reason="Assigned",
        )
        assert d.dry_run is True
        assert d.success is True
        dct = d.to_dict()
        assert dct["item_id"] == "i1"
        assert dct["dry_run"] is True

    def test_failure_decision(self):
        d = SchedulingDecision(
            item_id="i2", success=False,
            reason="No free slot",
        )
        assert d.success is False
        assert d.dry_run is True
