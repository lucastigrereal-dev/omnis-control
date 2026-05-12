"""Tests for P10 Sales/CRM service layer."""

from __future__ import annotations

import pytest

from src.sales_crm.errors import (
    ExternalContactBlockedError,
    InvalidDealError,
    InvalidFollowUpError,
    InvalidLeadError,
    InvalidObjectionError,
)
from src.sales_crm.models import (
    ActivityType,
    Deal,
    DealPriority,
    FollowUpStatus,
    FollowUpTask,
    Lead,
    LeadSource,
    LeadStatus,
    ObjectionCategory,
    ObjectionRecord,
    PipelineStage,
    ProposalRecord,
    SalesActivity,
    SalesPipeline,
)
from src.sales_crm.service import (
    PipelineSummary,
    SalesCRMPlanner,
    ScoreResult,
    ValidationResult,
)


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def planner():
    return SalesCRMPlanner()


@pytest.fixture
def lead(planner):
    return planner.create_lead(
        name="Hotel Teste",
        source=LeadSource.INSTAGRAM,
        business_name="Hotel Teste Ltda",
        contact_phone="+55 84 99999-0000",
        contact_email="contato@hotelteste.com.br",
        instagram_handle="@hotelteste",
        city="Natal",
        state="RN",
        niche="hotel",
        follower_count=50_000,
    )


@pytest.fixture
def deal(planner, lead):
    return planner.create_deal(lead.id, package="growth", priority=DealPriority.HIGH)


# ═══════════════════════════════════════════════════════════════
# SalesCRMPlanner — basics
# ═══════════════════════════════════════════════════════════════

class TestPlannerBasics:
    def test_default_dry_run_true(self):
        planner = SalesCRMPlanner()
        assert planner.dry_run is True

    def test_can_set_dry_run_false(self):
        planner = SalesCRMPlanner(dry_run=False)
        assert planner.dry_run is False

    def test_starts_empty(self):
        planner = SalesCRMPlanner()
        assert planner.lead_count == 0
        assert planner.deal_count == 0


# ═══════════════════════════════════════════════════════════════
# create_lead
# ═══════════════════════════════════════════════════════════════

class TestCreateLead:
    def test_returns_lead(self, planner):
        lead = planner.create_lead("Hotel X")
        assert isinstance(lead, Lead)
        assert lead.name == "Hotel X"

    def test_tracks_in_inventory(self, planner):
        planner.create_lead("A")
        planner.create_lead("B")
        assert planner.lead_count == 2

    def test_list_leads_returns_all(self, planner):
        planner.create_lead("A")
        planner.create_lead("B")
        leads = planner.list_leads()
        assert len(leads) == 2


# ═══════════════════════════════════════════════════════════════
# score_lead
# ═══════════════════════════════════════════════════════════════

class TestScoreLead:
    def test_raises_for_unknown_lead(self, planner):
        with pytest.raises(InvalidLeadError, match="Lead not found"):
            planner.score_lead("lead_nonexistent")

    def test_returns_score_result(self, planner, lead):
        result = planner.score_lead(lead.id)
        assert isinstance(result, ScoreResult)
        assert result.lead_id == lead.id

    def test_high_quality_lead_scores_high(self, planner, lead):
        result = planner.score_lead(lead.id)
        assert result.score > 60
        assert result.qualifies is True
        assert result.recommended_package in ("growth", "premium")

    def test_minimal_lead_scores_low(self, planner):
        lead = planner.create_lead("Minimal")
        result = planner.score_lead(lead.id)
        assert result.score < 40
        assert result.qualifies is False

    def test_breakdown_has_expected_keys(self, planner, lead):
        result = planner.score_lead(lead.id)
        expected = {"contact_info", "has_phone", "has_email", "has_instagram",
                    "follower_signal", "location", "niche_fit",
                    "has_business_name", "contact_channels"}
        assert set(result.breakdown.keys()) == expected

    def test_stores_score_on_lead(self, planner, lead):
        result = planner.score_lead(lead.id)
        assert lead.score == result.score

    def test_custom_threshold(self, planner):
        minimal = planner.create_lead("Minimal Lead")
        result = planner.score_lead(minimal.id, qualification_threshold=90)
        assert result.qualifies is False  # minimal lead won't hit 90


# ═══════════════════════════════════════════════════════════════
# create_deal
# ═══════════════════════════════════════════════════════════════

class TestCreateDeal:
    def test_raises_for_unknown_lead(self, planner):
        with pytest.raises(InvalidDealError, match="Lead not found"):
            planner.create_deal("lead_nonexistent")

    def test_returns_deal(self, planner, lead):
        deal = planner.create_deal(lead.id, package="growth")
        assert isinstance(deal, Deal)
        assert deal.lead_id == lead.id
        assert deal.package == "growth"
        assert deal.value_brl == 990

    def test_qualifies_lead_on_first_deal(self, planner, lead):
        assert lead.status == LeadStatus.NEW
        planner.create_deal(lead.id, package="growth")
        assert lead.status == LeadStatus.QUALIFIED

    def test_tracks_in_inventory(self, planner, lead):
        planner.create_deal(lead.id)
        planner.create_deal(lead.id, package="starter")
        assert planner.deal_count == 2

    def test_list_deals_returns_all(self, planner, lead):
        planner.create_deal(lead.id, package="growth")
        planner.create_deal(lead.id, package="starter")
        deals = planner.list_deals()
        assert len(deals) == 2


# ═══════════════════════════════════════════════════════════════
# advance_deal
# ═══════════════════════════════════════════════════════════════

class TestAdvanceDeal:
    def test_raises_for_unknown_deal(self, planner):
        with pytest.raises(InvalidDealError, match="Deal not found"):
            planner.advance_deal("deal_nonexistent", PipelineStage.PROPOSAL)

    def test_changes_stage_and_probability(self, planner, deal):
        planner.advance_deal(deal.id, PipelineStage.PROPOSAL)
        assert deal.stage == PipelineStage.PROPOSAL
        assert deal.probability == 0.50


# ═══════════════════════════════════════════════════════════════
# log_activity
# ═══════════════════════════════════════════════════════════════

class TestLogActivity:
    def test_blocks_external_contact(self, planner):
        with pytest.raises(ExternalContactBlockedError, match="External contact"):
            planner.log_activity(ActivityType.CALL, "Ligar para lead")

    def test_blocks_whatsapp(self, planner):
        with pytest.raises(ExternalContactBlockedError):
            planner.log_activity(ActivityType.WHATSAPP, "Mandar msg")

    def test_blocks_email(self, planner):
        with pytest.raises(ExternalContactBlockedError):
            planner.log_activity(ActivityType.EMAIL, "Enviar email")

    def test_blocks_dm(self, planner):
        with pytest.raises(ExternalContactBlockedError):
            planner.log_activity(ActivityType.DM, "Mandar DM")

    def test_allows_internal_activities(self, planner):
        for atype in [ActivityType.NOTE, ActivityType.MEETING, ActivityType.FOLLOW_UP]:
            act = planner.log_activity(atype, "Teste interno")
            assert isinstance(act, SalesActivity)
            assert act.activity_type == atype

    def test_tracks_activities(self, planner):
        planner.log_activity(ActivityType.NOTE, "Nota 1")
        planner.log_activity(ActivityType.NOTE, "Nota 2")
        assert len(planner.list_activities()) == 2


# ═══════════════════════════════════════════════════════════════
# record_objection
# ═══════════════════════════════════════════════════════════════

class TestRecordObjection:
    def test_returns_objection_record(self, planner):
        obj = planner.record_objection(ObjectionCategory.PRICE, "Muito caro")
        assert isinstance(obj, ObjectionRecord)
        assert obj.category == ObjectionCategory.PRICE

    def test_raises_for_unknown_lead(self, planner):
        with pytest.raises(InvalidObjectionError, match="Lead not found"):
            planner.record_objection(ObjectionCategory.PRICE, "Caro", lead_id="lead_fake")

    def test_raises_for_unknown_deal(self, planner):
        with pytest.raises(InvalidObjectionError, match="Deal not found"):
            planner.record_objection(ObjectionCategory.PRICE, "Caro", deal_id="deal_fake")

    def test_tracks_objections(self, planner, lead):
        planner.record_objection(ObjectionCategory.PRICE, "Caro", lead_id=lead.id)
        planner.record_objection(ObjectionCategory.TIMING, "Depois", lead_id=lead.id)
        assert len(planner.list_objections()) == 2


# ═══════════════════════════════════════════════════════════════
# plan_follow_up
# ═══════════════════════════════════════════════════════════════

class TestPlanFollowUp:
    def test_returns_follow_up_task(self, planner):
        fup = planner.plan_follow_up("Ligar", "2026-12-01T10:00:00Z")
        assert isinstance(fup, FollowUpTask)
        assert fup.description == "Ligar"
        assert fup.status == FollowUpStatus.PENDING

    def test_raises_for_unknown_lead(self, planner):
        with pytest.raises(InvalidFollowUpError, match="Lead not found"):
            planner.plan_follow_up("Tarefa", "2026-12-01T10:00:00Z", lead_id="lead_fake")

    def test_raises_for_unknown_deal(self, planner):
        with pytest.raises(InvalidFollowUpError, match="Deal not found"):
            planner.plan_follow_up("Tarefa", "2026-12-01T10:00:00Z", deal_id="deal_fake")

    def test_tracks_follow_ups(self, planner):
        planner.plan_follow_up("A", "2026-12-01T10:00:00Z")
        planner.plan_follow_up("B", "2026-12-02T10:00:00Z")
        assert len(planner.list_follow_ups()) == 2


# ═══════════════════════════════════════════════════════════════
# create_proposal
# ═══════════════════════════════════════════════════════════════

class TestCreateProposal:
    def test_returns_proposal(self, planner):
        prop = planner.create_proposal("growth")
        assert isinstance(prop, ProposalRecord)
        assert prop.package == "growth"
        assert prop.value_brl == 990

    def test_raises_for_unknown_lead(self, planner):
        with pytest.raises(InvalidDealError, match="Lead not found"):
            planner.create_proposal("growth", lead_id="lead_fake")

    def test_tracks_proposals(self, planner):
        planner.create_proposal("starter")
        planner.create_proposal("growth")
        assert len(planner.list_proposals()) == 2


# ═══════════════════════════════════════════════════════════════
# build_pipeline_summary
# ═══════════════════════════════════════════════════════════════

class TestBuildPipelineSummary:
    def test_returns_pipeline_summary(self, planner, deal):
        pipe = SalesPipeline.new("Test", "Test pipeline", deals=[deal])
        summary = planner.build_pipeline_summary(pipe)
        assert isinstance(summary, PipelineSummary)
        assert summary.pipeline_name == "Test"
        assert summary.total_deals == 1
        assert summary.active_deals == 1

    def test_empty_pipeline(self, planner):
        pipe = SalesPipeline.new("Empty", "No deals")
        summary = planner.build_pipeline_summary(pipe)
        assert summary.total_deals == 0
        assert summary.total_value == 0
        assert summary.won_deals == 0
        assert summary.lost_deals == 0

    def test_stage_breakdown(self, planner, lead):
        d1 = planner.create_deal(lead.id, package="starter", stage=PipelineStage.PROSPECTING)
        d2 = planner.create_deal(lead.id, package="growth", stage=PipelineStage.PROPOSAL)
        d3 = planner.create_deal(lead.id, package="premium", stage=PipelineStage.CLOSED_WON)
        pipe = SalesPipeline.new("Mix", "Mixed stages", deals=[d1, d2, d3])
        summary = planner.build_pipeline_summary(pipe)
        assert "prospecting" in summary.stage_breakdown
        assert "proposal" in summary.stage_breakdown
        assert "closed_won" in summary.stage_breakdown

    def test_risks_flag_stuck_prospecting(self, planner, lead):
        deals = []
        for i in range(7):
            deals.append(planner.create_deal(lead.id, package="starter",
                                             stage=PipelineStage.PROSPECTING))
        pipe = SalesPipeline.new("Stuck", "Many prospecting", deals=deals)
        summary = planner.build_pipeline_summary(pipe)
        assert any("stuck in prospecting" in r for r in summary.risks)

    def test_to_dict(self, planner, deal):
        pipe = SalesPipeline.new("T", "D", deals=[deal])
        summary = planner.build_pipeline_summary(pipe)
        d = summary.to_dict()
        assert d["pipeline_name"] == "T"
        assert d["total_deals"] == 1
        assert "stage_breakdown" in d


# ═══════════════════════════════════════════════════════════════
# validate_pipeline
# ═══════════════════════════════════════════════════════════════

class TestValidatePipeline:
    def test_empty_pipeline_warns(self, planner):
        pipe = SalesPipeline.new("Vazio", "Sem deals")
        result = planner.validate_pipeline(pipe)
        assert result.ok is True
        assert any("no deals" in w.lower() for w in result.warnings)

    def test_valid_pipeline_passes(self, planner, lead):
        deal = planner.create_deal(lead.id, package="growth")
        pipe = SalesPipeline.new("Ok", "Valid", deals=[deal])
        result = planner.validate_pipeline(pipe)
        assert result.ok is True

    def test_orphan_deal_fails(self, planner):
        deal = Deal.new(lead_id="lead_orphan", package="growth")
        pipe = SalesPipeline.new("Bad", "Orphan deal", deals=[deal])
        result = planner.validate_pipeline(pipe)
        assert result.valid is False
        assert any("unknown" in i.lower() or "references" in i.lower()
                   for i in result.issues)

    def test_probability_mismatch_warns(self, planner, lead):
        deal = planner.create_deal(lead.id, package="growth")
        deal.probability = 0.99  # override
        pipe = SalesPipeline.new("P", "D", deals=[deal])
        result = planner.validate_pipeline(pipe)
        assert any("probability" in w.lower() for w in result.warnings)

    def test_duplicate_active_deal_warns(self, planner, lead):
        d1 = planner.create_deal(lead.id, package="growth")
        d2 = planner.create_deal(lead.id, package="starter")
        pipe = SalesPipeline.new("Dup", "Duplicate active", deals=[d1, d2])
        result = planner.validate_pipeline(pipe)
        assert any("multiple active deals" in w.lower() for w in result.warnings)


# ═══════════════════════════════════════════════════════════════
# ValidationResult
# ═══════════════════════════════════════════════════════════════

class TestValidationResult:
    def test_success_ok(self):
        vr = ValidationResult.success()
        assert vr.valid is True
        assert vr.ok is True

    def test_success_with_warnings(self):
        vr = ValidationResult.success(warnings=["low confidence"])
        assert vr.ok is True
        assert vr.warnings == ["low confidence"]

    def test_failure_not_ok(self):
        vr = ValidationResult.failure(["bad schema"])
        assert vr.valid is False
        assert vr.ok is False


# ═══════════════════════════════════════════════════════════════
# ScoreResult
# ═══════════════════════════════════════════════════════════════

class TestScoreResult:
    def test_to_dict(self, planner, lead):
        result = planner.score_lead(lead.id)
        d = result.to_dict()
        assert d["lead_id"] == lead.id
        assert "score" in d
        assert "breakdown" in d
        assert "qualifies" in d


# ═══════════════════════════════════════════════════════════════
# Integration — full flow
# ═══════════════════════════════════════════════════════════════

class TestIntegrationFlow:
    def test_full_sales_flow(self, planner):
        # 1. Create and score a lead
        lead = planner.create_lead(
            name="Restaurante Sabor",
            source=LeadSource.INSTAGRAM,
            business_name="Sabor Ltda",
            contact_phone="+55 84 98888-0000",
            contact_email="contato@sabor.com.br",
            instagram_handle="@sabornatal",
            city="Natal",
            state="RN",
            niche="restaurante",
            follower_count=25_000,
        )
        score = planner.score_lead(lead.id)
        assert score.qualifies is True

        # 2. Create deal from qualified lead
        deal = planner.create_deal(lead.id, package="growth", priority=DealPriority.HIGH)
        assert deal.lead_id == lead.id
        assert lead.status == LeadStatus.QUALIFIED

        # 3. Log internal activity
        act = planner.log_activity(ActivityType.NOTE, "Lead muito interessado no Growth", lead_id=lead.id, deal_id=deal.id)
        assert isinstance(act, SalesActivity)

        # 4. Record objection
        obj = planner.record_objection(ObjectionCategory.PRICE, "R$990 está acima do orçamento", lead_id=lead.id, deal_id=deal.id)
        obj.resolve("Podemos parcelar em 3x no cartão")
        assert obj.resolved is True

        # 5. Plan follow-up
        fup = planner.plan_follow_up("Revisar objeção resolvida", "2026-05-15T10:00:00Z", lead_id=lead.id, deal_id=deal.id)
        assert fup.status == FollowUpStatus.PENDING

        # 6. Create proposal
        prop = planner.create_proposal("growth", lead_id=lead.id, deal_id=deal.id,
                                       content_summary="Pacote Growth — 3 collabs mensais")
        assert prop.package == "growth"

        # 7. Advance deal to proposal stage
        planner.advance_deal(deal.id, PipelineStage.PROPOSAL)
        assert deal.probability == 0.50

        # 8. Build pipeline summary
        pipe = SalesPipeline.new("Pipeline Test", "Integration test", deals=[deal])
        summary = planner.build_pipeline_summary(pipe)
        assert summary.total_deals == 1
        assert summary.total_value == 990

        # 9. Validate
        vr = planner.validate_pipeline(pipe)
        assert vr.ok is True

        # 10. Verify inventory
        assert planner.lead_count == 1
        assert planner.deal_count == 1
        assert len(planner.list_activities()) == 1
        assert len(planner.list_objections()) == 1
        assert len(planner.list_follow_ups()) == 1
        assert len(planner.list_proposals()) == 1
