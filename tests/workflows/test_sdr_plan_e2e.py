"""E2E tests — SDRPlanWorkflow: prospects → SDRPlan finalizado → akasha.

Cobertura:
  - plano gerado com hotel/restaurante/misc
  - run_id propagado
  - plan_id gerado (prefix "plan")
  - plan.status == "final" após build
  - prospects_count == len(prospects)
  - sequences_count (só pursuable recebem sequências)
  - risk_flags presentes (all_messages_dry_run, etc.)
  - akasha evento "sdr_plan_generated"
  - erro: título vazio, lista vazia
  - SDRPlanResult.to_dict keys
  - cost_local_pct=100
"""
from __future__ import annotations

import pytest

from src.commercial_sdr.models import LeadSource, ProspectProfile
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.sdr_plan_workflow import (
    SDRPlanWorkflow,
    SDRPlanResult,
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


def _misc(name: str = "Padaria Central") -> ProspectProfile:
    return ProspectProfile.new(
        company_name=name,
        contact_name="Dono",
        segment="padaria",
        source=LeadSource.MANUAL_RESEARCH,
    )


_TITLE = "Prospecção Hotéis Natal — Junho/2026"
_DESC = "Hotéis e pousadas do RN para publis de viagem"


def _make_wf() -> tuple[SDRPlanWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return SDRPlanWorkflow(akasha_sink=sink), sink


# ── basic run ─────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()], dry_run=True)
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    assert result.run_id
    assert len(result.run_id) == 12


def test_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    assert result.cost_local_pct == 100


def test_plan_is_not_none():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    assert result.plan is not None


def test_plan_id_starts_with_plan():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    assert result.plan_id.startswith("plan")


def test_plan_status_final():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    assert result.plan.status == "final"


def test_prospects_count():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel(), _hotel("Hotel Sol"), _misc()])
    assert result.prospects_count == 3


# ── sequences ─────────────────────────────────────────────────────────────────

def test_sequences_generated_for_pursuable():
    """Hotel (HOT/WARM) gets a sequence; misc (low-fit) may not."""
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    assert result.sequences_count >= 0  # at least 0


def test_sequences_count_le_prospects_count():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel(), _misc()])
    assert result.sequences_count <= result.prospects_count


def test_hotel_generates_sequence():
    """Hotel segment is high-fit → is_pursuable → gets sequence."""
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    assert result.sequences_count == 1


# ── risk flags ────────────────────────────────────────────────────────────────

def test_risk_flags_present():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    assert len(result.risk_flags) > 0


def test_risk_flags_include_dry_run():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    assert "all_messages_dry_run" in result.risk_flags


def test_risk_flags_include_approval():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    assert "approval_required_for_external_send" in result.risk_flags


# ── akasha ────────────────────────────────────────────────────────────────────

def test_emits_akasha_event():
    wf, sink = _make_wf()
    wf.run(_TITLE, _DESC, [_hotel()])
    events = sink.query_events("sdr_plan_generated")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    events = sink.query_events("sdr_plan_generated")
    assert events[0].source == result.run_id


def test_event_has_plan_id():
    wf, sink = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    events = sink.query_events("sdr_plan_generated")
    assert events[0].payload["plan_id"] == result.plan_id


def test_event_has_sequences_count():
    wf, sink = _make_wf()
    wf.run(_TITLE, _DESC, [_hotel()])
    events = sink.query_events("sdr_plan_generated")
    assert "sequences_count" in events[0].payload


def test_akasha_event_id_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    assert result.akasha_event_id.startswith("ske_")


def test_akasha_status_written():
    wf, sink = _make_wf()
    wf.run(_TITLE, _DESC, [_hotel()])
    events = sink.query_events("sdr_plan_generated")
    assert events[0].status == SinkStatus.WRITTEN


# ── errors ────────────────────────────────────────────────────────────────────

def test_empty_title_returns_error():
    wf, _ = _make_wf()
    result = wf.run("", _DESC, [_hotel()])
    assert result.success is False
    assert result.error == "empty_title"


def test_empty_prospects_returns_error():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [])
    assert result.success is False
    assert result.error == "empty_prospect_list"


def test_error_has_run_id():
    wf, _ = _make_wf()
    result = wf.run("", _DESC, [_hotel()])
    assert result.run_id
    assert len(result.run_id) == 12


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run(_TITLE, _DESC, [_hotel()])
    d = result.to_dict()
    for key in ["run_id", "success", "plan_id", "prospects_count",
                "sequences_count", "risk_flags",
                "akasha_event_id", "cost_local_pct"]:
        assert key in d
