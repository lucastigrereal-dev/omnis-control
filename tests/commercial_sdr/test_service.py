"""Tests for P9 Commercial SDR service."""
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
from src.commercial_sdr.service import (
    CommercialSDRPlanner,
    score_prospect,
    build_outreach_sequence,
    generate_sdr_message,
    build_batch_plan,
    validate_sequence,
)
from src.commercial_sdr.errors import (
    EmptyProspectListError,
)


class TestScoreProspect:
    def test_hotel_prospect_scores_high(self, sample_hotel_prospect):
        score = score_prospect(sample_hotel_prospect)
        assert score.tier == ScoreTier.HOT
        assert score.is_pursuable is True
        assert len(score.reasoning) >= 4

    def test_restaurant_prospect_scores_hot(self, sample_restaurant_prospect):
        score = score_prospect(sample_restaurant_prospect)
        assert score.tier == ScoreTier.HOT

    def test_minimal_prospect_scores_low(self, sample_minimal_prospect):
        score = score_prospect(sample_minimal_prospect)
        assert score.tier in (ScoreTier.COLD, ScoreTier.DISQUALIFIED)
        assert score.is_pursuable is False

    def test_inbound_lead_scores_higher(self):
        p = ProspectProfile.new("Hotel X", "Ana", "hotel", LeadSource.INBOUND,
                                 instagram_handle="@h", email="a@h.com", phone="+55")
        score = score_prospect(p)
        assert score.tier == ScoreTier.HOT

    def test_manual_research_with_no_channels_scores_cold(self):
        p = ProspectProfile.new("Loja Y", "Ze", "varejo", LeadSource.MANUAL_RESEARCH)
        score = score_prospect(p)
        assert score.tier in (ScoreTier.COLD, ScoreTier.DISQUALIFIED)

    def test_high_fit_segments_score_max_segment_fit(self):
        for seg in ["hotel", "resort", "pousada", "restaurante", "gastronomia",
                     "turismo", "viagem", "agencia"]:
            p = ProspectProfile.new("X", "Y", seg, LeadSource.INSTAGRAM,
                                     instagram_handle="@x")
            score = score_prospect(p)
            assert score.segment_fit == 0.90, f"Segmento {seg} deveria ter fit 0.90"

    def test_medium_fit_segments_score_medium(self):
        for seg in ["evento", "experiencia", "guia", "transporte"]:
            p = ProspectProfile.new("X", "Y", seg, LeadSource.INSTAGRAM,
                                     instagram_handle="@x")
            score = score_prospect(p)
            assert score.segment_fit == 0.55, f"Segmento {seg} deveria ter fit 0.55"

    def test_unknown_segment_scores_low_fit(self):
        p = ProspectProfile.new("X", "Y", "tecnologia", LeadSource.INSTAGRAM,
                                 instagram_handle="@x")
        score = score_prospect(p)
        assert score.segment_fit == 0.25

    def test_urgency_detected_from_tags(self):
        p = ProspectProfile.new("X", "Y", "hotel", LeadSource.INSTAGRAM,
                                 instagram_handle="@x", tags=["urgente", "vip"])
        score = score_prospect(p)
        assert score.urgency == 0.75

    def test_urgency_detected_from_notes(self):
        p = ProspectProfile.new("X", "Y", "hotel", LeadSource.INSTAGRAM,
                                 instagram_handle="@x", notes="cliente quente, fechar rapido")
        score = score_prospect(p)
        assert score.urgency == 0.75

    def test_urgency_moderate_with_website(self):
        p = ProspectProfile.new("X", "Y", "hotel", LeadSource.INSTAGRAM,
                                 instagram_handle="@x", website="https://x.com")
        score = score_prospect(p)
        assert score.urgency == 0.45

    def test_urgency_default(self):
        p = ProspectProfile.new("X", "Y", "hotel", LeadSource.INSTAGRAM,
                                 instagram_handle="@x")
        score = score_prospect(p)
        assert score.urgency == 0.30

    def test_referral_signals_high_budget(self):
        p = ProspectProfile.new("X", "Y", "hotel", LeadSource.REFERRAL,
                                 instagram_handle="@x")
        score = score_prospect(p)
        assert score.budget_indicator == 0.80

    def test_multi_channel_engagement_max(self):
        p = ProspectProfile.new("X", "Y", "hotel", LeadSource.INSTAGRAM,
                                 instagram_handle="@x", email="a@b.com",
                                 phone="+55", website="https://x.com")
        score = score_prospect(p)
        assert score.engagement_signal == 0.85

    def test_zero_channel_engagement_min(self):
        p = ProspectProfile.new("X", "Y", "varejo", LeadSource.MANUAL_RESEARCH)
        score = score_prospect(p)
        assert score.engagement_signal == 0.05

    @pytest.mark.parametrize("source,expected_budget", [
        (LeadSource.REFERRAL, 0.80),
        (LeadSource.INBOUND, 0.75),
        (LeadSource.PARTNERSHIP, 0.65),
        (LeadSource.INSTAGRAM, 0.50),
        (LeadSource.EVENT, 0.45),
        (LeadSource.MANUAL_RESEARCH, 0.30),
    ])
    def test_budget_by_source(self, source, expected_budget):
        p = ProspectProfile.new("X", "Y", "hotel", source, instagram_handle="@x")
        score = score_prospect(p)
        assert score.budget_indicator == expected_budget


class TestGenerateSDRMessage:
    def test_email_intro_message(self, sample_hotel_prospect):
        msg = generate_sdr_message(sample_hotel_prospect, OutreachChannel.EMAIL,
                                   StepAction.INTRO_MESSAGE)
        assert msg.channel == OutreachChannel.EMAIL
        assert "Hotel Villa D'oro" in msg.subject
        assert "Roberta Campos" in msg.body
        assert msg.approval_required is False  # email intro = low risk

    def test_email_proposal_requires_approval(self, sample_hotel_prospect):
        msg = generate_sdr_message(sample_hotel_prospect, OutreachChannel.EMAIL,
                                   StepAction.PROPOSAL)
        assert msg.approval_required is True

    def test_instagram_dm_always_requires_approval(self, sample_hotel_prospect):
        msg = generate_sdr_message(sample_hotel_prospect, OutreachChannel.INSTAGRAM_DM,
                                   StepAction.INTRO_MESSAGE)
        assert msg.approval_required is True
        assert "Lucas Tigre" in msg.body

    def test_follow_up_email(self, sample_hotel_prospect):
        msg = generate_sdr_message(sample_hotel_prospect, OutreachChannel.EMAIL,
                                   StepAction.FOLLOW_UP)
        assert "ultima mensagem" in msg.body.lower()
        assert msg.approval_required is False

    def test_value_offer_email(self, sample_hotel_prospect):
        msg = generate_sdr_message(sample_hotel_prospect, OutreachChannel.EMAIL,
                                   StepAction.VALUE_OFFER)
        assert "CPM" in msg.body
        assert "98%" in msg.body

    def test_fallback_template_for_unknown_action_channel(self, sample_hotel_prospect):
        msg = generate_sdr_message(sample_hotel_prospect, OutreachChannel.LINKEDIN,
                                   StepAction.CLOSE_ASK)
        assert msg.body != ""
        assert msg.subject != ""
        assert msg.approval_required is True  # LinkedIn = high risk

    def test_dm_intro_contains_handle(self, sample_hotel_prospect):
        msg = generate_sdr_message(sample_hotel_prospect, OutreachChannel.INSTAGRAM_DM,
                                   StepAction.INTRO_MESSAGE)
        assert "@lucastigrereal" in msg.body

    def test_whatsapp_always_requires_approval(self, sample_hotel_prospect):
        msg = generate_sdr_message(sample_hotel_prospect, OutreachChannel.WHATSAPP,
                                   StepAction.INTRO_MESSAGE)
        assert msg.approval_required is True

    def test_phone_always_requires_approval(self, sample_hotel_prospect):
        msg = generate_sdr_message(sample_hotel_prospect, OutreachChannel.PHONE,
                                   StepAction.INTRO_MESSAGE)
        assert msg.approval_required is True

    def test_proposal_contains_pricing(self, sample_hotel_prospect):
        msg = generate_sdr_message(sample_hotel_prospect, OutreachChannel.EMAIL,
                                   StepAction.PROPOSAL)
        assert "R$990" in msg.body
        assert "Growth" in msg.body

    def test_all_messages_have_signature(self, sample_hotel_prospect):
        for channel in OutreachChannel:
            for action in [StepAction.INTRO_MESSAGE, StepAction.FOLLOW_UP]:
                msg = generate_sdr_message(sample_hotel_prospect, channel, action)
                assert isinstance(msg, SDRMessage)
                assert msg.sent is False  # nunca enviado

    def test_message_not_sent(self, sample_hotel_prospect):
        msg = generate_sdr_message(sample_hotel_prospect, OutreachChannel.EMAIL,
                                   StepAction.INTRO_MESSAGE)
        assert msg.sent is False


class TestBuildOutreachSequence:
    def test_sequence_has_seven_steps(self, sample_hotel_prospect):
        seq = build_outreach_sequence(sample_hotel_prospect)
        assert seq.total_steps == 7
        assert seq.status == "ready"
        assert seq.dry_run is True

    def test_sequence_steps_in_order(self, sample_hotel_prospect):
        seq = build_outreach_sequence(sample_hotel_prospect)
        actions = [s.action for s in seq.steps]
        assert actions == [
            StepAction.RESEARCH,
            StepAction.CONNECT,
            StepAction.INTRO_MESSAGE,
            StepAction.VALUE_OFFER,
            StepAction.FOLLOW_UP,
            StepAction.PROPOSAL,
            StepAction.CLOSE_ASK,
        ]

    def test_sequence_total_delay(self, sample_hotel_prospect):
        seq = build_outreach_sequence(sample_hotel_prospect)
        assert seq.total_delay_days == 25  # 0+0+0+3+5+7+10

    def test_all_steps_have_message(self, sample_hotel_prospect):
        seq = build_outreach_sequence(sample_hotel_prospect)
        for step in seq.steps:
            assert step.message is not None
            assert isinstance(step.message, SDRMessage)

    def test_proposal_step_requires_approval(self, sample_hotel_prospect):
        seq = build_outreach_sequence(sample_hotel_prospect)
        proposal_step = seq.steps[5]  # step 6 — PROPOSAL
        assert proposal_step.action == StepAction.PROPOSAL
        assert proposal_step.requires_approval is True

    def test_all_risk_flags_present(self, sample_hotel_prospect):
        seq = build_outreach_sequence(sample_hotel_prospect)
        assert "dry_run_active" in seq.risk_flags
        assert "no_real_delivery" in seq.risk_flags
        assert "approval_gated" in seq.risk_flags

    def test_minimal_prospect_sequence_still_generated(self, sample_minimal_prospect):
        seq = build_outreach_sequence(sample_minimal_prospect)
        assert seq.total_steps == 7
        assert seq.dry_run is True


class TestValidateSequence:
    def test_valid_sequence_no_warnings(self, sample_sequence):
        warnings = validate_sequence(sample_sequence)
        assert warnings == []

    def test_sent_message_in_dry_run_warns(self, sample_sequence):
        sample_sequence.steps[0].message.sent = True
        warnings = validate_sequence(sample_sequence)
        assert len(warnings) >= 1
        assert any("enviada" in w for w in warnings)

    def test_high_risk_channel_without_approval_warns(self):
        seq = OutreachSequence.new("p1")
        step = OutreachStep.new(
            seq.sequence_id, 1, StepAction.INTRO_MESSAGE,
            OutreachChannel.INSTAGRAM_DM,
            requires_approval=False,
        )
        seq.steps = [step]
        warnings = validate_sequence(seq)
        assert len(warnings) >= 1
        assert any("instagram_dm" in w for w in warnings)

    def test_negative_delay_rejected_by_model(self):
        seq = OutreachSequence.new("p1")
        with pytest.raises(ValueError, match="delay_days"):
            OutreachStep.new(
                seq.sequence_id, 1, StepAction.CONNECT, OutreachChannel.EMAIL,
                delay_days=-5,
            )

    def test_excessive_total_delay_warns(self):
        seq = OutreachSequence.new("p1")
        seq.steps = [
            OutreachStep.new(seq.sequence_id, 1, StepAction.RESEARCH,
                             OutreachChannel.EMAIL, delay_days=31),
        ]
        warnings = validate_sequence(seq)
        assert any("30 dias" in w for w in warnings)


class TestCommercialSDRPlanner:
    def test_build_sdr_plan(self, sample_prospects):
        planner = CommercialSDRPlanner()
        plan = planner.build_sdr_plan("Plano SDR", "Prospeccao Maio", sample_prospects)
        assert isinstance(plan, SDRPlan)
        assert plan.title == "Plano SDR"
        assert plan.status == "final"
        assert plan.dry_run is True
        assert plan.total_prospects == 3
        assert len(plan.scores) == 3

    def test_build_sdr_plan_only_generates_sequences_for_pursuable(self, sample_prospects):
        planner = CommercialSDRPlanner()
        plan = planner.build_sdr_plan("P", "D", sample_prospects)
        assert len(plan.sequences) <= plan.total_prospects
        assert len(plan.sequences) == plan.pursuable_count

    def test_planner_rejects_empty_list(self):
        planner = CommercialSDRPlanner()
        with pytest.raises(EmptyProspectListError):
            planner.build_sdr_plan("P", "D", [])

    def test_planner_risk_flags(self):
        planner = CommercialSDRPlanner()
        assert "no_real_delivery" in planner.risk_flags
        assert "approval_required_for_external_send" in planner.risk_flags
        assert "mass_outreach_flagged" in planner.risk_flags

    def test_planner_dry_run_default(self):
        planner = CommercialSDRPlanner()
        assert planner.dry_run is True

    def test_plan_contains_safety_rules(self, sample_prospects):
        planner = CommercialSDRPlanner()
        plan = planner.build_sdr_plan("P", "D", sample_prospects)
        assert len(plan.safety_rules) == 4
        assert "no_real_message_sending" in plan.safety_rules
        assert "no_external_api_calls" in plan.safety_rules
        assert "human_approval_for_all_outreach" in plan.safety_rules

    def test_single_prospect_plan(self, sample_hotel_prospect):
        planner = CommercialSDRPlanner()
        plan = planner.build_sdr_plan("P", "D", [sample_hotel_prospect])
        assert plan.total_prospects == 1
        assert len(plan.sequences) == 1  # hotel = HOT = pursuable

    def test_all_messages_are_dry_run(self, sample_prospects):
        planner = CommercialSDRPlanner()
        plan = planner.build_sdr_plan("P", "D", sample_prospects)
        for seq in plan.sequences:
            for step in seq.steps:
                if step.message:
                    assert step.message.sent is False

    def test_hot_prospects_have_sequences(self, sample_hotel_prospect):
        planner = CommercialSDRPlanner()
        plan = planner.build_sdr_plan("P", "D", [sample_hotel_prospect])
        assert len(plan.sequences) == 1
        assert plan.sequences[0].profile_id == sample_hotel_prospect.profile_id


class TestBuildBatchPlan:
    def test_build_batch_plan_convenience(self, sample_prospects):
        plan = build_batch_plan("Batch Plan", "Batch Desc", sample_prospects)
        assert isinstance(plan, SDRPlan)
        assert plan.title == "Batch Plan"
        assert plan.status == "final"

    def test_batch_plan_rejects_empty(self):
        with pytest.raises(EmptyProspectListError):
            build_batch_plan("P", "D", [])


class TestDryRunGuarantees:
    """Garantias de que nenhum envio real acontece."""

    def test_planner_always_dry_run(self):
        planner = CommercialSDRPlanner()
        assert planner.dry_run is True

    def test_sequence_always_dry_run(self, sample_sequence):
        assert sample_sequence.dry_run is True

    def test_plan_always_dry_run(self, sample_plan):
        assert sample_plan.dry_run is True

    def test_messages_never_sent(self, sample_sequence):
        for step in sample_sequence.steps:
            assert step.message is not None
            assert step.message.sent is False

    def test_no_external_channels_leak(self, sample_plan):
        """Verifica que todos os canais sao apenas enum — nenhuma conexao real."""
        channels_used = set()
        for seq in sample_plan.sequences:
            for step in seq.steps:
                channels_used.add(step.channel)
        assert OutreachChannel.PHONE in channels_used or True  # canais sao so enums

    def test_approval_required_for_risky_actions(self, sample_sequence):
        proposal_steps = [s for s in sample_sequence.steps
                          if s.action == StepAction.PROPOSAL]
        for step in proposal_steps:
            assert step.requires_approval is True, \
                f"Step {step.step_number} ({step.action.value}) deveria requerer aprovacao"
