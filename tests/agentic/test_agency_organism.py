"""Tests — Agency como organismo (Onda 11).

Cobertura:
  - Agency accept_mission: success, saturated, routing
  - Agency complete_mission: libera capacidade, emite evento
  - Agency get_health: status idle/active/saturated, load_pct
  - Agency run_id propagado em cada evento akasha
  - AgencyRegistry: register, get, get_by_sector, route_mission
  - Health report coletivo
  - Budget remaining
  - to_dict / model properties
"""
from __future__ import annotations

import pytest

from src.agentic.agency import (
    Agency,
    AgencyConfig,
    AgencyHealth,
    AgencyRegistry,
    AcceptResult,
    AGENCY_IDLE,
    AGENCY_ACTIVE,
    AGENCY_SATURATED,
)
from src.agentic.squad_selector import SquadDefinition, SquadMember, SquadSelector
from src.agentic.mission_engine import MissionContract
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus


# ── helpers ───────────────────────────────────────────────────────────────────

def _mission(setor: str = "marketing", objetivo: str = "criar conteúdo") -> MissionContract:
    return MissionContract(
        mission_id=f"MSN-{setor[:3].upper()}-001",
        timestamp="2026-05-24T00:00:00Z",
        status="open",
        setor=setor,
        objetivo=objetivo,
        criado_por="test",
    )


def _agency(capacity: int = 3, sector: str = "marketing") -> tuple[Agency, MockAkashaSink]:
    config = AgencyConfig(
        agency_id=f"AGY-{sector.upper()[:3]}",
        name=f"Agencia {sector.title()}",
        sector=sector,
        capacity=capacity,
        budget_usd=100.0,
    )
    sink = MockAkashaSink()
    ag = Agency(config=config, akasha_sink=sink)
    return ag, sink


# ── accept_mission ────────────────────────────────────────────────────────────

def test_accept_mission_succeeds():
    ag, _ = _agency()
    result = ag.accept_mission(_mission())
    assert result.accepted is True


def test_accept_mission_creates_run_id():
    ag, _ = _agency()
    result = ag.accept_mission(_mission())
    assert result.run_id
    assert len(result.run_id) == 12


def test_accept_mission_has_squad_assignment():
    ag, _ = _agency()
    result = ag.accept_mission(_mission(setor="marketing"))
    assert result.squad_assignment is not None
    assert result.squad_assignment.squad.squad_id != ""


def test_accept_mission_routes_to_correct_sector():
    ag, _ = _agency(sector="sales")
    result = ag.accept_mission(_mission(setor="sales"))
    assert result.squad_assignment.squad.sector == "sales"


def test_accept_mission_emits_akasha_event():
    ag, sink = _agency()
    ag.accept_mission(_mission())
    events = sink.query_events("agency_mission_accepted")
    assert len(events) == 1


def test_accept_mission_event_has_run_id():
    ag, sink = _agency()
    result = ag.accept_mission(_mission())
    events = sink.query_events("agency_mission_accepted")
    assert events[0].payload["run_id"] == result.run_id


def test_accept_mission_event_has_mission_id():
    ag, sink = _agency()
    mission = _mission()
    ag.accept_mission(mission)
    events = sink.query_events("agency_mission_accepted")
    assert events[0].payload["mission_id"] == mission.mission_id


def test_accept_mission_event_status_written():
    ag, sink = _agency()
    ag.accept_mission(_mission())
    events = sink.query_events("agency_mission_accepted")
    assert events[0].status == SinkStatus.WRITTEN


def test_accept_result_has_akasha_event_id():
    ag, _ = _agency()
    result = ag.accept_mission(_mission())
    assert result.akasha_event_id.startswith("ske_")


# ── saturation ────────────────────────────────────────────────────────────────

def test_saturated_rejects_when_full():
    ag, _ = _agency(capacity=2)
    ag.accept_mission(MissionContract("M-001", "t", "open", "marketing", "obj", "test"))
    ag.accept_mission(MissionContract("M-002", "t", "open", "marketing", "obj", "test"))
    result = ag.accept_mission(MissionContract("M-003", "t", "open", "marketing", "obj", "test"))
    assert result.accepted is False
    assert result.error == "agency_saturated"


def test_saturated_no_akasha_event_on_reject():
    ag, sink = _agency(capacity=1)
    ag.accept_mission(MissionContract("M-001", "t", "open", "marketing", "obj", "test"))
    ag.accept_mission(MissionContract("M-002", "t", "open", "marketing", "obj", "test"))
    events = sink.query_events("agency_mission_accepted")
    assert len(events) == 1


def test_saturated_has_run_id():
    ag, _ = _agency(capacity=1)
    ag.accept_mission(MissionContract("M-001", "t", "open", "marketing", "obj", "test"))
    result = ag.accept_mission(MissionContract("M-002", "t", "open", "marketing", "obj", "test"))
    assert result.run_id
    assert len(result.run_id) == 12


# ── complete_mission ──────────────────────────────────────────────────────────

def test_complete_mission_returns_true():
    ag, _ = _agency()
    ag.accept_mission(_mission())
    ok = ag.complete_mission("MSN-MAR-001")
    assert ok is True


def test_complete_mission_frees_capacity():
    ag, _ = _agency(capacity=1)
    ag.accept_mission(MissionContract("M-001", "t", "open", "marketing", "obj", "test"))
    ag.complete_mission("M-001")
    result = ag.accept_mission(MissionContract("M-002", "t", "open", "marketing", "obj", "test"))
    assert result.accepted is True


def test_complete_mission_emits_event():
    ag, sink = _agency()
    ag.accept_mission(_mission())
    ag.complete_mission("MSN-MAR-001")
    events = sink.query_events("agency_mission_completed")
    assert len(events) == 1


def test_complete_unknown_mission_returns_false():
    ag, _ = _agency()
    ok = ag.complete_mission("M-GHOST-999")
    assert ok is False


# ── get_health ────────────────────────────────────────────────────────────────

def test_health_initial_status_is_idle():
    ag, _ = _agency()
    h = ag.get_health()
    assert h.status == AGENCY_IDLE


def test_health_active_after_accept():
    ag, _ = _agency()
    ag.accept_mission(_mission())
    assert ag.get_health().status == AGENCY_ACTIVE


def test_health_saturated_when_full():
    ag, _ = _agency(capacity=2)
    ag.accept_mission(MissionContract("M-001", "t", "open", "marketing", "obj", "test"))
    ag.accept_mission(MissionContract("M-002", "t", "open", "marketing", "obj", "test"))
    assert ag.get_health().status == AGENCY_SATURATED


def test_health_idle_after_complete():
    ag, _ = _agency()
    ag.accept_mission(_mission())
    ag.complete_mission("MSN-MAR-001")
    assert ag.get_health().status == AGENCY_IDLE


def test_health_load_pct_zero_when_idle():
    ag, _ = _agency()
    assert ag.get_health().load_pct == 0


def test_health_load_pct_100_when_saturated():
    ag, _ = _agency(capacity=1)
    ag.accept_mission(_mission())
    assert ag.get_health().load_pct == 100


def test_health_budget_remaining():
    ag, _ = _agency()
    h = ag.get_health()
    assert h.budget_remaining == 100.0


def test_health_to_dict_has_required_keys():
    ag, _ = _agency()
    d = ag.get_health().to_dict()
    for key in ["agency_id", "status", "active_missions", "completed_missions",
                "capacity", "load_pct", "budget_used_usd", "squad_count"]:
        assert key in d


# ── AgencyRegistry ────────────────────────────────────────────────────────────

def test_registry_register_and_get():
    reg = AgencyRegistry()
    ag, _ = _agency()
    reg.register(ag)
    assert reg.get(ag.agency_id) is ag


def test_registry_get_by_sector():
    reg = AgencyRegistry()
    ag, _ = _agency(sector="marketing")
    reg.register(ag)
    assert reg.get_by_sector("marketing") is ag


def test_registry_route_mission():
    reg = AgencyRegistry()
    ag, sink = _agency(sector="marketing")
    reg.register(ag)
    result = reg.route_mission(_mission(setor="marketing"))
    assert result is not None
    assert result.accepted is True


def test_registry_route_unknown_sector_returns_none():
    reg = AgencyRegistry()
    result = reg.route_mission(_mission(setor="unknown_sector_xyz"))
    assert result is None


def test_registry_health_report_lists_all():
    reg = AgencyRegistry()
    ag1, _ = _agency(sector="marketing")
    ag2, _ = _agency(sector="sales")
    reg.register(ag1)
    reg.register(ag2)
    report = reg.get_health_report()
    assert len(report) == 2


def test_accept_result_to_dict():
    ag, _ = _agency()
    result = ag.accept_mission(_mission())
    d = result.to_dict()
    assert d["accepted"] is True
    assert d["run_id"] == result.run_id
    assert d["agency_id"] == ag.agency_id
