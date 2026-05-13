"""Tests for CampaignOrchestrator service."""

from __future__ import annotations

import pytest

from src.analytics.service import MetricSummary
from src.marketing.models import CampaignBrief

from src.campaign_manager.errors import BudgetError, CampaignError, ROIError, StateTransitionError
from src.campaign_manager.models import Campaign, CampaignStatus, _now_iso
from src.campaign_manager.service import CampaignOrchestrator


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------


def _make_brief(name="Hotel Villa do Sol", budget=350.0, end_date="2026-05-20T23:59:59Z"):
    return CampaignBrief.new(
        name=name,
        objective_id="mktobj_abc",
        audience_id="aud_abc",
        budget=budget,
        end_date=end_date,
        key_message="Test message",
        call_to_action="link_bio",
        tone="professional",
    )


def _make_channels():
    return [
        {"profile": "lucastigrereal", "role": "primary_authority", "slot_count": 2},
        {"profile": "afamiliatigrereal", "role": "family_support", "slot_count": 1},
    ]


def _make_metrics():
    return MetricSummary.compute("met_abc", [1200.0, 800.0, 950.0, 1100.0, 900.0])


# ============================================================================
# orchestrate_campaign
# ============================================================================


class TestOrchestrateCampaign:
    def test_creates_campaign_from_brief(self):
        brief = _make_brief()
        channels = _make_channels()
        result = CampaignOrchestrator.orchestrate_campaign(brief, channels=channels)
        assert isinstance(result, Campaign)
        assert result.campaign_name == "Hotel Villa do Sol"
        assert result.brief_ref == brief.id

    def test_returns_planned_status(self):
        brief = _make_brief()
        result = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        assert result.status == CampaignStatus.PLANNED

    def test_sets_budget_from_brief(self):
        brief = _make_brief(budget=500.0)
        result = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        assert result.budget is not None
        assert result.budget.total_budget_brl == 500.0

    def test_rejects_empty_channels(self):
        brief = _make_brief()
        with pytest.raises(CampaignError, match="brief must define at least 1 channel"):
            CampaignOrchestrator.orchestrate_campaign(brief, channels=[])

    def test_rejects_zero_budget_brief(self):
        brief = _make_brief(budget=0.0)
        with pytest.raises(BudgetError, match="total_budget_brl must be > 0"):
            CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())

    def test_rejects_unnamed_brief(self):
        brief = _make_brief(name="")
        with pytest.raises(CampaignError, match="brief must have a name"):
            CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())

    def test_uses_budget_total_param(self):
        brief = _make_brief(budget=350.0)
        result = CampaignOrchestrator.orchestrate_campaign(
            brief, channels=_make_channels(), budget_total=990.0
        )
        assert result.budget.total_budget_brl == 990.0

    def test_dry_run_default_true(self):
        brief = _make_brief()
        result = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        assert result.dry_run is True

    def test_budget_backref_matches_campaign(self):
        brief = _make_brief()
        result = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        assert result.budget.campaign_ref == result.campaign_id


# ============================================================================
# allocate_budget
# ============================================================================


class TestAllocateBudget:
    def test_creates_budget_tracker(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        bt = CampaignOrchestrator.allocate_budget(campaign, 990.0)
        assert bt.budget_id.startswith("bud_")
        assert bt.total_budget_brl == 990.0

    def test_updates_campaign_budget(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        CampaignOrchestrator.allocate_budget(campaign, 500.0)
        assert campaign.budget.total_budget_brl == 500.0

    def test_rejects_zero_budget(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        with pytest.raises(BudgetError, match="total_budget_brl must be > 0"):
            CampaignOrchestrator.allocate_budget(campaign, 0.0)

    def test_rejects_negative_budget(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        with pytest.raises(BudgetError, match="total_budget_brl must be > 0"):
            CampaignOrchestrator.allocate_budget(campaign, -100.0)

    def test_rejects_archived_campaign(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        campaign.transition_to(CampaignStatus.IN_PROGRESS)
        campaign.transition_to(CampaignStatus.COMPLETED)
        campaign.transition_to(CampaignStatus.ANALYZED)
        campaign.transition_to(CampaignStatus.ARCHIVED)
        with pytest.raises(StateTransitionError, match="archived campaigns cannot be reopened"):
            CampaignOrchestrator.allocate_budget(campaign, 500.0)

    def test_with_breakdown(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        breakdown = [
            {"category": "collab_posts", "allocated_brl": 600.0, "spent_brl": 0.0},
        ]
        bt = CampaignOrchestrator.allocate_budget(campaign, 990.0, breakdown=breakdown)
        assert bt.breakdown == breakdown


# ============================================================================
# calculate_roi
# ============================================================================


class TestCalculateROI:
    def test_returns_roi_calculation(self):
        brief = _make_brief(budget=500.0)
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        roi = CampaignOrchestrator.calculate_roi(campaign)
        assert roi.roi_id.startswith("roi_")

    def test_updates_campaign_roi(self):
        brief = _make_brief(budget=500.0)
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        CampaignOrchestrator.calculate_roi(campaign)
        assert campaign.roi is not None

    def test_rejects_without_budget(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        campaign.budget = None
        with pytest.raises(ROIError, match="cannot calculate ROI without budget"):
            CampaignOrchestrator.calculate_roi(campaign)

    def test_rejects_empty_metrics(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        empty = MetricSummary.compute("met_abc", [])
        with pytest.raises(ROIError, match="cannot calculate ROI without metrics"):
            CampaignOrchestrator.calculate_roi(campaign, metrics=empty)

    def test_with_metrics_populates_actual(self):
        brief = _make_brief(budget=500.0)
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        roi = CampaignOrchestrator.calculate_roi(campaign, metrics=_make_metrics())
        assert roi.actual_revenue_brl is not None
        assert roi.actual_cost_brl is not None
        assert roi.calculated_at is not None

    def test_projected_roi_calculated(self):
        brief = _make_brief(budget=500.0)
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        roi = CampaignOrchestrator.calculate_roi(campaign)
        assert roi.projected_roi_percent is not None


# ============================================================================
# transition_state
# ============================================================================


class TestTransitionState:
    def test_planned_to_in_progress(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        result = CampaignOrchestrator.transition_state(campaign, CampaignStatus.IN_PROGRESS)
        assert result.status == CampaignStatus.IN_PROGRESS

    def test_invalid_transition_raises(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        with pytest.raises(StateTransitionError):
            CampaignOrchestrator.transition_state(campaign, CampaignStatus.ANALYZED)

    def test_archived_rejects_transitions(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        campaign.transition_to(CampaignStatus.IN_PROGRESS)
        campaign.transition_to(CampaignStatus.COMPLETED)
        campaign.transition_to(CampaignStatus.ANALYZED)
        campaign.transition_to(CampaignStatus.ARCHIVED)
        with pytest.raises(StateTransitionError, match="archived campaigns cannot be reopened"):
            CampaignOrchestrator.transition_state(campaign, CampaignStatus.PLANNED)


# ============================================================================
# build_publish_queue_plan
# ============================================================================


class TestBuildPublishQueuePlan:
    def test_returns_dict(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        plan = CampaignOrchestrator.build_publish_queue_plan(campaign)
        assert isinstance(plan, dict)

    def test_contains_plan_id(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        plan = CampaignOrchestrator.build_publish_queue_plan(campaign)
        assert plan["plan_id"].startswith("pqp_")

    def test_item_count_matches_slots(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        plan = CampaignOrchestrator.build_publish_queue_plan(campaign)
        assert plan["item_count"] == 3  # 2 + 1

    def test_channel_order_respects_primary_first(self):
        brief = _make_brief()
        channels = [
            {"profile": "afamiliatigrereal", "role": "family_support", "slot_count": 1},
            {"profile": "lucastigrereal", "role": "primary_authority", "slot_count": 1},
        ]
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=channels)
        plan = CampaignOrchestrator.build_publish_queue_plan(campaign)
        assert plan["channel_order"][0] == "lucastigrereal"

    def test_updates_campaign_publish_ref(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        plan = CampaignOrchestrator.build_publish_queue_plan(campaign)
        assert campaign.publish_queue_plan_ref == plan["plan_id"]

    def test_empty_channels_raises(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        campaign.channels = []
        with pytest.raises(CampaignError, match="publish queue plan is empty"):
            CampaignOrchestrator.build_publish_queue_plan(campaign)


# ============================================================================
# generate_manifest
# ============================================================================


class TestGenerateManifest:
    def test_returns_dict(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        manifest = CampaignOrchestrator.generate_manifest(campaign)
        assert isinstance(manifest, dict)

    def test_contains_manifest_version(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        manifest = CampaignOrchestrator.generate_manifest(campaign)
        assert manifest["manifest_version"] == "1.0"

    def test_contains_generated_by(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        manifest = CampaignOrchestrator.generate_manifest(campaign)
        assert manifest["generated_by"] == "src/campaign_manager/"

    def test_contains_checksum(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        manifest = CampaignOrchestrator.generate_manifest(campaign)
        assert manifest["checksum"] is not None
        assert len(manifest["checksum"]) == 64  # SHA256 hex

    def test_contains_campaign_snapshot(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        manifest = CampaignOrchestrator.generate_manifest(campaign)
        assert manifest["campaign"]["campaign_id"] == campaign.campaign_id

    def test_contains_budget_snapshot(self):
        brief = _make_brief(budget=500.0)
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        manifest = CampaignOrchestrator.generate_manifest(campaign)
        assert manifest["budget"]["total_budget_brl"] == 500.0

    def test_checksum_is_deterministic(self):
        brief = _make_brief()
        campaign = CampaignOrchestrator.orchestrate_campaign(brief, channels=_make_channels())
        m1 = CampaignOrchestrator.generate_manifest(campaign)
        m2 = CampaignOrchestrator.generate_manifest(campaign)
        assert m1["checksum"] == m2["checksum"]
