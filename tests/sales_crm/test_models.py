"""Tests for P10 Sales/CRM models."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.sales_crm.models import (
    VALID_PACKAGES,
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
    ProposalStatus,
    SalesActivity,
    SalesPipeline,
)


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _make_lead(**kw) -> Lead:
    return Lead.new(
        name=kw.pop("name", "Hotel Teste"),
        source=kw.pop("source", LeadSource.INSTAGRAM),
        business_name=kw.pop("business_name", "Hotel Teste Ltda"),
        contact_phone=kw.pop("contact_phone", "+55 84 99999-0000"),
        contact_email=kw.pop("contact_email", "contato@hotelteste.com.br"),
        instagram_handle=kw.pop("instagram_handle", "@hotelteste"),
        city=kw.pop("city", "Natal"),
        state=kw.pop("state", "RN"),
        niche=kw.pop("niche", "hotel"),
        **kw,
    )


def _make_deal(**kw) -> Deal:
    return Deal.new(
        lead_id=kw.pop("lead_id", "lead_abc12345"),
        package=kw.pop("package", "growth"),
        **kw,
    )


# ═══════════════════════════════════════════════════════════════
# Lead
# ═══════════════════════════════════════════════════════════════

class TestLead:
    def test_new_creates_lead_with_id_prefix(self):
        lead = _make_lead()
        assert lead.id.startswith("lead_")
        assert len(lead.id) == 13  # "lead_" + 8 hex

    def test_new_unique_ids(self):
        a = _make_lead()
        b = _make_lead()
        assert a.id != b.id

    def test_new_defaults_status_to_new(self):
        lead = _make_lead()
        assert lead.status == LeadStatus.NEW
        assert lead.score == 0.0

    def test_new_rejects_empty_name(self):
        with pytest.raises(ValueError, match="Lead name is required"):
            Lead.new(name="   ")

    def test_new_strips_strings(self):
        lead = Lead.new(name="  Hotel X  ", contact_phone="  +55 11  ", city="  SP  ")
        assert lead.name == "Hotel X"
        assert lead.contact_phone == "+55 11"
        assert lead.city == "SP"

    def test_has_contact_info_with_phone(self):
        lead = _make_lead(contact_email=None, instagram_handle=None)
        assert lead.has_contact_info is True

    def test_has_contact_info_false_when_none(self):
        lead = _make_lead(contact_phone=None, contact_email=None, instagram_handle=None)
        assert lead.has_contact_info is False

    def test_dry_run_true_by_default(self):
        lead = _make_lead()
        assert lead.dry_run is True

    def test_is_qualified(self):
        lead = _make_lead()
        assert lead.is_qualified is False
        lead.status = LeadStatus.QUALIFIED
        assert lead.is_qualified is True

    def test_to_dict_from_dict_round_trip(self):
        lead = _make_lead(tags=["vip", "urgent"], notes="Test note")
        d = lead.to_dict()
        restored = Lead.from_dict(d)
        assert restored.id == lead.id
        assert restored.name == lead.name
        assert restored.source == lead.source
        assert restored.tags == ["vip", "urgent"]
        assert restored.notes == "Test note"

    def test_to_json_from_json_round_trip(self):
        lead = _make_lead()
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "lead.json"
            lead.to_json(p)
            restored = Lead.from_json(p)
            assert restored.id == lead.id
            assert restored.name == lead.name

    def test_from_dict_populates_defaults(self):
        d = {"id": "lead_abc", "name": "Test", "source": "instagram"}
        lead = Lead.from_dict(d)
        assert lead.status == LeadStatus.NEW
        assert lead.score == 0.0
        assert lead.tags == []
        assert lead.dry_run is True

    def test_optional_fields_none_by_default(self):
        lead = Lead.new(name="Minimal")
        assert lead.business_name is None
        assert lead.contact_phone is None
        assert lead.contact_email is None
        assert lead.city is None


# ═══════════════════════════════════════════════════════════════
# Deal
# ═══════════════════════════════════════════════════════════════

class TestDeal:
    def test_new_creates_deal_with_id_prefix(self):
        deal = _make_deal()
        assert deal.id.startswith("deal_")

    def test_new_unique_ids(self):
        a = _make_deal()
        b = _make_deal()
        assert a.id != b.id

    def test_new_rejects_invalid_package(self):
        with pytest.raises(ValueError, match="Invalid package"):
            _make_deal(package="enterprise")

    def test_new_accepts_all_valid_packages(self):
        for pkg in VALID_PACKAGES:
            deal = _make_deal(package=pkg)
            assert deal.package == pkg

    def test_package_prices(self):
        assert _make_deal(package="starter").value_brl == 350
        assert _make_deal(package="growth").value_brl == 990
        assert _make_deal(package="premium").value_brl == 1200

    def test_default_stage_prospecting(self):
        deal = _make_deal()
        assert deal.stage == PipelineStage.PROSPECTING
        assert deal.probability == 0.10

    def test_default_probabilities_by_stage(self):
        expected = {
            PipelineStage.PROSPECTING: 0.10,
            PipelineStage.QUALIFICATION: 0.30,
            PipelineStage.PROPOSAL: 0.50,
            PipelineStage.NEGOTIATION: 0.70,
            PipelineStage.CLOSED_WON: 1.0,
            PipelineStage.CLOSED_LOST: 0.0,
        }
        for stage, prob in expected.items():
            deal = _make_deal(stage=stage)
            assert deal.probability == prob, f"Stage {stage}: expected {prob}, got {deal.probability}"

    def test_expected_value(self):
        deal = _make_deal(package="growth")
        assert deal.expected_value == 990 * 0.10

    def test_is_active(self):
        deal = _make_deal()
        assert deal.is_active is True
        deal.stage = PipelineStage.CLOSED_WON
        assert deal.is_active is False
        deal.stage = PipelineStage.CLOSED_LOST
        assert deal.is_active is False

    def test_to_dict_from_dict_round_trip(self):
        deal = _make_deal(expected_close_date="2026-06-01", tags=["premium"])
        d = deal.to_dict()
        restored = Deal.from_dict(d)
        assert restored.id == deal.id
        assert restored.lead_id == deal.lead_id
        assert restored.stage == deal.stage
        assert restored.tags == ["premium"]

    def test_custom_probability_overrides_default(self):
        deal = _make_deal(probability=0.60)
        assert deal.probability == 0.60


# ═══════════════════════════════════════════════════════════════
# SalesActivity
# ═══════════════════════════════════════════════════════════════

class TestSalesActivity:
    def test_new_creates_activity_with_id_prefix(self):
        act = SalesActivity.new(ActivityType.NOTE, "Test note")
        assert act.id.startswith("act_")

    def test_external_activities_require_approval(self):
        act = SalesActivity.new(ActivityType.CALL, "Ligar para lead")
        assert act.approval_required is True
        assert act.approved is False
        assert "external_contact_blocked" in act.risk_flags

    def test_note_does_not_require_approval(self):
        act = SalesActivity.new(ActivityType.NOTE, "Nota interna")
        assert act.approval_required is False
        assert act.risk_flags == []

    def test_follow_up_does_not_require_approval(self):
        act = SalesActivity.new(ActivityType.FOLLOW_UP, "Revisar follow-up")
        assert act.approval_required is False

    def test_all_external_types_require_approval(self):
        for atype in [ActivityType.CALL, ActivityType.WHATSAPP, ActivityType.EMAIL, ActivityType.DM]:
            act = SalesActivity.new(atype, "Test")
            assert act.approval_required is True, f"{atype} should require approval"
            assert act.is_external is True

    def test_non_external_types(self):
        for atype in [ActivityType.MEETING, ActivityType.FOLLOW_UP, ActivityType.NOTE]:
            act = SalesActivity.new(atype, "Test")
            assert act.is_external is False

    def test_to_dict_from_dict_round_trip(self):
        act = SalesActivity.new(ActivityType.NOTE, "Nota", lead_id="lead_abc", outcome="Ok")
        d = act.to_dict()
        restored = SalesActivity.from_dict(d)
        assert restored.id == act.id
        assert restored.description == "Nota"
        assert restored.outcome == "Ok"


# ═══════════════════════════════════════════════════════════════
# ObjectionRecord
# ═══════════════════════════════════════════════════════════════

class TestObjectionRecord:
    def test_new_creates_with_id_prefix(self):
        obj = ObjectionRecord.new(ObjectionCategory.PRICE, "Muito caro")
        assert obj.id.startswith("obj_")

    def test_new_defaults_resolved_false(self):
        obj = ObjectionRecord.new(ObjectionCategory.PRICE, "Muito caro")
        assert obj.resolved is False
        assert obj.resolved_at is None

    def test_resolve_sets_resolved(self):
        obj = ObjectionRecord.new(ObjectionCategory.PRICE, "Muito caro")
        obj.resolve("Oferecemos desconto de 10%")
        assert obj.resolved is True
        assert obj.resolved_at is not None
        assert "T" in obj.resolved_at
        assert obj.response == "Oferecemos desconto de 10%"

    def test_to_dict_from_dict_round_trip(self):
        obj = ObjectionRecord.new(ObjectionCategory.PRICE, "Muito caro", lead_id="lead_abc")
        obj.resolve("Resposta")
        d = obj.to_dict()
        restored = ObjectionRecord.from_dict(d)
        assert restored.id == obj.id
        assert restored.resolved is True
        assert restored.response == "Resposta"


# ═══════════════════════════════════════════════════════════════
# ProposalRecord
# ═══════════════════════════════════════════════════════════════

class TestProposalRecord:
    def test_new_creates_with_id_prefix(self):
        prop = ProposalRecord.new("growth")
        assert prop.id.startswith("prop_")

    def test_new_defaults_to_draft(self):
        prop = ProposalRecord.new("growth")
        assert prop.status == ProposalStatus.DRAFT
        assert prop.approval_required is True

    def test_rejects_invalid_package(self):
        with pytest.raises(ValueError, match="Invalid package"):
            ProposalRecord.new("ultimate")

    def test_prices(self):
        assert ProposalRecord.new("starter").value_brl == 350
        assert ProposalRecord.new("growth").value_brl == 990
        assert ProposalRecord.new("premium").value_brl == 1200

    def test_is_sent(self):
        prop = ProposalRecord.new("growth")
        assert prop.is_sent is False
        prop.status = ProposalStatus.SENT
        assert prop.is_sent is True
        prop.status = ProposalStatus.ACCEPTED
        assert prop.is_sent is True

    def test_to_dict_from_dict_round_trip(self):
        prop = ProposalRecord.new("growth", lead_id="lead_abc",
                                  content_summary="Pacote Growth 3 collabs")
        d = prop.to_dict()
        restored = ProposalRecord.from_dict(d)
        assert restored.id == prop.id
        assert restored.package == "growth"
        assert restored.content_summary == "Pacote Growth 3 collabs"


# ═══════════════════════════════════════════════════════════════
# FollowUpTask
# ═══════════════════════════════════════════════════════════════

class TestFollowUpTask:
    def test_new_creates_with_id_prefix(self):
        fup = FollowUpTask.new("Ligar amanha", "2026-12-01T10:00:00Z")
        assert fup.id.startswith("fup_")

    def test_new_defaults_to_pending(self):
        fup = FollowUpTask.new("Ligar amanha", "2026-12-01T10:00:00Z")
        assert fup.status == FollowUpStatus.PENDING
        assert fup.completed_at is None

    def test_is_overdue_when_past(self):
        fup = FollowUpTask.new("Tarefa atrasada", "2020-01-01T00:00:00Z")
        assert fup.is_overdue is True

    def test_is_overdue_false_when_completed(self):
        fup = FollowUpTask.new("Tarefa", "2020-01-01T00:00:00Z")
        fup.complete()
        assert fup.is_overdue is False

    def test_complete_sets_status(self):
        fup = FollowUpTask.new("Tarefa", "2026-12-01T10:00:00Z")
        fup.complete("Feito!")
        assert fup.status == FollowUpStatus.COMPLETED
        assert fup.completed_at is not None
        assert fup.notes == "Feito!"

    def test_cancel_sets_status(self):
        fup = FollowUpTask.new("Tarefa", "2026-12-01T10:00:00Z")
        fup.cancel()
        assert fup.status == FollowUpStatus.CANCELLED

    def test_to_dict_from_dict_round_trip(self):
        fup = FollowUpTask.new("Tarefa", "2026-12-01T10:00:00Z", lead_id="lead_abc")
        fup.complete("Ok")
        d = fup.to_dict()
        restored = FollowUpTask.from_dict(d)
        assert restored.id == fup.id
        assert restored.status == FollowUpStatus.COMPLETED
        assert restored.notes == "Ok"


# ═══════════════════════════════════════════════════════════════
# SalesPipeline
# ═══════════════════════════════════════════════════════════════

class TestSalesPipeline:
    def test_new_creates_with_id_prefix(self):
        pipe = SalesPipeline.new("Pipeline Q2", "Pipeline do Q2 2026")
        assert pipe.id.startswith("pipe_")

    def test_empty_pipeline_has_zero_metrics(self):
        pipe = SalesPipeline.new("Vazio", "Sem deals")
        assert pipe.deal_count == 0
        assert pipe.active_count == 0
        assert pipe.total_value == 0
        assert pipe.weighted_value == 0

    def test_total_value_sums_deals(self):
        d1 = _make_deal(package="starter")  # 350
        d2 = _make_deal(package="growth")   # 990
        pipe = SalesPipeline.new("P", "D", deals=[d1, d2])
        assert pipe.total_value == 1340

    def test_weighted_value(self):
        d1 = _make_deal(package="starter")  # 350 * 0.10 = 35
        d2 = _make_deal(package="premium")  # 1200 * 0.10 = 120
        pipe = SalesPipeline.new("P", "D", deals=[d1, d2])
        assert pipe.weighted_value == 155.0

    def test_active_deals_excludes_terminal(self):
        d1 = _make_deal(stage=PipelineStage.PROSPECTING)
        d2 = _make_deal(stage=PipelineStage.CLOSED_WON)
        d3 = _make_deal(stage=PipelineStage.CLOSED_LOST)
        pipe = SalesPipeline.new("P", "D", deals=[d1, d2, d3])
        assert pipe.active_count == 1
        assert len(pipe.active_deals) == 1

    def test_count_by_stage(self):
        d1 = _make_deal(stage=PipelineStage.PROSPECTING)
        d2 = _make_deal(stage=PipelineStage.PROSPECTING)
        d3 = _make_deal(stage=PipelineStage.NEGOTIATION)
        pipe = SalesPipeline.new("P", "D", deals=[d1, d2, d3])
        assert pipe.count_by_stage(PipelineStage.PROSPECTING) == 2
        assert pipe.count_by_stage(PipelineStage.NEGOTIATION) == 1
        assert pipe.count_by_stage(PipelineStage.CLOSED_WON) == 0

    def test_value_by_stage(self):
        d1 = _make_deal(package="starter", stage=PipelineStage.CLOSED_WON)  # 350
        d2 = _make_deal(package="growth", stage=PipelineStage.PROPOSAL)     # 990
        pipe = SalesPipeline.new("P", "D", deals=[d1, d2])
        assert pipe.value_by_stage(PipelineStage.CLOSED_WON) == 350
        assert pipe.value_by_stage(PipelineStage.PROPOSAL) == 990

    def test_to_dict_includes_computed_fields(self):
        d1 = _make_deal(package="growth")
        pipe = SalesPipeline.new("P", "D", deals=[d1])
        d = pipe.to_dict()
        assert d["total_value"] == 990
        assert d["weighted_value"] == 99.0
        assert d["deal_count"] == 1

    def test_to_dict_from_dict_round_trip(self):
        d1 = _make_deal(package="growth")
        pipe = SalesPipeline.new("Pipeline Q2", "Desc", deals=[d1])
        d = pipe.to_dict()
        restored = SalesPipeline.from_dict(d)
        assert restored.id == pipe.id
        assert restored.name == pipe.name
        assert restored.deal_count == 1
        assert isinstance(restored.deals[0], Deal)


# ═══════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════

class TestEnums:
    def test_pipeline_stage_active_stages(self):
        active = PipelineStage.active_stages()
        assert PipelineStage.CLOSED_WON not in active
        assert PipelineStage.CLOSED_LOST not in active
        assert PipelineStage.PROSPECTING in active

    def test_pipeline_stage_terminal_stages(self):
        terminal = PipelineStage.terminal_stages()
        assert terminal == [PipelineStage.CLOSED_WON, PipelineStage.CLOSED_LOST]

    def test_lead_source_values(self):
        assert LeadSource.INSTAGRAM.value == "instagram"
        assert LeadSource.DIRECT_CONTACT.value == "direct_contact"

    def test_objection_category_values(self):
        assert ObjectionCategory.PRICE.value == "price"
        assert ObjectionCategory.BUDGET.value == "budget"
        assert len(ObjectionCategory) == 8


# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

class TestConstants:
    def test_valid_packages(self):
        assert VALID_PACKAGES == frozenset({"starter", "growth", "premium"})
