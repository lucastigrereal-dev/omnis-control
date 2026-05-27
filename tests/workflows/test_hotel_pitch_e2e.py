"""E2E tests — HotelPitchWorkflow (Onda 33).

Cobertura (mock / dry_run=True):
  - run() success, run_id, profile_id, company_name, tier, composite_score
  - subject_line, opening, proposal, social_proof, cta presentes
  - full_pitch nonempty, char_count > 0
  - model_used = mock/template em dry_run
  - akasha evento hotel_pitch_generated, source=run_id, event_id prefix
  - to_dict keys
  - cost_local_pct = 100
  - erros: empty_profile_id, empty_company_name
  - sem score (score=None): não quebra

Real LLM (pytest.mark.real_llm):
  - Ollama llama3.1:8b gera pitch real para Rifoles Praia Hotel
  - subject_line, opening, cta não vazios
  - tokens_used > 0, output impresso
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.commercial_sdr.models import LeadSource, OpportunityScore, ProspectProfile, ScoreTier
from src.workflows.hotel_pitch_workflow import HotelPitchWorkflow


# ── helpers ───────────────────────────────────────────────────────────────────

def _prospect(
    pid: str = "P-001",
    company: str = "Pousada Teste",
    contact: str = "João Silva",
    insta: str = "@pousadateste",
) -> ProspectProfile:
    return ProspectProfile(
        profile_id=pid,
        company_name=company,
        contact_name=contact,
        segment="hotel",
        source=LeadSource.MANUAL_RESEARCH,
        location="Natal/RN",
        instagram_handle=insta,
    )


def _score(tier: ScoreTier = ScoreTier.WARM, composite: float = 0.60) -> OpportunityScore:
    return OpportunityScore(
        score_id="SC-TEST-001",
        profile_id="P-001",
        segment_fit=0.90,
        engagement_signal=0.50,
        budget_indicator=0.30,
        urgency=0.40,
        composite=composite,
        tier=tier,
        reasoning=["hotel segment fit", "Instagram presente"],
    )


def _make_wf() -> tuple[HotelPitchWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return HotelPitchWorkflow(akasha_sink=sink), sink


# ── basic ─────────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    assert result.run_id
    assert len(result.run_id) == 12


def test_run_profile_id():
    wf, _ = _make_wf()
    result = wf.run(_prospect("P-XYZ"), _score(), dry_run=True)
    assert result.profile_id == "P-XYZ"


def test_run_company_name():
    wf, _ = _make_wf()
    result = wf.run(_prospect(company="Hotel Oásis"), _score(), dry_run=True)
    assert result.company_name == "Hotel Oásis"


def test_run_tier_from_score():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(tier=ScoreTier.HOT, composite=0.85), dry_run=True)
    assert result.tier == "hot"


def test_run_composite_score():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(composite=0.72), dry_run=True)
    assert abs(result.composite_score - 0.72) < 0.001


def test_run_without_score():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), score=None, dry_run=True)
    assert result.success is True
    assert result.tier == "warm"


def test_dry_run_model_is_template():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    assert result.model_used == "mock/template"


def test_dry_run_tokens_zero():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    assert result.tokens_used == 0


def test_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    assert result.cost_local_pct == 100


# ── pitch content ─────────────────────────────────────────────────────────────

def test_subject_line_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    assert len(result.subject_line) > 0


def test_opening_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    assert len(result.opening) > 0


def test_proposal_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    assert len(result.proposal) > 0


def test_cta_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    assert len(result.cta) > 0


def test_full_pitch_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    assert len(result.full_pitch) > 30


def test_char_count_positive():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    assert result.char_count > 0


# ── akasha ────────────────────────────────────────────────────────────────────

def test_akasha_event_emitted():
    wf, sink = _make_wf()
    wf.run(_prospect(), _score(), dry_run=True)
    events = sink.query_events("hotel_pitch_generated")
    assert len(events) == 1


def test_akasha_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    events = sink.query_events("hotel_pitch_generated")
    assert events[0].source == result.run_id


def test_akasha_event_id_prefix():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    assert result.akasha_event_id.startswith("ske_")


def test_akasha_event_status_written():
    wf, sink = _make_wf()
    wf.run(_prospect(), _score(), dry_run=True)
    events = sink.query_events("hotel_pitch_generated")
    assert events[0].status == SinkStatus.WRITTEN


def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run(_prospect(), _score(), dry_run=True)
    d = result.to_dict()
    for key in ["run_id", "success", "profile_id", "company_name", "tier",
                "composite_score", "subject_line", "opening", "proposal",
                "social_proof", "cta", "model_used", "tokens_used",
                "char_count", "akasha_event_id", "cost_local_pct"]:
        assert key in d


# ── error cases ───────────────────────────────────────────────────────────────

def test_empty_profile_id_error():
    wf, _ = _make_wf()
    p = _prospect(pid="")
    result = wf.run(p, _score(), dry_run=True)
    assert result.success is False
    assert result.error == "empty_profile_id"


def test_empty_company_name_error():
    wf, _ = _make_wf()
    p = _prospect(company="")
    result = wf.run(p, _score(), dry_run=True)
    assert result.success is False
    assert result.error == "empty_company_name"


def test_error_has_run_id():
    wf, _ = _make_wf()
    p = _prospect(pid="")
    result = wf.run(p, _score(), dry_run=True)
    assert len(result.run_id) == 12


# ── REAL LLM — Ollama llama3.1:8b ─────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.real_llm
def test_real_ollama_pitch_rifoles():
    """PROVA REAL: Ollama gera pitch para Rifoles Praia Hotel (lead HOT/WARM real)."""
    rifoles = ProspectProfile(
        profile_id="P-RN-003",
        company_name="Rifoles Praia Hotel",
        contact_name="Camila Santos",
        segment="hotel",
        source=LeadSource.MANUAL_RESEARCH,
        location="Ponta Negra, Natal/RN",
        instagram_handle="@rifoleshotel",
        website="https://rifoles.com.br",
        notes="Resort 5★ frente mar, 28k seguidores",
    )
    score = OpportunityScore(
        score_id="SC-RN-003",
        profile_id="P-RN-003",
        segment_fit=0.90,
        engagement_signal=0.55,
        budget_indicator=0.30,
        urgency=0.40,
        composite=0.595,
        tier=ScoreTier.WARM,
        reasoning=["hotel segment fit", "Instagram 28k"],
    )

    sink = MockAkashaSink()
    wf = HotelPitchWorkflow(akasha_sink=sink)
    result = wf.run(rifoles, score, dry_run=False)

    print("\n" + "=" * 60)
    print(f"MODEL: {result.model_used} | TOKENS: {result.tokens_used}")
    print(f"SUBJECT: {result.subject_line}")
    print(f"OPENING: {result.opening}")
    print(f"PROPOSAL: {result.proposal}")
    print(f"PROOF: {result.social_proof}")
    print(f"CTA: {result.cta}")
    print(f"CHARS: {result.char_count}")
    print("PITCH COMPLETO:")
    print(result.full_pitch)
    print("=" * 60)

    assert result.success is True
    assert result.tokens_used > 0
    assert len(result.subject_line) > 0
    assert len(result.opening) > 0
    assert len(result.cta) > 0
    assert result.model_used == "llama3.1:8b"
