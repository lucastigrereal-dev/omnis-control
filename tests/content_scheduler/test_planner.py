"""Tests for P1 Content Scheduler Planner."""

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
    SlotPriority,
)
from src.content_scheduler.planner import ContentSchedulerPlanner


@pytest.fixture
def planner():
    return ContentSchedulerPlanner()


@pytest.fixture
def sample_start():
    return datetime(2026, 5, 18, 0, 0, 0)


class TestBuildCalendarPlan:
    def test_build_default(self, planner, sample_start):
        plan = planner.build_calendar_plan(start=sample_start)
        assert isinstance(plan, CalendarPlan)
        assert plan.slot_count == 7 * 3 * 5  # days * channels * slots_per_day
        assert plan.window.duration_days() == 7
        assert all(s.is_available() for s in plan.slots)

    def test_build_single_day(self, planner, sample_start):
        plan = planner.build_calendar_plan(start=sample_start, days=1)
        assert plan.slot_count == 1 * 3 * 5  # 15

    def test_build_custom_channels(self, planner, sample_start):
        plan = planner.build_calendar_plan(
            start=sample_start,
            days=1,
            channels=[PublishingChannel.INSTAGRAM_FEED],
        )
        assert plan.slot_count == 1 * 1 * 5  # 5
        assert all(s.channel == PublishingChannel.INSTAGRAM_FEED for s in plan.slots)

    def test_build_days_validation(self, planner, sample_start):
        with pytest.raises(ValueError, match="days must be >= 1"):
            planner.build_calendar_plan(start=sample_start, days=0)

    def test_build_slot_hours(self, planner, sample_start):
        plan = planner.build_calendar_plan(start=sample_start, days=1,
                                           channels=[PublishingChannel.INSTAGRAM_FEED])
        expected_hours = [8, 11, 14, 17, 20]
        actual_hours = [s.opens_at.hour for s in plan.slots]
        assert actual_hours == expected_hours

    def test_build_with_label(self, planner, sample_start):
        plan = planner.build_calendar_plan(start=sample_start, days=1, label="Q3 Campaign")
        assert plan.label == "Q3 Campaign"


class TestAssignContentSlots:
    def test_assign_single_item(self, planner, sample_start):
        plan = planner.build_calendar_plan(start=sample_start, days=1)
        queue = QueuePlan()
        item = ContentItemDraft(channel=PublishingChannel.INSTAGRAM_FEED)
        item.mark_ready()
        queue.add(item)

        decisions = planner.assign_content_slots(plan, queue)
        assert len(decisions) == 1
        assert decisions[0].success is True
        assert decisions[0].item_id == item.id
        assert decisions[0].dry_run is True
        assert item.status == ContentStatus.ASSIGNED

    def test_assign_no_free_slot(self, planner, sample_start):
        plan = planner.build_calendar_plan(start=sample_start, days=1,
                                           channels=[PublishingChannel.YOUTUBE])
        queue = QueuePlan()
        item = ContentItemDraft(channel=PublishingChannel.INSTAGRAM_FEED)
        item.mark_ready()
        queue.add(item)

        decisions = planner.assign_content_slots(plan, queue)
        assert len(decisions) == 1
        assert decisions[0].success is False
        assert "No free slot" in decisions[0].reason

    def test_assign_multiple_items(self, planner, sample_start):
        plan = planner.build_calendar_plan(start=sample_start, days=1,
                                           channels=[PublishingChannel.INSTAGRAM_FEED])
        queue = QueuePlan()
        for _ in range(3):
            item = ContentItemDraft(channel=PublishingChannel.INSTAGRAM_FEED)
            item.mark_ready()
            queue.add(item)

        decisions = planner.assign_content_slots(plan, queue)
        assert len([d for d in decisions if d.success]) == 3
        assert queue.assigned == queue.items

    def test_assign_dry_run_never_publishes(self, planner, sample_start):
        """All decisions must be dry_run=True — never real publishing."""
        plan = planner.build_calendar_plan(start=sample_start, days=1)
        queue = QueuePlan()
        item = ContentItemDraft()
        item.mark_ready()
        queue.add(item)

        decisions = planner.assign_content_slots(plan, queue)
        assert all(d.dry_run for d in decisions)


class TestValidateScheduleWindow:
    def test_valid(self):
        w = ScheduleWindow(
            start=datetime(2026, 5, 12),
            end=datetime(2026, 5, 19),
            allowed_channels=[PublishingChannel.INSTAGRAM_FEED],
        )
        assert ContentSchedulerPlanner.validate_schedule_window(w) == []

    def test_invalid_start_end(self):
        w = ScheduleWindow(
            start=datetime(2026, 5, 19),
            end=datetime(2026, 5, 12),
            allowed_channels=[PublishingChannel.INSTAGRAM_FEED],
        )
        issues = ContentSchedulerPlanner.validate_schedule_window(w)
        assert any("start must be before end" in i for i in issues)

    def test_no_channels(self):
        w = ScheduleWindow(
            start=datetime(2026, 5, 12),
            end=datetime(2026, 5, 19),
            allowed_channels=[],
        )
        issues = ContentSchedulerPlanner.validate_schedule_window(w)
        assert any("channel" in i for i in issues)

    def test_invalid_max_slots(self):
        w = ScheduleWindow(
            start=datetime(2026, 5, 12),
            end=datetime(2026, 5, 19),
            allowed_channels=[PublishingChannel.INSTAGRAM_FEED],
            max_slots_per_day=0,
        )
        issues = ContentSchedulerPlanner.validate_schedule_window(w)
        assert any("max_slots_per_day" in i for i in issues)


class TestDetectScheduleConflicts:
    def test_no_conflicts(self, planner, sample_start):
        plan = planner.build_calendar_plan(start=sample_start, days=1)
        conflicts = ContentSchedulerPlanner.detect_schedule_conflicts(plan)
        assert conflicts == []

    def test_overlap_detected(self):
        now = datetime.utcnow()
        s1 = ContentSlot(opens_at=now, duration_min=30,
                         channel=PublishingChannel.INSTAGRAM_FEED)
        s2 = ContentSlot(opens_at=now + timedelta(minutes=15), duration_min=30,
                         channel=PublishingChannel.INSTAGRAM_FEED)
        plan = CalendarPlan(slots=[s1, s2])
        conflicts = ContentSchedulerPlanner.detect_schedule_conflicts(plan)
        assert len(conflicts) >= 1
        assert conflicts[0]["type"] == "overlap"

    def test_different_channels_no_overlap(self):
        now = datetime.utcnow()
        s1 = ContentSlot(opens_at=now, channel=PublishingChannel.INSTAGRAM_FEED)
        s2 = ContentSlot(opens_at=now, channel=PublishingChannel.INSTAGRAM_STORY)
        plan = CalendarPlan(slots=[s1, s2])
        conflicts = ContentSchedulerPlanner.detect_schedule_conflicts(plan)
        assert conflicts == []

    def test_duplicate_assignment(self):
        now = datetime.utcnow()
        s1 = ContentSlot(opens_at=now, channel=PublishingChannel.INSTAGRAM_FEED)
        s1.assign("item-x")
        s2 = ContentSlot(opens_at=now + timedelta(hours=3),
                         channel=PublishingChannel.INSTAGRAM_FEED)
        s2.assign("item-x")
        plan = CalendarPlan(slots=[s1, s2])
        conflicts = ContentSchedulerPlanner.detect_schedule_conflicts(plan)
        dupes = [c for c in conflicts if c["type"] == "duplicate_assignment"]
        assert len(dupes) == 1


class TestExports:
    def test_export_calendar_csv(self, planner, sample_start):
        plan = planner.build_calendar_plan(start=sample_start, days=1,
                                           channels=[PublishingChannel.INSTAGRAM_FEED])
        csv_str = ContentSchedulerPlanner.export_calendar_csv(plan)
        assert "slot_id" in csv_str
        assert "channel" in csv_str
        assert "opens_at" in csv_str
        lines = csv_str.strip().split("\n")
        assert len(lines) == 6  # header + 5 slots

    def test_export_queue_json(self):
        qp = QueuePlan(label="Test Queue")
        item = ContentItemDraft(title="Hello", channel=PublishingChannel.INSTAGRAM_FEED)
        qp.add(item)
        json_str = ContentSchedulerPlanner.export_queue_json(qp)
        data = __import__("json").loads(json_str)
        assert data["queue_id"] == qp.id
        assert data["label"] == "Test Queue"
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Hello"

    def test_export_queue_json_empty(self):
        qp = QueuePlan()
        json_str = ContentSchedulerPlanner.export_queue_json(qp)
        data = __import__("json").loads(json_str)
        assert data["items"] == []

    def test_export_csv_with_assigned_slots(self, planner, sample_start):
        plan = planner.build_calendar_plan(start=sample_start, days=1,
                                           channels=[PublishingChannel.INSTAGRAM_FEED])
        plan.slots[0].assign("item-abc")
        csv_str = ContentSchedulerPlanner.export_calendar_csv(plan)
        assert "item-abc" in csv_str


class TestPlannerConfiguration:
    def test_custom_max_slots(self):
        p = ContentSchedulerPlanner(max_slots_per_day=3)
        assert p.max_slots_per_day == 3

    def test_custom_channels(self):
        p = ContentSchedulerPlanner(default_channels=[PublishingChannel.YOUTUBE])
        assert p.default_channels == [PublishingChannel.YOUTUBE]
