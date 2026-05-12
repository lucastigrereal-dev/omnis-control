"""Tests for P9 Commercial SDR models."""
from __future__ import annotations

import pytest

from src.commercial_sdr.models import (
    ProspectProfile,
    LeadSource,
    OutreachChannel,
    StepAction,
    ScoreTier,
    SDRMessage,
    OutreachStep,
    OutreachSequence,
    OpportunityScore,
    SDRPlan,
)


class TestLeadSource:
    def test_all_sources_exist(self):
        assert len(LeadSource) == 6

    @pytest.mark.parametrize("source", list(LeadSource))
    def test_source_has_value(self, source):
        assert isinstance(source.value, str)
        assert len(source.value) > 0


class TestOutreachChannel:
    def test_all_channels_exist(self):
        assert len(OutreachChannel) == 5

    @pytest.mark.parametrize("channel", list(OutreachChannel))
    def test_channel_has_value(self, channel):
        assert isinstance(channel.value, str)


class TestStepAction:
    def test_all_actions_exist(self):
        assert len(StepAction) == 7


class TestScoreTier:
    def test_all_tiers_exist(self):
        assert len(ScoreTier) == 4


class TestProspectProfile:
    def test_new_creates_profile(self):
        p = ProspectProfile.new(
            "Hotel Teste", "Maria", "hotel", LeadSource.INSTAGRAM,
            instagram_handle="@hotelteste",
        )
        assert p.profile_id.startswith("prospect_")
        assert len(p.profile_id) == 17  # "prospect_" + 8 hex
        assert p.company_name == "Hotel Teste"
        assert p.contact_name == "Maria"
        assert p.segment == "hotel"
        assert p.source == LeadSource.INSTAGRAM
        assert p.instagram_handle == "@hotelteste"
        assert p.email is None
        assert p.phone is None
        assert p.tags == []

    def test_new_full_profile(self):
        p = ProspectProfile.new(
            "Hotel X", "Joao", "resort", LeadSource.REFERRAL,
            instagram_handle="@hotelx",
            email="joao@hotelx.com",
            phone="+55 84 99999",
            website="https://hotelx.com",
            location="Natal-RN",
            notes="Cliente potencial",
            tags=["premium", "resort"],
        )
        assert p.email == "joao@hotelx.com"
        assert p.phone == "+55 84 99999"
        assert p.website == "https://hotelx.com"
        assert p.location == "Natal-RN"
        assert p.notes == "Cliente potencial"
        assert p.tags == ["premium", "resort"]
        assert p.has_instagram is True
        assert p.has_email is True
        assert p.has_phone is True

    def test_new_minimal_prospect(self):
        p = ProspectProfile.new(
            "Loja X", "Ana", "varejo", LeadSource.MANUAL_RESEARCH,
        )
        assert p.instagram_handle is None
        assert p.email is None
        assert p.phone is None
        assert p.website is None
        assert p.location == ""
        assert p.has_instagram is False
        assert p.has_email is False
        assert p.has_phone is False

    def test_new_rejects_empty_company(self):
        with pytest.raises(ValueError, match="company_name"):
            ProspectProfile.new("", "Joao", "hotel", LeadSource.INSTAGRAM)

    def test_new_rejects_whitespace_company(self):
        with pytest.raises(ValueError, match="company_name"):
            ProspectProfile.new("   ", "Joao", "hotel", LeadSource.INSTAGRAM)

    def test_new_rejects_empty_contact(self):
        with pytest.raises(ValueError, match="contact_name"):
            ProspectProfile.new("Hotel", "", "hotel", LeadSource.INSTAGRAM)

    def test_strips_whitespace(self):
        p = ProspectProfile.new(
            "  Hotel Spa  ", "  Carlos  ", "hotel", LeadSource.INBOUND,
            instagram_handle="  @hotelspa  ",
            email="  carlos@spa.com  ",
        )
        assert p.company_name == "Hotel Spa"
        assert p.contact_name == "Carlos"
        assert p.instagram_handle == "@hotelspa"
        assert p.email == "carlos@spa.com"

    def test_round_trip_dict(self):
        p = ProspectProfile.new(
            "Hotel Z", "Zeca", "pousada", LeadSource.EVENT,
            instagram_handle="@hotelz",
            email="zeca@hotelz.com",
            tags=["a", "b"],
        )
        d = p.to_dict()
        p2 = ProspectProfile.from_dict(d)
        assert p2.profile_id == p.profile_id
        assert p2.company_name == p.company_name
        assert p2.source == p.source
        assert p2.instagram_handle == p.instagram_handle
        assert p2.email == p.email
        assert p2.tags == p.tags

    def test_from_dict_handles_string_source(self):
        d = {
            "profile_id": "prospect_abc12345",
            "company_name": "Hotel",
            "contact_name": "Ana",
            "segment": "hotel",
            "source": "referral",
        }
        p = ProspectProfile.from_dict(d)
        assert p.source == LeadSource.REFERRAL


class TestSDRMessage:
    def test_new_creates_message(self):
        m = SDRMessage.new(
            "prospect_abc", OutreachChannel.EMAIL,
            "Assunto", "Corpo da mensagem",
        )
        assert m.message_id.startswith("msg_")
        assert m.channel == OutreachChannel.EMAIL
        assert m.subject == "Assunto"
        assert m.body == "Corpo da mensagem"
        assert m.approval_required is True
        assert m.sent is False

    def test_new_without_approval(self):
        m = SDRMessage.new(
            "p1", OutreachChannel.EMAIL, "S", "B", approval_required=False,
        )
        assert m.approval_required is False

    def test_new_with_cta(self):
        m = SDRMessage.new(
            "p1", OutreachChannel.EMAIL, "S", "Body", call_to_action="Clique aqui",
        )
        assert m.call_to_action == "Clique aqui"

    def test_new_rejects_empty_body(self):
        with pytest.raises(ValueError, match="body"):
            SDRMessage.new("p1", OutreachChannel.EMAIL, "S", "")

    def test_round_trip_dict(self):
        m = SDRMessage.new(
            "p1", OutreachChannel.EMAIL, "Assunto", "Corpo",
            call_to_action="CTA", approval_required=True,
        )
        d = m.to_dict()
        m2 = SDRMessage.from_dict(d)
        assert m2.message_id == m.message_id
        assert m2.channel == m.channel
        assert m2.subject == m.subject
        assert m2.body == m.body
        assert m2.call_to_action == m.call_to_action
        assert m2.approval_required == m.approval_required


class TestOutreachStep:
    def test_new_creates_step(self):
        msg = SDRMessage.new("p1", OutreachChannel.EMAIL, "S", "Body")
        s = OutreachStep.new(
            "seq_abc", 1, StepAction.INTRO_MESSAGE, OutreachChannel.EMAIL,
            message=msg, delay_days=3,
        )
        assert s.step_id.startswith("step_")
        assert s.step_number == 1
        assert s.action == StepAction.INTRO_MESSAGE
        assert s.channel == OutreachChannel.EMAIL
        assert s.message is msg
        assert s.delay_days == 3
        assert s.requires_approval is True
        assert s.completed is False

    def test_new_without_message(self):
        s = OutreachStep.new(
            "seq_x", 2, StepAction.RESEARCH, OutreachChannel.EMAIL,
        )
        assert s.message is None
        assert s.requires_approval is True

    def test_new_rejects_step_zero(self):
        with pytest.raises(ValueError, match="step_number"):
            OutreachStep.new("s", 0, StepAction.CONNECT, OutreachChannel.EMAIL)

    def test_new_rejects_negative_step(self):
        with pytest.raises(ValueError, match="step_number"):
            OutreachStep.new("s", -1, StepAction.CONNECT, OutreachChannel.EMAIL)

    def test_new_rejects_negative_delay(self):
        with pytest.raises(ValueError, match="delay_days"):
            OutreachStep.new("s", 1, StepAction.CONNECT, OutreachChannel.EMAIL, delay_days=-1)

    def test_round_trip_dict(self):
        msg = SDRMessage.new("p1", OutreachChannel.EMAIL, "S", "Body", "CTA")
        s = OutreachStep.new(
            "seq_x", 3, StepAction.VALUE_OFFER, OutreachChannel.EMAIL,
            message=msg, delay_days=5, notes="teste",
        )
        d = s.to_dict()
        s2 = OutreachStep.from_dict(d)
        assert s2.step_id == s.step_id
        assert s2.step_number == 3
        assert s2.action == StepAction.VALUE_OFFER
        assert s2.message is not None
        assert s2.message.body == "Body"
        assert s2.delay_days == 5
        assert s2.notes == "teste"

    def test_round_trip_dict_without_message(self):
        s = OutreachStep.new("seq_x", 1, StepAction.RESEARCH, OutreachChannel.EMAIL)
        d = s.to_dict()
        s2 = OutreachStep.from_dict(d)
        assert s2.message is None


class TestOutreachSequence:
    def test_new_creates_sequence(self):
        seq = OutreachSequence.new("prospect_abc")
        assert seq.sequence_id.startswith("seq_")
        assert seq.profile_id == "prospect_abc"
        assert seq.steps == []
        assert seq.status == "draft"
        assert seq.dry_run is True
        assert len(seq.risk_flags) == 3

    def test_add_steps(self):
        seq = OutreachSequence.new("p1")
        s1 = OutreachStep.new(seq.sequence_id, 1, StepAction.RESEARCH, OutreachChannel.EMAIL)
        s2 = OutreachStep.new(seq.sequence_id, 2, StepAction.CONNECT, OutreachChannel.EMAIL, delay_days=2)
        seq.steps = [s1, s2]
        assert seq.total_steps == 2
        assert seq.total_delay_days == 2
        assert seq.pending_approvals == 2

    def test_total_delay_days_sums_all(self):
        seq = OutreachSequence.new("p1")
        seq.steps = [
            OutreachStep.new(seq.sequence_id, 1, StepAction.RESEARCH, OutreachChannel.EMAIL, delay_days=0),
            OutreachStep.new(seq.sequence_id, 2, StepAction.CONNECT, OutreachChannel.EMAIL, delay_days=3),
            OutreachStep.new(seq.sequence_id, 3, StepAction.INTRO_MESSAGE, OutreachChannel.EMAIL, delay_days=5),
        ]
        assert seq.total_delay_days == 8

    def test_pending_approvals_counts_correctly(self):
        seq = OutreachSequence.new("p1")
        s1 = OutreachStep.new(seq.sequence_id, 1, StepAction.RESEARCH, OutreachChannel.EMAIL)
        s2 = OutreachStep.new(seq.sequence_id, 2, StepAction.CONNECT, OutreachChannel.EMAIL)
        s2.completed = True
        seq.steps = [s1, s2]
        assert seq.pending_approvals == 1

    def test_round_trip_dict(self):
        seq = OutreachSequence.new("p1")
        s1 = OutreachStep.new(seq.sequence_id, 1, StepAction.RESEARCH, OutreachChannel.EMAIL)
        seq.steps = [s1]
        d = seq.to_dict()
        seq2 = OutreachSequence.from_dict(d)
        assert seq2.sequence_id == seq.sequence_id
        assert seq2.profile_id == seq.profile_id
        assert seq2.total_steps == 1
        assert seq2.dry_run is True
        assert len(seq2.risk_flags) == 3


class TestOpportunityScore:
    def test_new_creates_score(self):
        s = OpportunityScore.new("p1", 0.90, 0.85, 0.80, 0.75)
        assert s.score_id.startswith("score_")
        assert s.segment_fit == 0.90
        assert s.engagement_signal == 0.85
        assert s.budget_indicator == 0.80
        assert s.urgency == 0.75
        assert s.tier == ScoreTier.HOT
        assert s.is_pursuable is True

    def test_hot_threshold(self):
        s = OpportunityScore.new("p1", 0.70, 0.70, 0.70, 0.70)
        assert s.tier == ScoreTier.HOT

    def test_warm_threshold(self):
        s = OpportunityScore.new("p1", 0.50, 0.50, 0.50, 0.50)
        assert s.tier == ScoreTier.WARM
        assert s.is_pursuable is True

    def test_cold_threshold(self):
        s = OpportunityScore.new("p1", 0.20, 0.20, 0.20, 0.20)
        assert s.tier == ScoreTier.COLD
        assert s.is_pursuable is False

    def test_disqualified_threshold(self):
        s = OpportunityScore.new("p1", 0.10, 0.10, 0.10, 0.10)
        assert s.tier == ScoreTier.DISQUALIFIED
        assert s.is_pursuable is False

    def test_composite_formula(self):
        s = OpportunityScore.new("p1", 1.0, 0.0, 0.0, 0.0)
        assert s.composite == 0.35

    def test_new_rejects_negative_segment_fit(self):
        with pytest.raises(ValueError, match="segment_fit"):
            OpportunityScore.new("p1", -0.1, 0.5, 0.5, 0.5)

    def test_new_rejects_over_one(self):
        with pytest.raises(ValueError, match="engagement_signal"):
            OpportunityScore.new("p1", 0.5, 1.1, 0.5, 0.5)

    def test_new_rejects_invalid_budget(self):
        with pytest.raises(ValueError, match="budget_indicator"):
            OpportunityScore.new("p1", 0.5, 0.5, 1.5, 0.5)

    def test_new_rejects_invalid_urgency(self):
        with pytest.raises(ValueError, match="urgency"):
            OpportunityScore.new("p1", 0.5, 0.5, 0.5, -0.5)

    def test_with_reasoning(self):
        s = OpportunityScore.new("p1", 0.9, 0.9, 0.9, 0.9, reasoning=["Alto potencial"])
        assert s.reasoning == ["Alto potencial"]

    def test_round_trip_dict(self):
        s = OpportunityScore.new("p1", 0.88, 0.77, 0.66, 0.55, reasoning=["r1", "r2"])
        d = s.to_dict()
        s2 = OpportunityScore.from_dict(d)
        assert s2.score_id == s.score_id
        assert s2.profile_id == s.profile_id
        assert s2.composite == s.composite
        assert s2.tier == s.tier
        assert s2.reasoning == s.reasoning

    def test_composite_is_rounded(self):
        s = OpportunityScore.new("p1", 0.333, 0.25, 0.25, 0.15)
        assert s.composite == round(0.11655 + 0.0625 + 0.0625 + 0.0225, 4)


class TestSDRPlan:
    def test_new_creates_plan(self):
        p = SDRPlan.new("Plano", "Descricao")
        assert p.plan_id.startswith("plan_")
        assert p.title == "Plano"
        assert p.description == "Descricao"
        assert p.prospects == []
        assert p.scores == []
        assert p.sequences == []
        assert p.status == "draft"
        assert p.dry_run is True
        assert len(p.risk_flags) == 3
        assert len(p.safety_rules) == 4

    def test_add_prospect(self):
        plan = SDRPlan.new("P", "D")
        p = ProspectProfile.new("Hotel", "Ana", "hotel", LeadSource.INSTAGRAM)
        plan.add_prospect(p)
        assert plan.total_prospects == 1

    def test_add_score(self):
        plan = SDRPlan.new("P", "D")
        s = OpportunityScore.new("p1", 0.9, 0.9, 0.9, 0.9)
        plan.add_score(s)
        assert plan.hot_count == 1
        assert plan.warm_count == 0
        assert plan.pursuable_count == 1

    def test_add_sequence(self):
        plan = SDRPlan.new("P", "D")
        seq = OutreachSequence.new("p1")
        plan.add_sequence(seq)
        assert len(plan.sequences) == 1

    def test_counts(self):
        plan = SDRPlan.new("P", "D")
        plan.add_score(OpportunityScore.new("p1", 0.9, 0.9, 0.9, 0.9))
        plan.add_score(OpportunityScore.new("p2", 0.5, 0.5, 0.5, 0.5))
        plan.add_score(OpportunityScore.new("p3", 0.1, 0.1, 0.1, 0.1))
        assert plan.hot_count == 1
        assert plan.warm_count == 1
        assert plan.pursuable_count == 2

    def test_finalize(self):
        plan = SDRPlan.new("P", "D")
        prospect = ProspectProfile.new("H", "A", "hotel", LeadSource.INSTAGRAM)
        plan.add_prospect(prospect)
        plan.finalize()
        assert plan.status == "final"
        assert plan.finalized_at is not None

    def test_strips_title_and_description(self):
        p = SDRPlan.new("  Plano  ", "  Desc  ")
        assert p.title == "Plano"
        assert p.description == "Desc"

    def test_round_trip_dict(self):
        plan = SDRPlan.new("Full Plan", "Full Description")
        prospect = ProspectProfile.new("Hotel", "Joao", "hotel", LeadSource.INSTAGRAM,
                                        instagram_handle="@h")
        plan.add_prospect(prospect)
        score = OpportunityScore.new(prospect.profile_id, 0.9, 0.85, 0.80, 0.75,
                                      reasoning=["top prospect"])
        plan.add_score(score)
        seq = OutreachSequence.new(prospect.profile_id)
        plan.add_sequence(seq)
        plan.finalize()

        d = plan.to_dict()
        plan2 = SDRPlan.from_dict(d)
        assert plan2.plan_id == plan.plan_id
        assert plan2.title == plan.title
        assert plan2.status == "final"
        assert plan2.total_prospects == 1
        assert len(plan2.scores) == 1
        assert len(plan2.sequences) == 1
        assert plan2.dry_run is True
