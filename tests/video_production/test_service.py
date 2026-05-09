"""Tests for video_production service."""
import json
import pytest
from pathlib import Path

from src.video_production.models import PlanStatus, SlotStatus
from src.video_production.service import (
    create_plan,
    list_plans,
    get_plan,
    mark_slot,
    PlanNotFoundError,
    PlanValidationError,
)


@pytest.fixture
def tmp_log(tmp_path):
    return tmp_path / "video_production_plans.jsonl"


class TestCreatePlan:
    def test_creates_plan_with_correct_attributes(self, tmp_log):
        plan = create_plan("afamiliatigrereal", "reel", 5, days_ahead=10, log_path=tmp_log)
        assert plan.account_handle == "afamiliatigrereal"
        assert plan.format == "reel"
        assert plan.quantity == 5
        assert plan.days_ahead == 10
        assert plan.status == PlanStatus.ACTIVE

    def test_plan_id_has_vplan_prefix(self, tmp_log):
        plan = create_plan("lucastigrereal", "carousel", 3, log_path=tmp_log)
        assert plan.plan_id.startswith("vplan_")

    def test_strips_at_from_handle(self, tmp_log):
        plan = create_plan("@afamiliatigrereal", "reel", 3, log_path=tmp_log)
        assert plan.account_handle == "afamiliatigrereal"
        assert "@" not in plan.account_handle

    def test_generates_correct_slot_count(self, tmp_log):
        plan = create_plan("test_account", "reel", 7, days_ahead=21, log_path=tmp_log)
        assert len(plan.slots) == 7

    def test_slots_have_unique_ids(self, tmp_log):
        plan = create_plan("test_account", "carousel", 5, log_path=tmp_log)
        ids = [s.slot_id for s in plan.slots]
        assert len(set(ids)) == 5

    def test_slots_start_pending(self, tmp_log):
        plan = create_plan("test_account", "reel", 3, log_path=tmp_log)
        assert all(s.status == SlotStatus.PENDING for s in plan.slots)

    def test_persists_to_log(self, tmp_log):
        create_plan("test_account", "reel", 3, log_path=tmp_log)
        assert tmp_log.exists()
        lines = [l for l in tmp_log.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 1

    def test_invalid_format_raises(self, tmp_log):
        with pytest.raises(PlanValidationError, match="format"):
            create_plan("test_account", "tiktok", 3, log_path=tmp_log)

    def test_quantity_zero_raises(self, tmp_log):
        with pytest.raises(PlanValidationError, match="quantity"):
            create_plan("test_account", "reel", 0, log_path=tmp_log)

    def test_quantity_too_high_raises(self, tmp_log):
        with pytest.raises(PlanValidationError, match="quantity"):
            create_plan("test_account", "reel", 101, log_path=tmp_log)

    def test_no_network_calls(self, tmp_log):
        from unittest.mock import patch
        with patch("requests.post") as mock:
            create_plan("test_account", "reel", 2, log_path=tmp_log)
            mock.assert_not_called()


class TestListPlans:
    def test_returns_all_plans(self, tmp_log):
        create_plan("acc1", "reel", 3, log_path=tmp_log)
        create_plan("acc2", "carousel", 2, log_path=tmp_log)
        plans = list_plans(log_path=tmp_log)
        assert len(plans) == 2

    def test_filters_by_account(self, tmp_log):
        create_plan("acc1", "reel", 3, log_path=tmp_log)
        create_plan("acc2", "carousel", 2, log_path=tmp_log)
        plans = list_plans(account_handle="acc1", log_path=tmp_log)
        assert len(plans) == 1
        assert plans[0].account_handle == "acc1"

    def test_returns_empty_when_no_file(self, tmp_log):
        assert list_plans(log_path=tmp_log) == []


class TestGetPlan:
    def test_returns_plan_by_full_id(self, tmp_log):
        plan = create_plan("acc1", "reel", 3, log_path=tmp_log)
        found = get_plan(plan.plan_id, log_path=tmp_log)
        assert found.plan_id == plan.plan_id

    def test_returns_plan_by_prefix(self, tmp_log):
        plan = create_plan("acc1", "reel", 3, log_path=tmp_log)
        found = get_plan(plan.plan_id[:10], log_path=tmp_log)
        assert found.plan_id == plan.plan_id

    def test_raises_when_not_found(self, tmp_log):
        with pytest.raises(PlanNotFoundError):
            get_plan("nonexistent_plan", log_path=tmp_log)


class TestMarkSlot:
    def test_marks_slot_produced(self, tmp_log):
        plan = create_plan("acc1", "reel", 2, log_path=tmp_log)
        slot_id = plan.slots[0].slot_id
        updated = mark_slot(plan.plan_id, slot_id, "produced", log_path=tmp_log)
        assert updated.slots[0].status == SlotStatus.PRODUCED

    def test_assigns_asset_id(self, tmp_log):
        plan = create_plan("acc1", "reel", 2, log_path=tmp_log)
        slot_id = plan.slots[0].slot_id
        updated = mark_slot(plan.plan_id, slot_id, "assigned", asset_id="asset_abc", log_path=tmp_log)
        assert updated.slots[0].asset_id == "asset_abc"

    def test_raises_on_invalid_plan(self, tmp_log):
        with pytest.raises(PlanNotFoundError):
            mark_slot("bad_plan_id", "bad_slot_id", "produced", log_path=tmp_log)

    def test_raises_on_invalid_status(self, tmp_log):
        plan = create_plan("acc1", "reel", 2, log_path=tmp_log)
        with pytest.raises(PlanValidationError):
            mark_slot(plan.plan_id, plan.slots[0].slot_id, "invalid_status", log_path=tmp_log)


class TestVideoProductionPlanModel:
    def test_pending_count(self, tmp_log):
        plan = create_plan("acc1", "reel", 4, log_path=tmp_log)
        assert plan.pending_count() == 4
        assert plan.produced_count() == 0

    def test_roundtrip_serialization(self, tmp_log):
        from src.video_production.models import VideoProductionPlan
        plan = create_plan("acc1", "carousel", 3, log_path=tmp_log)
        d = plan.to_dict()
        restored = VideoProductionPlan.from_dict(d)
        assert restored.plan_id == plan.plan_id
        assert len(restored.slots) == len(plan.slots)
        assert restored.slots[0].date == plan.slots[0].date
