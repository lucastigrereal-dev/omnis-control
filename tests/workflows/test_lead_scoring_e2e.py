"""E2E tests — LeadScoringWorkflow: prospects → score → ranking → akasha.

Cobertura:
  - scoring de uma lista de prospects (hotel/restaurante/misc)
  - run_id propagado
  - tier distribution (HOT/WARM/COLD/DISQUALIFIED)
  - ranking por composite score descendente
  - hot_leads / warm_leads / top_3 properties
  - akasha evento com run_id e tier_distribution
  - erro: lista vazia
  - to_dict keys
  - cost_local_pct=100
"""
from __future__ import annotations

import pytest

from src.commercial_sdr.models import LeadSource, ProspectProfile
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.lead_scoring_workflow import (
    LeadScoringWorkflow,
    LeadScoringResult,
    ScoredLead,
    _COST_LOCAL_PCT,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _hotel(name: str = "Hotel Beira Mar", handle: str = "@hotelbeiramar") -> ProspectProfile:
    return ProspectProfile.new(
        company_name=name,
        contact_name="Gerente",
        segment="hotel",
        source=LeadSource.INSTAGRAM,
        instagram_handle=handle,
        email=f"contato@{name.lower().replace(' ', '')}.com",
    )


def _restaurante(name: str = "Restaurante Mangai") -> ProspectProfile:
    return ProspectProfile.new(
        company_name=name,
        contact_name="Chef",
        segment="restaurante",
        source=LeadSource.INSTAGRAM,
        instagram_handle=f"@{name.lower().replace(' ', '')}",
    )


def _misc(name: str = "Padaria Central") -> ProspectProfile:
    return ProspectProfile.new(
        company_name=name,
        contact_name="Dono",
        segment="padaria",
        source=LeadSource.MANUAL_RESEARCH,
    )


def _make_wf() -> tuple[LeadScoringWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return LeadScoringWorkflow(akasha_sink=sink), sink


# ── basic scoring ─────────────────────────────────────────────────────────────

def test_scoring_succeeds():
    wf, _ = _make_wf()
    result = wf.run([_hotel()], dry_run=True)
    assert result.success is True


def test_scoring_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run([_hotel()], dry_run=True)
    assert result.run_id
    assert len(result.run_id) == 12


def test_scoring_total_scored():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante(), _misc()], dry_run=True)
    assert result.total_scored == 3


def test_scoring_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run([_hotel()], dry_run=True)
    assert result.cost_local_pct == 100


# ── tiers ────────────────────────────────────────────────────────────────────

def test_hotel_segment_scores_high():
    wf, _ = _make_wf()
    result = wf.run([_hotel()], dry_run=True)
    assert result.scored_leads[0].score.composite >= 0.40


def test_hotel_with_instagram_is_warm_or_hot():
    wf, _ = _make_wf()
    result = wf.run([_hotel(handle="@grandhotel")], dry_run=True)
    from src.commercial_sdr.models import ScoreTier
    assert result.scored_leads[0].score.tier in (ScoreTier.HOT, ScoreTier.WARM)


def test_tier_counts_sum_to_total():
    wf, _ = _make_wf()
    prospects = [_hotel(), _restaurante(), _misc()]
    result = wf.run(prospects, dry_run=True)
    assert result.hot_count + result.warm_count + result.cold_count + result.disqualified_count == 3


# ── ranking ───────────────────────────────────────────────────────────────────

def test_results_sorted_by_composite_descending():
    wf, _ = _make_wf()
    result = wf.run([_misc(), _hotel(), _restaurante()], dry_run=True)
    scores = [l.score.composite for l in result.scored_leads]
    assert scores == sorted(scores, reverse=True)


def test_top_3_property():
    wf, _ = _make_wf()
    prospects = [_hotel(f"Hotel {i}") for i in range(5)]
    result = wf.run(prospects, dry_run=True)
    assert len(result.top_3) <= 3


def test_hot_leads_property():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _hotel(), _misc()], dry_run=True)
    from src.commercial_sdr.models import ScoreTier
    assert all(l.score.tier == ScoreTier.HOT for l in result.hot_leads)


def test_warm_leads_property():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante(), _misc()], dry_run=True)
    from src.commercial_sdr.models import ScoreTier
    assert all(l.score.tier == ScoreTier.WARM for l in result.warm_leads)


# ── akasha ────────────────────────────────────────────────────────────────────

def test_emits_akasha_event():
    wf, sink = _make_wf()
    wf.run([_hotel()], dry_run=True)
    events = sink.query_events("lead_scoring_completed")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run([_hotel()], dry_run=True)
    events = sink.query_events("lead_scoring_completed")
    assert events[0].source == result.run_id


def test_event_has_tier_counts():
    wf, sink = _make_wf()
    wf.run([_hotel(), _misc()], dry_run=True)
    events = sink.query_events("lead_scoring_completed")
    payload = events[0].payload
    assert "hot_count" in payload
    assert "warm_count" in payload


def test_event_has_top_leads():
    wf, sink = _make_wf()
    wf.run([_hotel(), _restaurante()], dry_run=True)
    events = sink.query_events("lead_scoring_completed")
    assert "top_leads" in events[0].payload


def test_akasha_event_id_nonempty():
    wf, _ = _make_wf()
    result = wf.run([_hotel()], dry_run=True)
    assert result.akasha_event_id.startswith("ske_")


def test_akasha_status_written():
    wf, sink = _make_wf()
    wf.run([_hotel()], dry_run=True)
    events = sink.query_events("lead_scoring_completed")
    assert events[0].status == SinkStatus.WRITTEN


# ── errors ────────────────────────────────────────────────────────────────────

def test_empty_list_returns_error():
    wf, _ = _make_wf()
    result = wf.run([], dry_run=True)
    assert result.success is False
    assert result.error == "empty_prospect_list"


def test_empty_list_has_run_id():
    wf, _ = _make_wf()
    result = wf.run([], dry_run=True)
    assert result.run_id
    assert len(result.run_id) == 12


# ── ScoredLead model ──────────────────────────────────────────────────────────

def test_scored_lead_to_dict():
    wf, _ = _make_wf()
    result = wf.run([_hotel()], dry_run=True)
    d = result.scored_leads[0].to_dict()
    for key in ["company_name", "segment", "tier", "composite"]:
        assert key in d


# ── LeadScoringResult model ───────────────────────────────────────────────────

def test_result_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run([_hotel()], dry_run=True)
    d = result.to_dict()
    for key in ["run_id", "success", "total_scored", "hot_count",
                "cost_local_pct", "akasha_event_id"]:
        assert key in d
