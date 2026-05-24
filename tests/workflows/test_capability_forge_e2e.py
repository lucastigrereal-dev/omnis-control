"""E2E tests — CapabilityForgeWorkflow: gaps + forge → akasha.

Cobertura:
  - run básico (success, run_id, cost_local_pct=100)
  - missions_count
  - total_gaps = sum de missing_skills
  - total_forge_results = total_gaps
  - high_severity_gaps (sales → high)
  - all_successful property
  - mission_results length = missions_count
  - mission result gaps_count
  - mission result all_successful
  - error: empty_missions
  - akasha evento "capability_gaps_detected"
  - event source = run_id
  - event has missions_count
  - akasha_event_id starts with ske_
  - event status WRITTEN
  - dry_run propagado
  - to_dict keys
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.capability_forge_workflow import (
    CapabilityForgeWorkflow,
    CapabilityForgeResult,
    _COST_LOCAL_PCT,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _mission(mission_id: str = "M-001", sector: str = "marketing",
             missing_skills: list[str] | None = None) -> dict:
    return {
        "mission_id": mission_id,
        "sector": sector,
        "missing_skills": ["caption_generator"] if missing_skills is None else missing_skills,
        "deliverables": ["legenda_final.md"],
    }


def _make_wf() -> tuple[CapabilityForgeWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return CapabilityForgeWorkflow(akasha_sink=sink), sink


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


# ── gaps + forge ──────────────────────────────────────────────────────────────

def test_missions_count():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1"), _mission("M-2")])
    assert result.missions_count == 2


def test_total_gaps_matches_missing_skills():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", missing_skills=["skill_a", "skill_b"])])
    assert result.total_gaps == 2


def test_total_forge_results_equals_total_gaps():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", missing_skills=["skill_a", "skill_b"])])
    assert result.total_forge_results == result.total_gaps


def test_high_severity_for_sales_sector():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", sector="sales", missing_skills=["dm_sequence"])])
    assert result.high_severity_gaps >= 1


def test_medium_severity_for_marketing():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", sector="marketing", missing_skills=["caption"])])
    assert result.high_severity_gaps == 0


def test_all_successful_in_dry_run():
    wf, _ = _make_wf()
    result = wf.run([_mission()])
    assert result.all_successful is True


def test_mission_results_length():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1"), _mission("M-2"), _mission("M-3")])
    assert len(result.mission_results) == 3


def test_mission_result_gaps_count():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", missing_skills=["skill_x", "skill_y"])])
    assert result.mission_results[0].gaps_count == 2


def test_mission_result_all_successful():
    wf, _ = _make_wf()
    result = wf.run([_mission()])
    assert result.mission_results[0].all_successful is True


def test_zero_missing_skills_zero_gaps():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", missing_skills=[])])
    assert result.total_gaps == 0
    assert result.total_forge_results == 0


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
    events = sink.query_events("capability_gaps_detected")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run([_mission()])
    events = sink.query_events("capability_gaps_detected")
    assert events[0].source == result.run_id


def test_event_has_missions_count():
    wf, sink = _make_wf()
    wf.run([_mission("M-1"), _mission("M-2")])
    events = sink.query_events("capability_gaps_detected")
    assert events[0].payload["missions_count"] == 2


def test_akasha_event_id_starts_with_ske():
    wf, _ = _make_wf()
    result = wf.run([_mission()])
    assert result.akasha_event_id.startswith("ske_")


def test_event_status_written():
    wf, sink = _make_wf()
    wf.run([_mission()])
    events = sink.query_events("capability_gaps_detected")
    assert events[0].status == SinkStatus.WRITTEN


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run([_mission()])
    d = result.to_dict()
    for key in ["run_id", "success", "missions_count", "total_gaps",
                "total_forge_results", "high_severity_gaps", "all_successful",
                "akasha_event_id", "cost_local_pct"]:
        assert key in d
