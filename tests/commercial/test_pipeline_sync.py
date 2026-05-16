"""Tests for W127 — Commercial Pipeline Sync Bridge."""
from __future__ import annotations

import pytest

from src.sales.leads import Lead
from src.commercial.hotel_lead import HotelLead
from src.commercial.lead_qualifier import (
    BANTResult, LeadQualifier,
    QUALIFIED, NURTURE, LOW_FIT, DISQUALIFIED, MISSING_INFO,
)
from src.commercial.package_matcher import PackageMatcher, PackageMatch
from src.commercial.proposal_brief import ProposalBriefBuilder, ProposalBrief
from src.commercial.pipeline_sync import (
    PipelineSyncEntry,
    PipelineSyncBridge,
    SyncStage,
    STAGE_ORDER,
    _suggest_stage,
    _generate_meeting_brief,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_strong_lead() -> HotelLead:
    base = Lead(
        lead_id="l1", name="Resort Paradiso", company="Paradiso Hoteis Ltda",
        contact_channel="whatsapp", source="indicacao", segment="hotel",
        interest="pacote", tags=["resort", "praia", "oportunidade"],
        score=90,
    )
    return HotelLead(
        hotel_lead_id="h1", base_lead=base, hotel_name="Resort Paradiso",
        city="Porto de Galinhas", state="PE", region="nordeste",
        hotel_tier="Premium", niche="resort",
        room_count_placeholder=120, average_daily_rate_placeholder=850.0,
        decision_maker_name="Carlos Mendes", decision_maker_role="Proprietario",
        fit_score=90, priority_tier="hot",
    )


def _make_medium_lead() -> HotelLead:
    base = Lead(
        lead_id="l2", name="Pousada Brisa", company="Brisa Turismo Ltda",
        contact_channel="email", source="instagram", segment="hotel",
        interest="collab", tags=["pousada", "praia"],
        score=60,
    )
    return HotelLead(
        hotel_lead_id="h2", base_lead=base, hotel_name="Pousada Brisa",
        city="Maragogi", state="AL", region="nordeste",
        hotel_tier="Growth", niche="pousada",
        room_count_placeholder=25, average_daily_rate_placeholder=350.0,
        decision_maker_name="Ana Souza", decision_maker_role="Gerente",
        fit_score=60, priority_tier="warm",
    )


def _make_weak_lead() -> HotelLead:
    base = Lead(
        lead_id="l3", name="Hostel Centro", company="Centro Hospedagem Ltda",
        contact_channel="", source="prospeccao", segment="hotel",
        interest="", tags=["hostel"],
        score=10,
    )
    return HotelLead(
        hotel_lead_id="h3", base_lead=base, hotel_name="Hostel Centro",
        city="Sao Paulo", state="SP", region="sudeste",
        hotel_tier="Starter", niche="hostel",
        room_count_placeholder=10, average_daily_rate_placeholder=80.0,
        fit_score=10, priority_tier="cold",
    )


# ── Stage Mapping Tests ────────────────────────────────────────────────────

class TestSuggestStage:
    def test_disqualified_maps_to_arquivado(self):
        assert _suggest_stage(DISQUALIFIED, False, False, "cold") == SyncStage.ARQUIVADO

    def test_missing_info_maps_to_novo(self):
        assert _suggest_stage(MISSING_INFO, False, False, "cold") == SyncStage.NOVO

    def test_low_fit_maps_to_novo(self):
        assert _suggest_stage(LOW_FIT, False, False, "cold") == SyncStage.NOVO

    def test_nurture_hot_maps_to_qualificado(self):
        assert _suggest_stage(NURTURE, False, False, "hot") == SyncStage.QUALIFICADO

    def test_nurture_cold_maps_to_novo(self):
        assert _suggest_stage(NURTURE, False, False, "cold") == SyncStage.NOVO

    def test_qualified_no_package_maps_to_qualificado(self):
        assert _suggest_stage(QUALIFIED, False, False, "hot") == SyncStage.QUALIFICADO

    def test_qualified_with_package_maps_to_proposta(self):
        assert _suggest_stage(QUALIFIED, True, False, "hot") == SyncStage.PROPOSTA

    def test_with_proposal_maps_to_negociacao(self):
        assert _suggest_stage(QUALIFIED, True, True, "hot") == SyncStage.NEGOCIACAO

    def test_nurture_with_proposal_maps_to_negociacao(self):
        assert _suggest_stage(NURTURE, True, True, "warm") == SyncStage.NEGOCIACAO


# ── PipelineSyncEntry Tests ─────────────────────────────────────────────────

class TestPipelineSyncEntry:
    def test_create_entry(self):
        entry = PipelineSyncEntry(
            sync_id="s1", hotel_lead_id="h1", hotel_name="Hotel Test",
            priority_tier="hot", fit_score=90, bant_tier=QUALIFIED, bant_score=85,
            recommended_package="Premium", has_package=True, has_proposal=True,
            suggested_stage=SyncStage.NEGOCIACAO,
        )
        assert entry.hotel_name == "Hotel Test"
        assert entry.is_actionable is True
        assert entry.stage_index == 3  # negociacao is index 3

    def test_entry_not_actionable(self):
        entry = PipelineSyncEntry(
            sync_id="s2", hotel_lead_id="h2", hotel_name="Bad",
            bant_tier=DISQUALIFIED, suggested_stage=SyncStage.ARQUIVADO,
        )
        assert entry.is_actionable is False

    def test_stage_index_unknown(self):
        entry = PipelineSyncEntry(
            sync_id="s3", hotel_lead_id="h3", hotel_name="X",
            suggested_stage="unknown",
        )
        assert entry.stage_index == -1

    def test_to_dict_roundtrip(self):
        entry = PipelineSyncEntry(
            sync_id="s4", hotel_lead_id="h4", hotel_name="Roundtrip",
            priority_tier="warm", fit_score=70, bant_tier=NURTURE, bant_score=55,
            recommended_package="Growth", has_package=True, has_proposal=False,
            suggested_stage=SyncStage.PROPOSTA,
            meeting_brief="# Meeting Brief",
            bant_risks=["Risk 1"], bant_reasons=["Reason 1"],
            package_rationale=["Good fit"],
            recommended_channels=["email", "whatsapp"],
            objection_count=6, next_action="Enviar proposta",
        )
        d = entry.to_dict()
        restored = PipelineSyncEntry.from_dict(d)
        assert restored.sync_id == "s4"
        assert restored.bant_tier == NURTURE
        assert restored.bant_risks == ["Risk 1"]
        assert restored.package_rationale == ["Good fit"]
        assert restored.recommended_channels == ["email", "whatsapp"]
        assert restored.meeting_brief == "# Meeting Brief"

    def test_from_dict_empty_defaults(self):
        d = {"sync_id": "s5", "hotel_lead_id": "h5", "hotel_name": "Minimal"}
        entry = PipelineSyncEntry.from_dict(d)
        assert entry.bant_risks == []
        assert entry.package_rationale == []
        assert entry.suggested_stage == SyncStage.NOVO
        assert entry.dry_run is True


# ── PipelineSyncBridge Tests ────────────────────────────────────────────────

class TestPipelineSyncBridge:
    def test_sync_from_qualified_lead_full_pipeline(self):
        """Full flow: HotelLead → BANT → PackageMatch → ProposalBrief → sync."""
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        matcher = PackageMatcher()
        builder = ProposalBriefBuilder()

        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        pb = builder.build(pm, br, hl)

        entry = bridge.sync(hl, br, pm, pb)

        assert entry.hotel_name == "Resort Paradiso"
        assert entry.bant_tier == QUALIFIED
        assert entry.has_package is True
        assert entry.has_proposal is True
        assert entry.suggested_stage == SyncStage.NEGOCIACAO
        assert entry.is_actionable is True
        assert entry.meeting_brief != ""
        assert entry.dry_run is True

    def test_sync_qualified_no_proposal(self):
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        matcher = PackageMatcher()

        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)

        entry = bridge.sync(hl, br, pm, None)
        assert entry.suggested_stage == SyncStage.PROPOSTA
        assert entry.has_package is True
        assert entry.has_proposal is False

    def test_sync_disqualified_no_package(self):
        bridge = PipelineSyncBridge()
        hl = _make_weak_lead()
        br = BANTResult(
            qualifier_id="q1", hotel_lead_id="h3", hotel_name="Hostel",
            budget_score=5, authority_score=2, need_score=5, timing_score=0,
            total_score=12, qualification_tier=DISQUALIFIED,
        )
        entry = bridge.sync(hl, br, None, None)
        assert entry.suggested_stage == SyncStage.ARQUIVADO
        assert entry.is_actionable is False
        assert entry.has_package is False
        assert entry.has_proposal is False

    def test_sync_nurture_no_package(self):
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        hl = _make_medium_lead()
        br = q.qualify(hl)

        # Don't pass package match — just BANT
        entry = bridge.sync(hl, br, None, None)
        assert entry.suggested_stage in (SyncStage.QUALIFICADO, SyncStage.NOVO)
        assert entry.bant_tier in (NURTURE, QUALIFIED)

    def test_sync_stage_correct_for_all_helpers(self):
        bridge = PipelineSyncBridge()
        q = LeadQualifier()

        for hl in [_make_strong_lead(), _make_medium_lead(), _make_weak_lead()]:
            br = q.qualify(hl)
            entry = bridge.sync(hl, br, None, None)
            assert entry.suggested_stage in (
                SyncStage.NOVO, SyncStage.QUALIFICADO, SyncStage.PROPOSTA,
                SyncStage.NEGOCIACAO, SyncStage.ARQUIVADO,
            )

    def test_sync_batch_multiple_leads(self):
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        matcher = PackageMatcher()

        leads = [_make_strong_lead(), _make_medium_lead(), _make_weak_lead()]
        bant_results = [q.qualify(hl) for hl in leads]
        pkg_matches = [matcher.match(hl, br) for hl, br in zip(leads, bant_results)]

        entries = bridge.sync_batch(leads, bant_results, pkg_matches)
        assert len(entries) == 3
        # Strong lead should be first (actionable, highest stage)
        assert entries[0].is_actionable

    def test_sync_batch_sorted_correctly(self):
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        matcher = PackageMatcher()

        leads = [_make_weak_lead(), _make_strong_lead(), _make_medium_lead()]
        bant_results = [q.qualify(hl) for hl in leads]
        pkg_matches = [matcher.match(hl, br) for hl, br in zip(leads, bant_results)]

        entries = bridge.sync_batch(leads, bant_results, pkg_matches)
        # First entry should be actionable (strong lead)
        assert entries[0].is_actionable
        # Last should be non-actionable (weak lead)
        assert not entries[-1].is_actionable

    def test_sync_batch_with_proposals(self):
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        matcher = PackageMatcher()
        builder = ProposalBriefBuilder()

        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        pb = builder.build(pm, br, hl)

        entries = bridge.sync_batch([hl], [br], [pm], [pb])
        assert len(entries) == 1
        assert entries[0].suggested_stage == SyncStage.NEGOCIACAO
        assert entries[0].has_proposal is True

    def test_sync_from_prospect_list(self):
        from src.commercial.prospect_list import ProspectList

        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        matcher = PackageMatcher()

        pl = ProspectList()
        pl.add(_make_strong_lead())
        pl.add(_make_medium_lead())

        leads = [e.hotel_lead for e in pl.list_all()]
        bant_results = [q.qualify(hl) for hl in leads]
        pkg_matches = [matcher.match(hl, br) for hl, br in zip(leads, bant_results)]

        entries = bridge.sync_from_prospect_list(pl, bant_results, pkg_matches)
        assert len(entries) == 2

    def test_summary_by_stage(self):
        bridge = PipelineSyncBridge()
        entries = [
            PipelineSyncEntry(sync_id="s1", hotel_lead_id="h1", hotel_name="A",
                              suggested_stage=SyncStage.NEGOCIACAO),
            PipelineSyncEntry(sync_id="s2", hotel_lead_id="h2", hotel_name="B",
                              suggested_stage=SyncStage.PROPOSTA),
            PipelineSyncEntry(sync_id="s3", hotel_lead_id="h3", hotel_name="C",
                              suggested_stage=SyncStage.PROPOSTA),
            PipelineSyncEntry(sync_id="s4", hotel_lead_id="h4", hotel_name="D",
                              suggested_stage=SyncStage.ARQUIVADO),
        ]
        summary = bridge.summary_by_stage(entries)
        assert summary[SyncStage.NEGOCIACAO] == 1
        assert summary[SyncStage.PROPOSTA] == 2
        assert summary[SyncStage.ARQUIVADO] == 1

    def test_summary_actionable(self):
        bridge = PipelineSyncBridge()
        entries = [
            PipelineSyncEntry(sync_id="s1", hotel_lead_id="h1", hotel_name="A",
                              suggested_stage=SyncStage.NEGOCIACAO),
            PipelineSyncEntry(sync_id="s2", hotel_lead_id="h2", hotel_name="B",
                              suggested_stage=SyncStage.ARQUIVADO),
        ]
        sa = bridge.summary_actionable(entries)
        assert sa["actionable"] == 1
        assert sa["non_actionable"] == 1
        assert sa["total"] == 2

    def test_export_report(self):
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        matcher = PackageMatcher()

        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        entry = bridge.sync(hl, br, pm)

        report = bridge.export_report([entry])
        assert "Commercial Pipeline Sync Report" in report
        assert "Resort Paradiso" in report
        assert "**dry_run:** True" in report

    def test_dry_run_default(self):
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        entry = bridge.sync(hl, br)
        assert entry.dry_run is True

    def test_deterministic(self):
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        matcher = PackageMatcher()

        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)

        e1 = bridge.sync(hl, br, pm)
        e2 = bridge.sync(hl, br, pm)
        assert e1.suggested_stage == e2.suggested_stage
        assert e1.bant_tier == e2.bant_tier
        assert e1.has_package == e2.has_package

    def test_no_network_no_api(self):
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        entry = bridge.sync(hl, br)
        # All local, no external calls
        assert entry.dry_run is True
        assert isinstance(entry.sync_id, str)

    def test_meeting_brief_contains_sections(self):
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        matcher = PackageMatcher()
        builder = ProposalBriefBuilder()

        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        pb = builder.build(pm, br, hl)

        entry = bridge.sync(hl, br, pm, pb)
        brief = entry.meeting_brief

        assert "SDR Meeting Brief" in brief
        assert "Resort Paradiso" in brief
        assert "Qualificacao BANT" in brief
        assert "Pacote Recomendado" in brief
        assert "Angulo Comercial" in brief
        assert "Talking Points" in brief
        assert "Valor Esperado" in brief
        assert "Canais Recomendados" in brief
        assert "Objecoes Mapeadas" in brief
        assert "Estrategia de Abordagem" in brief

    def test_meeting_brief_no_match(self):
        bridge = PipelineSyncBridge()
        hl = _make_weak_lead()
        br = BANTResult(
            qualifier_id="q1", hotel_lead_id="h3", hotel_name="Hostel",
            budget_score=5, authority_score=2, need_score=5, timing_score=0,
            total_score=12, qualification_tier=DISQUALIFIED,
        )
        entry = bridge.sync(hl, br)
        brief = entry.meeting_brief
        assert "SDR Meeting Brief" in brief
        assert "Hostel Centro" in brief
        assert "Qualificacao BANT" in brief

    def test_sync_with_none_package_and_proposal(self):
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        entry = bridge.sync(hl, br, None, None)
        assert entry.has_package is False
        assert entry.has_proposal is False
        assert entry.meeting_brief != ""

    def test_stage_order_constant(self):
        assert len(STAGE_ORDER) == 5
        assert STAGE_ORDER[0] == SyncStage.NOVO
        assert STAGE_ORDER[-1] == SyncStage.FECHADO

    def test_sync_stage_matches_stage_order(self):
        """All suggested stages should be in STAGE_ORDER or ARQUIVADO."""
        bridge = PipelineSyncBridge()
        q = LeadQualifier()

        for hl in [_make_strong_lead(), _make_medium_lead(), _make_weak_lead()]:
            br = q.qualify(hl)
            entry = bridge.sync(hl, br)
            valid = list(STAGE_ORDER) + [SyncStage.ARQUIVADO]
            assert entry.suggested_stage in valid
