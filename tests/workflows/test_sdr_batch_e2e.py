"""E2E tests — SDRBatchWorkflow: prospects → score → outreach → akasha.

Cobertura:
  - pipeline completo (score + sequence) para hotel/restaurante/misc
  - run_id propagado
  - scored_count == prospects
  - actionable_count (HOT+WARM recebem sequências)
  - leads sorted by composite descending
  - hot_leads / warm_leads / cold_leads properties
  - sequences_generated <= actionable_count
  - SDRLead.is_actionable e to_dict
  - akasha evento com tier counts + sequences_generated
  - erro: lista vazia
  - to_dict keys
  - cost_local_pct=100
"""
from __future__ import annotations

import pytest

from src.commercial_sdr.models import LeadSource, ProspectProfile, ScoreTier
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.sdr_batch_workflow import (
    SDRBatchWorkflow,
    SDRBatchResult,
    SDRLead,
    _COST_LOCAL_PCT,
    _ACTIONABLE_TIERS,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _hotel(name: str = "Hotel Beira Mar") -> ProspectProfile:
    return ProspectProfile.new(
        company_name=name,
        contact_name="Gerente",
        segment="hotel",
        source=LeadSource.INSTAGRAM,
        instagram_handle=f"@{name.lower().replace(' ', '')}",
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


def _make_wf() -> tuple[SDRBatchWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return SDRBatchWorkflow(akasha_sink=sink), sink


# ── basic pipeline ────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf, _ = _make_wf()
    result = wf.run([_hotel()], dry_run=True)
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    assert result.run_id
    assert len(result.run_id) == 12


def test_scored_count_equals_total_prospects():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante(), _misc()])
    assert result.scored_count == 3


def test_total_prospects_recorded():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante()])
    assert result.total_prospects == 2


def test_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    assert result.cost_local_pct == 100


# ── scoring and ranking ───────────────────────────────────────────────────────

def test_leads_sorted_by_composite_descending():
    wf, _ = _make_wf()
    result = wf.run([_misc(), _hotel(), _restaurante()])
    scores = [l.score.composite for l in result.leads]
    assert scores == sorted(scores, reverse=True)


def test_hotel_is_actionable():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    assert result.leads[0].is_actionable is True


def test_misc_low_segment_not_actionable():
    wf, _ = _make_wf()
    result = wf.run([_misc()])
    assert result.leads[0].is_actionable is False


def test_hot_leads_subset():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante()])
    for l in result.hot_leads:
        assert l.score.tier == ScoreTier.HOT


def test_warm_leads_subset():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante()])
    for l in result.warm_leads:
        assert l.score.tier == ScoreTier.WARM


def test_cold_leads_subset():
    wf, _ = _make_wf()
    result = wf.run([_misc()])
    for l in result.cold_leads:
        assert l.score.tier == ScoreTier.COLD


def test_tier_counts_sum_to_scored():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante(), _misc()])
    total = len(result.hot_leads) + len(result.warm_leads) + len(result.cold_leads)
    disq = sum(1 for l in result.leads if l.score.tier == ScoreTier.DISQUALIFIED)
    assert total + disq == result.scored_count


# ── sequences ─────────────────────────────────────────────────────────────────

def test_actionable_leads_have_sequences():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante()])
    for l in result.leads:
        if l.is_actionable:
            assert l.sequence is not None


def test_non_actionable_leads_have_no_sequences():
    wf, _ = _make_wf()
    result = wf.run([_misc()])
    for l in result.leads:
        if not l.is_actionable:
            assert l.sequence is None


def test_sequences_generated_le_actionable():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante(), _misc()])
    assert result.sequences_generated <= result.actionable_count


# ── SDRLead model ─────────────────────────────────────────────────────────────

def test_sdr_lead_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    d = result.leads[0].to_dict()
    for key in ["profile_id", "company_name", "segment", "tier", "composite",
                "has_sequence", "steps_count"]:
        assert key in d


def test_sdr_lead_has_sequence_true_for_actionable():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    if result.leads[0].is_actionable:
        assert result.leads[0].to_dict()["has_sequence"] is True


# ── akasha ────────────────────────────────────────────────────────────────────

def test_emits_akasha_event():
    wf, sink = _make_wf()
    wf.run([_hotel()])
    events = sink.query_events("sdr_batch_completed")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run([_hotel()])
    events = sink.query_events("sdr_batch_completed")
    assert events[0].source == result.run_id


def test_event_has_actionable_count():
    wf, sink = _make_wf()
    wf.run([_hotel(), _misc()])
    events = sink.query_events("sdr_batch_completed")
    assert "actionable_count" in events[0].payload


def test_event_has_sequences_generated():
    wf, sink = _make_wf()
    wf.run([_hotel()])
    events = sink.query_events("sdr_batch_completed")
    assert "sequences_generated" in events[0].payload


def test_akasha_event_id_nonempty():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    assert result.akasha_event_id.startswith("ske_")


def test_akasha_status_written():
    wf, sink = _make_wf()
    wf.run([_hotel()])
    events = sink.query_events("sdr_batch_completed")
    assert events[0].status == SinkStatus.WRITTEN


# ── errors ────────────────────────────────────────────────────────────────────

def test_empty_list_returns_error():
    wf, _ = _make_wf()
    result = wf.run([], dry_run=True)
    assert result.success is False
    assert result.error == "empty_prospect_list"


def test_empty_list_has_run_id():
    wf, _ = _make_wf()
    result = wf.run([])
    assert result.run_id
    assert len(result.run_id) == 12


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    d = result.to_dict()
    for key in ["run_id", "success", "total_prospects", "scored_count",
                "actionable_count", "sequences_generated", "hot_count",
                "warm_count", "cold_count", "akasha_event_id", "cost_local_pct"]:
        assert key in d
