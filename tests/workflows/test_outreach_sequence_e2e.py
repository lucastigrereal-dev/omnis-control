"""E2E tests — OutreachSequenceWorkflow: prospects → sequências SDR → akasha.

Cobertura:
  - geração de sequências para hotel, restaurante, misc
  - run_id propagado
  - sequences_count == total_prospects (para casos sem falha)
  - total_steps (7 por sequência padrão)
  - warnings (validate_sequence integrado)
  - sequences_with_warnings property
  - akasha evento com counts
  - erro: lista vazia
  - to_dict keys
  - cost_local_pct=100
"""
from __future__ import annotations

import pytest

from src.commercial_sdr.models import LeadSource, ProspectProfile
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.outreach_sequence_workflow import (
    OutreachSequenceWorkflow,
    OutreachSequenceResult,
    SequenceReport,
    _COST_LOCAL_PCT,
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


def _make_wf() -> tuple[OutreachSequenceWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return OutreachSequenceWorkflow(akasha_sink=sink), sink


# ── basic run ─────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf, _ = _make_wf()
    result = wf.run([_hotel()], dry_run=True)
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    assert result.run_id
    assert len(result.run_id) == 12


def test_sequences_count_equals_prospects():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante()], dry_run=True)
    assert result.sequences_count == 2


def test_total_prospects():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante(), _hotel("Hotel Sol")], dry_run=True)
    assert result.total_prospects == 3


def test_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    assert result.cost_local_pct == 100


# ── sequences and steps ───────────────────────────────────────────────────────

def test_sequence_has_steps():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    assert len(result.sequences[0].steps) > 0


def test_total_steps_is_multiple_of_7():
    """Default cadence has 7 steps per prospect."""
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante()])
    assert result.total_steps == 14


def test_total_steps_single_prospect():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    assert result.total_steps == 7


def test_sequence_id_nonempty():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    assert result.sequences[0].sequence_id


# ── reports ───────────────────────────────────────────────────────────────────

def test_reports_count_matches_sequences():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante()])
    assert len(result.reports) == result.sequences_count


def test_report_has_steps_count():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    assert result.reports[0].steps_count == 7


def test_report_has_company_name():
    wf, _ = _make_wf()
    result = wf.run([_hotel("Hotel Maravilha")])
    assert result.reports[0].company_name == "Hotel Maravilha"


def test_report_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    d = result.reports[0].to_dict()
    for key in ["profile_id", "company_name", "sequence_id", "steps_count", "has_warnings"]:
        assert key in d


# ── warnings ──────────────────────────────────────────────────────────────────

def test_total_warnings_is_int():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    assert isinstance(result.total_warnings, int)


def test_sequences_with_warnings_subset():
    wf, _ = _make_wf()
    result = wf.run([_hotel(), _restaurante()])
    # sequences_with_warnings must be a subset of sequences
    warn_ids = {s.sequence_id for s in result.sequences_with_warnings}
    all_ids = {s.sequence_id for s in result.sequences}
    assert warn_ids.issubset(all_ids)


# ── akasha ────────────────────────────────────────────────────────────────────

def test_emits_akasha_event():
    wf, sink = _make_wf()
    wf.run([_hotel()])
    events = sink.query_events("outreach_sequences_generated")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run([_hotel()])
    events = sink.query_events("outreach_sequences_generated")
    assert events[0].source == result.run_id


def test_event_has_sequences_count():
    wf, sink = _make_wf()
    wf.run([_hotel(), _restaurante()])
    events = sink.query_events("outreach_sequences_generated")
    assert events[0].payload["sequences_count"] == 2


def test_event_has_total_steps():
    wf, sink = _make_wf()
    wf.run([_hotel()])
    events = sink.query_events("outreach_sequences_generated")
    assert "total_steps" in events[0].payload


def test_akasha_event_id_nonempty():
    wf, _ = _make_wf()
    result = wf.run([_hotel()])
    assert result.akasha_event_id.startswith("ske_")


def test_akasha_status_written():
    wf, sink = _make_wf()
    wf.run([_hotel()])
    events = sink.query_events("outreach_sequences_generated")
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
    for key in ["run_id", "success", "total_prospects", "sequences_count",
                "total_steps", "total_warnings", "akasha_event_id", "cost_local_pct"]:
        assert key in d
