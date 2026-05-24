"""E2E tests — SquadAssignmentWorkflow: missões → SquadAssignment lote → akasha.

Cobertura:
  - run básico (success, run_id, cost_local_pct=100)
  - missions_count correto
  - assignments length = missions_count
  - sector marketing → SQD-MKT
  - sector sales → SQD-SALES
  - sector desconhecido → fallback SQD-GEN
  - unique_squads property
  - fallback_count property
  - to_dict keys
  - error: empty_missions
  - akasha evento "squad_assignments_generated"
  - event source = run_id
  - event has missions_count
  - akasha_event_id starts with ske_
  - event status WRITTEN
  - dry_run propagado
  - assignment.mission_id correto
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.squad_assignment_workflow import (
    SquadAssignmentWorkflow,
    SquadAssignmentResult,
    _COST_LOCAL_PCT,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _mission(mission_id: str = "M-001", sector: str = "marketing") -> dict:
    return {"mission_id": mission_id, "sector": sector}


def _make_wf() -> tuple[SquadAssignmentWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return SquadAssignmentWorkflow(akasha_sink=sink), sink


# ── basic run ─────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf, _ = _make_wf()
    result = wf.run([_mission()])
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run([_mission()])
    assert result.run_id
    assert len(result.run_id) == 12


def test_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run([_mission()])
    assert result.cost_local_pct == _COST_LOCAL_PCT == 100


def test_dry_run_propagated():
    wf, _ = _make_wf()
    result = wf.run([_mission()], dry_run=True)
    assert result.dry_run is True


# ── assignments ───────────────────────────────────────────────────────────────

def test_missions_count():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1"), _mission("M-2"), _mission("M-3")])
    assert result.missions_count == 3


def test_assignments_length_matches_missions():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1"), _mission("M-2")])
    assert len(result.assignments) == 2


def test_assignment_mission_id_correct():
    wf, _ = _make_wf()
    result = wf.run([_mission("MISSION-42", "marketing")])
    assert result.assignments[0].mission_id == "MISSION-42"


def test_marketing_sector_gets_mkt_squad():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", "marketing")])
    assert result.assignments[0].squad.squad_id == "SQD-MKT"


def test_sales_sector_gets_sales_squad():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", "sales")])
    assert result.assignments[0].squad.squad_id == "SQD-SALES"


def test_unknown_sector_gets_fallback():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", "unknown_sector_xyz")])
    assert result.assignments[0].squad.squad_id == "SQD-GEN"


def test_unique_squads_property():
    wf, _ = _make_wf()
    result = wf.run([
        _mission("M-1", "marketing"),
        _mission("M-2", "marketing"),
        _mission("M-3", "sales"),
    ])
    assert result.unique_squads == 2


def test_fallback_count():
    wf, _ = _make_wf()
    result = wf.run([
        _mission("M-1", "unknown_xyz"),
        _mission("M-2", "marketing"),
        _mission("M-3", "also_unknown"),
    ])
    assert result.fallback_count == 2


def test_squads_used_list_length():
    wf, _ = _make_wf()
    result = wf.run([_mission(f"M-{i}") for i in range(4)])
    assert len(result.squads_used) == 4


# ── error ─────────────────────────────────────────────────────────────────────

def test_empty_missions_returns_error():
    wf, _ = _make_wf()
    result = wf.run([])
    assert result.success is False
    assert result.error == "empty_missions"


def test_empty_missions_has_run_id():
    wf, _ = _make_wf()
    result = wf.run([])
    assert result.run_id
    assert len(result.run_id) == 12


# ── akasha ────────────────────────────────────────────────────────────────────

def test_emits_akasha_event():
    wf, sink = _make_wf()
    wf.run([_mission()])
    events = sink.query_events("squad_assignments_generated")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run([_mission()])
    events = sink.query_events("squad_assignments_generated")
    assert events[0].source == result.run_id


def test_event_has_missions_count():
    wf, sink = _make_wf()
    wf.run([_mission("M-1"), _mission("M-2")])
    events = sink.query_events("squad_assignments_generated")
    assert events[0].payload["missions_count"] == 2


def test_akasha_event_id_starts_with_ske():
    wf, _ = _make_wf()
    result = wf.run([_mission()])
    assert result.akasha_event_id.startswith("ske_")


def test_event_status_written():
    wf, sink = _make_wf()
    wf.run([_mission()])
    events = sink.query_events("squad_assignments_generated")
    assert events[0].status == SinkStatus.WRITTEN


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run([_mission()])
    d = result.to_dict()
    for key in ["run_id", "success", "missions_count", "unique_squads",
                "fallback_count", "squads_used",
                "akasha_event_id", "cost_local_pct"]:
        assert key in d
