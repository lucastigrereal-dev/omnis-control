"""Tests for P19 models: Campaign, BudgetTracker, ROICalculation, CampaignStatus."""

from __future__ import annotations

import pytest

from src.campaign_manager.errors import BudgetError, StateTransitionError
from src.campaign_manager.models import (
    ROICalculation,
    VALID_TRANSITIONS,
    BudgetTracker,
    Campaign,
    CampaignStatus,
    _new_id,
    _now_iso,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_channel(profile="lucastigrereal", role="primary_authority", slot_count=1):
    return {"profile": profile, "role": role, "slot_count": slot_count}


# ============================================================================
# CampaignStatus enum
# ============================================================================


class TestCampaignStatusEnum:
    def test_exactly_six_states(self):
        assert len(CampaignStatus) == 6

    def test_contains_draft(self):
        assert CampaignStatus.DRAFT.value == "draft"

    def test_contains_planned(self):
        assert CampaignStatus.PLANNED.value == "planned"

    def test_contains_in_progress(self):
        assert CampaignStatus.IN_PROGRESS.value == "in_progress"

    def test_contains_completed(self):
        assert CampaignStatus.COMPLETED.value == "completed"

    def test_contains_analyzed(self):
        assert CampaignStatus.ANALYZED.value == "analyzed"

    def test_contains_archived(self):
        assert CampaignStatus.ARCHIVED.value == "archived"

    def test_is_str_enum(self):
        assert isinstance(CampaignStatus.DRAFT, str)


# ============================================================================
# BudgetTracker
# ============================================================================


class TestBudgetTracker:
    def test_new_creates_valid_id(self):
        bt = BudgetTracker.new(campaign_ref="cmp_abc", total_budget_brl=350.0)
        assert bt.budget_id.startswith("bud_")

    def test_new_sets_campaign_ref(self):
        bt = BudgetTracker.new(campaign_ref="cmp_abc", total_budget_brl=350.0)
        assert bt.campaign_ref == "cmp_abc"

    def test_new_sets_allocated_equal_to_total(self):
        bt = BudgetTracker.new(campaign_ref="cmp_abc", total_budget_brl=500.0)
        assert bt.allocated_brl == 500.0

    def test_new_spent_starts_at_zero(self):
        bt = BudgetTracker.new(campaign_ref="cmp_abc", total_budget_brl=350.0)
        assert bt.spent_brl == 0.0

    def test_new_rejects_zero_budget(self):
        with pytest.raises(BudgetError, match="total_budget_brl must be > 0"):
            BudgetTracker.new(campaign_ref="cmp_abc", total_budget_brl=0.0)

    def test_new_rejects_negative_budget(self):
        with pytest.raises(BudgetError, match="total_budget_brl must be > 0"):
            BudgetTracker.new(campaign_ref="cmp_abc", total_budget_brl=-100.0)

    def test_default_currency_is_brl(self):
        bt = BudgetTracker.new(campaign_ref="cmp_abc", total_budget_brl=350.0)
        assert bt.currency == "BRL"

    def test_remaining_brl(self):
        bt = BudgetTracker.new(campaign_ref="cmp_abc", total_budget_brl=500.0)
        bt.spent_brl = 200.0
        assert bt.remaining_brl == 300.0

    def test_is_over_budget(self):
        bt = BudgetTracker.new(campaign_ref="cmp_abc", total_budget_brl=500.0)
        bt.spent_brl = 600.0
        assert bt.is_over_budget

    def test_is_not_over_budget(self):
        bt = BudgetTracker.new(campaign_ref="cmp_abc", total_budget_brl=500.0)
        bt.spent_brl = 400.0
        assert not bt.is_over_budget

    def test_to_dict_roundtrip(self):
        bt = BudgetTracker.new(campaign_ref="cmp_abc", total_budget_brl=990.0)
        bt.breakdown = [{"category": "collab", "allocated_brl": 600.0}]
        data = bt.to_dict()
        bt2 = BudgetTracker.from_dict(data)
        assert bt2.budget_id == bt.budget_id
        assert bt2.total_budget_brl == 990.0
        assert bt2.breakdown == [{"category": "collab", "allocated_brl": 600.0}]

    def test_from_dict_preserves_spent(self):
        data = {
            "budget_id": "bud_1234",
            "campaign_ref": "cmp_xyz",
            "total_budget_brl": 350.0,
            "allocated_brl": 200.0,
            "spent_brl": 100.0,
            "breakdown": [],
            "currency": "BRL",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        bt = BudgetTracker.from_dict(data)
        assert bt.spent_brl == 100.0
        assert bt.allocated_brl == 200.0


# ============================================================================
# ROICalculation
# ============================================================================


class TestROICalculation:
    def test_new_creates_valid_id(self):
        roi = ROICalculation.new(campaign_ref="cmp_abc", projected_revenue_brl=500.0)
        assert roi.roi_id.startswith("roi_")

    def test_new_sets_campaign_ref(self):
        roi = ROICalculation.new(campaign_ref="cmp_abc", projected_revenue_brl=500.0)
        assert roi.campaign_ref == "cmp_abc"

    def test_new_calculates_projected_roi(self):
        roi = ROICalculation.new(
            campaign_ref="cmp_abc",
            projected_revenue_brl=500.0,
            projected_cost_brl=250.0,
        )
        assert roi.projected_roi_percent == 100.0

    def test_new_projected_roi_none_when_cost_zero(self):
        roi = ROICalculation.new(
            campaign_ref="cmp_abc",
            projected_revenue_brl=500.0,
            projected_cost_brl=0.0,
        )
        assert roi.projected_roi_percent is None

    def test_actual_fields_start_none(self):
        roi = ROICalculation.new(campaign_ref="cmp_abc", projected_revenue_brl=500.0)
        assert roi.actual_revenue_brl is None
        assert roi.actual_cost_brl is None
        assert roi.actual_roi_percent is None

    def test_default_formula(self):
        roi = ROICalculation.new(campaign_ref="cmp_abc", projected_revenue_brl=500.0)
        assert "revenue - cost" in roi.formula

    def test_roi_label_with_projected(self):
        roi = ROICalculation.new(
            campaign_ref="cmp_abc",
            projected_revenue_brl=500.0,
            projected_cost_brl=250.0,
        )
        assert roi.roi_label == "100.0%"

    def test_roi_label_na_when_none(self):
        roi = ROICalculation.new(campaign_ref="cmp_abc", projected_revenue_brl=500.0)
        assert roi.roi_label == "N/A"

    def test_to_dict_roundtrip(self):
        roi = ROICalculation.new(
            campaign_ref="cmp_abc",
            projected_revenue_brl=990.0,
            projected_cost_brl=300.0,
        )
        data = roi.to_dict()
        roi2 = ROICalculation.from_dict(data)
        assert roi2.roi_id == roi.roi_id
        assert roi2.projected_roi_percent == roi.projected_roi_percent


# ============================================================================
# Campaign
# ============================================================================


class TestCampaign:
    def test_new_creates_valid_id(self):
        c = Campaign.new(
            campaign_name="Test Campaign",
            brief_ref="cmp_brief123",
            channels=[_make_channel()],
        )
        assert c.campaign_id.startswith("cmp_")

    def test_new_starts_in_draft(self):
        c = Campaign.new(
            campaign_name="Test Campaign",
            brief_ref="cmp_brief123",
            channels=[_make_channel()],
        )
        assert c.status == CampaignStatus.DRAFT

    def test_new_rejects_empty_channels(self):
        with pytest.raises(BudgetError, match="brief must define at least 1 channel"):
            Campaign.new(campaign_name="Test", brief_ref="cmp_abc", channels=[])

    def test_new_defaults_dry_run_true(self):
        c = Campaign.new(
            campaign_name="Test",
            brief_ref="cmp_abc",
            channels=[_make_channel()],
        )
        assert c.dry_run is True

    def test_new_defaults_approval_required_true(self):
        c = Campaign.new(
            campaign_name="Test",
            brief_ref="cmp_abc",
            channels=[_make_channel()],
        )
        assert c.approval_required is True

    def test_new_retry_count_starts_zero(self):
        c = Campaign.new(
            campaign_name="Test",
            brief_ref="cmp_abc",
            channels=[_make_channel()],
        )
        assert c.retry_count == 0

    def test_new_error_message_starts_none(self):
        c = Campaign.new(
            campaign_name="Test",
            brief_ref="cmp_abc",
            channels=[_make_channel()],
        )
        assert c.error_message is None

    def test_new_stores_tags(self):
        c = Campaign.new(
            campaign_name="Test",
            brief_ref="cmp_abc",
            channels=[_make_channel()],
            tags=["hotel", "collab"],
        )
        assert "hotel" in c.tags

    def test_to_dict_roundtrip(self):
        budget = BudgetTracker.new(campaign_ref="cmp_abc", total_budget_brl=350.0)
        roi = ROICalculation.new(campaign_ref="cmp_abc", projected_revenue_brl=350.0)
        c = Campaign.new(
            campaign_name="Hotel Villa",
            brief_ref="cmp_brief123",
            channels=[_make_channel(), _make_channel("afamiliatigrereal", "family_support", 2)],
            budget=budget,
            roi=roi,
            deadline="2026-05-20T23:59:59Z",
            tags=["hotel"],
        )
        data = c.to_dict()
        c2 = Campaign.from_dict(data)
        assert c2.campaign_id == c.campaign_id
        assert c2.campaign_name == "Hotel Villa"
        assert c2.status == CampaignStatus.DRAFT
        assert len(c2.channels) == 2
        assert c2.budget is not None
        assert c2.budget.total_budget_brl == 350.0
        assert c2.roi is not None

    def test_from_dict_with_string_status(self):
        data = {
            "campaign_id": "cmp_test1",
            "campaign_name": "From Dict",
            "brief_ref": "cmp_bref1",
            "status": "draft",
            "channels": [_make_channel()],
            "budget": None,
            "roi": None,
            "metrics_plan": {},
            "timeline": {"created_at": _now_iso(), "deadline": None},
            "publish_queue_plan_ref": None,
            "dry_run": True,
            "approval_required": True,
            "retry_count": 0,
            "error_message": None,
            "tags": [],
        }
        c = Campaign.from_dict(data)
        assert c.status == CampaignStatus.DRAFT


# ============================================================================
# State transitions
# ============================================================================


class TestStateTransitions:
    def test_draft_to_planned_valid(self):
        c = Campaign.new(
            campaign_name="Test", brief_ref="cmp_abc", channels=[_make_channel()]
        )
        c.transition_to(CampaignStatus.PLANNED)
        assert c.status == CampaignStatus.PLANNED

    def test_planned_to_in_progress_valid(self):
        c = Campaign.new(
            campaign_name="Test", brief_ref="cmp_abc", channels=[_make_channel()]
        )
        c.transition_to(CampaignStatus.PLANNED)
        c.transition_to(CampaignStatus.IN_PROGRESS)
        assert c.status == CampaignStatus.IN_PROGRESS

    def test_in_progress_to_completed_valid(self):
        c = Campaign.new(
            campaign_name="Test", brief_ref="cmp_abc", channels=[_make_channel()]
        )
        c.transition_to(CampaignStatus.PLANNED)
        c.transition_to(CampaignStatus.IN_PROGRESS)
        c.transition_to(CampaignStatus.COMPLETED)
        assert c.status == CampaignStatus.COMPLETED

    def test_completed_to_analyzed_valid(self):
        c = Campaign.new(
            campaign_name="Test", brief_ref="cmp_abc", channels=[_make_channel()]
        )
        c.transition_to(CampaignStatus.PLANNED)
        c.transition_to(CampaignStatus.IN_PROGRESS)
        c.transition_to(CampaignStatus.COMPLETED)
        c.transition_to(CampaignStatus.ANALYZED)
        assert c.status == CampaignStatus.ANALYZED

    def test_analyzed_to_archived_valid(self):
        c = Campaign.new(
            campaign_name="Test", brief_ref="cmp_abc", channels=[_make_channel()]
        )
        c.transition_to(CampaignStatus.PLANNED)
        c.transition_to(CampaignStatus.IN_PROGRESS)
        c.transition_to(CampaignStatus.COMPLETED)
        c.transition_to(CampaignStatus.ANALYZED)
        c.transition_to(CampaignStatus.ARCHIVED)
        assert c.status == CampaignStatus.ARCHIVED

    def test_draft_to_completed_invalid(self):
        c = Campaign.new(
            campaign_name="Test", brief_ref="cmp_abc", channels=[_make_channel()]
        )
        with pytest.raises(StateTransitionError, match="invalid transition"):
            c.transition_to(CampaignStatus.COMPLETED)

    def test_archived_cannot_reopen(self):
        c = Campaign.new(
            campaign_name="Test", brief_ref="cmp_abc", channels=[_make_channel()]
        )
        c.transition_to(CampaignStatus.PLANNED)
        c.transition_to(CampaignStatus.IN_PROGRESS)
        c.transition_to(CampaignStatus.COMPLETED)
        c.transition_to(CampaignStatus.ANALYZED)
        c.transition_to(CampaignStatus.ARCHIVED)
        with pytest.raises(StateTransitionError):
            c.transition_to(CampaignStatus.PLANNED)

    def test_transition_updates_started_at(self):
        c = Campaign.new(
            campaign_name="Test", brief_ref="cmp_abc", channels=[_make_channel()]
        )
        c.transition_to(CampaignStatus.PLANNED)
        assert c.timeline["started_at"] is None
        c.transition_to(CampaignStatus.IN_PROGRESS)
        assert c.timeline["started_at"] is not None

    def test_transition_updates_completed_at(self):
        c = Campaign.new(
            campaign_name="Test", brief_ref="cmp_abc", channels=[_make_channel()]
        )
        c.transition_to(CampaignStatus.PLANNED)
        c.transition_to(CampaignStatus.IN_PROGRESS)
        c.transition_to(CampaignStatus.COMPLETED)
        assert c.timeline["completed_at"] is not None

    def test_transition_updates_analyzed_at(self):
        c = Campaign.new(
            campaign_name="Test", brief_ref="cmp_abc", channels=[_make_channel()]
        )
        c.transition_to(CampaignStatus.PLANNED)
        c.transition_to(CampaignStatus.IN_PROGRESS)
        c.transition_to(CampaignStatus.COMPLETED)
        c.transition_to(CampaignStatus.ANALYZED)
        assert c.timeline["analyzed_at"] is not None

    def test_transition_updates_archived_at(self):
        c = Campaign.new(
            campaign_name="Test", brief_ref="cmp_abc", channels=[_make_channel()]
        )
        c.transition_to(CampaignStatus.PLANNED)
        c.transition_to(CampaignStatus.IN_PROGRESS)
        c.transition_to(CampaignStatus.COMPLETED)
        c.transition_to(CampaignStatus.ANALYZED)
        c.transition_to(CampaignStatus.ARCHIVED)
        assert c.timeline["archived_at"] is not None

    def test_valid_transitions_covers_all_states(self):
        for status in CampaignStatus:
            assert status in VALID_TRANSITIONS, f"{status} missing from VALID_TRANSITIONS"


# ============================================================================
# Helpers
# ============================================================================


class TestHelpers:
    def test_now_iso_returns_string(self):
        assert isinstance(_now_iso(), str)

    def test_now_iso_contains_t(self):
        assert "T" in _now_iso()

    def test_new_id_uses_prefix(self):
        id1 = _new_id("cmp_")
        assert id1.startswith("cmp_")

    def test_new_id_is_unique(self):
        ids = {_new_id("tst_") for _ in range(100)}
        assert len(ids) == 100
