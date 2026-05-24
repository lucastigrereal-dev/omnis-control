"""Prova REAL — LeadScoringWorkflow com leads reais de hotéis em Natal/RN.

Dívida retroativa da Onda 32: LeadScoringWorkflow foi testado com dados mock
na Onda 16. Este arquivo prova com inputs representativos do negócio real do Lucas.

Hotéis reais de Natal/RN com perfil típico de prospects SDR:
  - Pousada boutique (lead HOT esperado)
  - Hotel urbano sem Instagram (COLD esperado)
  - Resort premium (WARM ou HOT esperado)

Output real impresso via -s para inspeção.
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.commercial_sdr.models import LeadSource, ProspectProfile
from src.workflows.lead_scoring_workflow import LeadScoringWorkflow


# ── prospects reais de Natal/RN ───────────────────────────────────────────────

_BOUTIQUE = ProspectProfile(
    profile_id="P-RN-001",
    company_name="Pousada Vila do Mar",
    contact_name="Fernanda Araújo",
    segment="hotel",
    source=LeadSource.MANUAL_RESEARCH,
    location="Ponta Negra, Natal/RN",
    instagram_handle="@viladomarnatal",
    website="https://viladomarnatal.com.br",
    tags=["boutique", "ponta_negra", "instagramavel"],
    notes="Pousada boutique 4★ em Ponta Negra, ativa no Instagram, 12k seguidores",
)

_URBAN_NO_INSTA = ProspectProfile(
    profile_id="P-RN-002",
    company_name="Hotel Central Natal",
    contact_name="Roberto Lima",
    segment="hotel",
    source=LeadSource.MANUAL_RESEARCH,
    location="Centro, Natal/RN",
    website="https://hotelcentralnatal.com.br",
    tags=["urbano", "sem_instagram"],
    notes="Hotel 3★ no centro, sem presença relevante no Instagram",
)

_RESORT = ProspectProfile(
    profile_id="P-RN-003",
    company_name="Rifoles Praia Hotel",
    contact_name="Camila Santos",
    segment="hotel",
    source=LeadSource.MANUAL_RESEARCH,
    location="Ponta Negra, Natal/RN",
    instagram_handle="@rifoleshotel",
    website="https://rifoles.com.br",
    tags=["resort", "premium", "piscina_borda_infinita"],
    notes="Resort 5★ frente mar em Ponta Negra, 28k seguidores, faz collabs esporádicas",
)


# ── testes de prova real ──────────────────────────────────────────────────────

def test_real_lead_scoring_natal_hotels():
    """PROVA REAL: 3 hotéis de Natal/RN scorados — output impresso para inspeção."""
    sink = MockAkashaSink()
    wf = LeadScoringWorkflow(akasha_sink=sink)
    result = wf.run([_BOUTIQUE, _URBAN_NO_INSTA, _RESORT], dry_run=True)

    print("\n" + "=" * 60)
    print(f"RUN_ID: {result.run_id} | TOTAL: {result.total_scored}")
    print(f"HOT: {result.hot_count} | WARM: {result.warm_count} | COLD: {result.cold_count}")
    print()
    for lead in result.scored_leads:
        print(f"  [{lead.score.tier.value:12s}] score={lead.score.composite:.3f}  {lead.profile.company_name}")
        print(f"           seg_fit={lead.score.segment_fit:.3f}  eng={lead.score.engagement_signal:.3f}")
        if lead.score.reasoning:
            print(f"           reasoning: {', '.join(lead.score.reasoning[:3])}")
    print()
    print(f"TIER DIST: hot={result.hot_count} warm={result.warm_count} cold={result.cold_count}")
    print("=" * 60)

    assert result.total_scored == 3
    assert result.success is True


def test_real_boutique_scores_higher_than_no_instagram():
    """Pousada com Instagram ativo deve superar hotel sem Instagram."""
    sink = MockAkashaSink()
    wf = LeadScoringWorkflow(akasha_sink=sink)
    result = wf.run([_BOUTIQUE, _URBAN_NO_INSTA])

    scores = {lead.profile.profile_id: lead.score.composite for lead in result.scored_leads}
    assert scores["P-RN-001"] > scores["P-RN-002"], (
        f"Boutique com Instagram ({scores['P-RN-001']:.3f}) "
        f"deveria > Hotel sem Instagram ({scores['P-RN-002']:.3f})"
    )


def test_real_ranking_order():
    """Leads aparecem em ordem decrescente de score."""
    sink = MockAkashaSink()
    wf = LeadScoringWorkflow(akasha_sink=sink)
    result = wf.run([_BOUTIQUE, _URBAN_NO_INSTA, _RESORT])

    composites = [lead.score.composite for lead in result.scored_leads]
    assert composites == sorted(composites, reverse=True), (
        f"Ranking fora de ordem: {composites}"
    )


def test_real_akasha_event_emitted():
    """Evento akasha emitido com score dos hotéis reais."""
    sink = MockAkashaSink()
    wf = LeadScoringWorkflow(akasha_sink=sink)
    result = wf.run([_BOUTIQUE, _URBAN_NO_INSTA, _RESORT])

    events = sink.query_events("lead_scoring_completed")
    assert len(events) == 1
    assert events[0].source == result.run_id
    payload = events[0].payload
    assert payload["total_scored"] == 3
    print(f"\nAkasha payload: hot={payload.get('hot_count', 0)}, "
          f"warm={payload.get('warm_count', 0)}, cold={payload.get('cold_count', 0)}")
