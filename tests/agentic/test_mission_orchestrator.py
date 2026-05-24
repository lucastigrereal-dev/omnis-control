"""Tests — MissionOrchestrator (Onda 14).

Cobertura:
  - orchestrate básico: brief → agency → workflow → akasha
  - sem agência registrada (agency_registry vazio) — workflow direto
  - agência aceita missão → squad atribuído → workflow executado
  - agência saturada → rejeita → erro retornado
  - workflow não encontrado → erro retornado
  - workflow levanta exceção → erro retornado
  - run_id propagado em OrchestrationResult
  - akasha evento gravado com mission_id e workflow_name
  - to_dict do OrchestrationResult
"""
from __future__ import annotations

import pytest

from src.agentic.agency import Agency, AgencyConfig, AgencyRegistry
from src.agentic.mission_orchestrator import MissionBrief, MissionOrchestrator, OrchestrationResult
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.workflow_registry import WorkflowEntry, WorkflowRegistry


# ── helpers ───────────────────────────────────────────────────────────────────

class _OkWorkflow:
    def run(self, **kwargs):
        class _R:
            success = True
            run_id = "wf_run_001"
            def to_dict(self): return {"success": True, "run_id": self.run_id}
        return _R()


class _FailWorkflow:
    def run(self, **kwargs):
        raise RuntimeError("workflow internal error")


def _make_registry(wf_ok: bool = True) -> WorkflowRegistry:
    reg = WorkflowRegistry()
    if wf_ok:
        reg.register(WorkflowEntry(
            name="test_wf", version="1.0", description="test",
            cost_local_pct=100, dry_run_safe=True,
            factory=_OkWorkflow,
        ))
    else:
        reg.register(WorkflowEntry(
            name="test_wf", version="1.0", description="fail",
            cost_local_pct=100, dry_run_safe=True,
            factory=_FailWorkflow,
        ))
    return reg


def _make_agency_registry(capacity: int = 5, sector: str = "marketing") -> AgencyRegistry:
    config = AgencyConfig(agency_id="AGY-MKT", name="Agency Marketing",
                          sector=sector, capacity=capacity)
    sink = MockAkashaSink()
    ag = Agency(config=config, akasha_sink=sink)
    reg = AgencyRegistry()
    reg.register(ag)
    return reg


def _brief(wf_name: str = "test_wf", setor: str = "marketing") -> MissionBrief:
    return MissionBrief(
        objetivo="criar conteúdo de viagem para Instagram",
        setor=setor,
        workflow_name=wf_name,
        workflow_kwargs={"dry_run": True},
    )


# ── basic orchestration ───────────────────────────────────────────────────────

def test_orchestrate_succeeds_without_agency():
    wf_reg = _make_registry()
    sink = MockAkashaSink()
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=sink)
    result = orch.orchestrate(_brief())
    assert result.success is True


def test_orchestrate_creates_run_id():
    wf_reg = _make_registry()
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=MockAkashaSink())
    result = orch.orchestrate(_brief())
    assert result.run_id
    assert len(result.run_id) == 12


def test_orchestrate_has_mission_id():
    wf_reg = _make_registry()
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=MockAkashaSink())
    result = orch.orchestrate(_brief())
    assert result.mission_id.startswith("MSN-")


def test_orchestrate_emits_akasha_event():
    wf_reg = _make_registry()
    sink = MockAkashaSink()
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=sink)
    orch.orchestrate(_brief())
    events = sink.query_events("orchestration_completed")
    assert len(events) == 1


def test_orchestrate_event_source_is_run_id():
    wf_reg = _make_registry()
    sink = MockAkashaSink()
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=sink)
    result = orch.orchestrate(_brief())
    events = sink.query_events("orchestration_completed")
    assert events[0].source == result.run_id


def test_orchestrate_event_has_mission_id():
    wf_reg = _make_registry()
    sink = MockAkashaSink()
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=sink)
    result = orch.orchestrate(_brief())
    events = sink.query_events("orchestration_completed")
    assert events[0].payload["mission_id"] == result.mission_id


def test_orchestrate_event_has_workflow_name():
    wf_reg = _make_registry()
    sink = MockAkashaSink()
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=sink)
    orch.orchestrate(_brief(wf_name="test_wf"))
    events = sink.query_events("orchestration_completed")
    assert events[0].payload["workflow_name"] == "test_wf"


def test_orchestrate_akasha_event_id_nonempty():
    wf_reg = _make_registry()
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=MockAkashaSink())
    result = orch.orchestrate(_brief())
    assert result.akasha_event_id.startswith("ske_")


# ── with agency ───────────────────────────────────────────────────────────────

def test_orchestrate_with_agency_succeeds():
    wf_reg = _make_registry()
    ag_reg = _make_agency_registry()
    sink = MockAkashaSink()
    orch = MissionOrchestrator(agency_registry=ag_reg, workflow_registry=wf_reg, akasha_sink=sink)
    result = orch.orchestrate(_brief(setor="marketing"))
    assert result.success is True
    assert result.agency_id == "AGY-MKT"


def test_orchestrate_with_agency_has_squad_id():
    wf_reg = _make_registry()
    ag_reg = _make_agency_registry()
    orch = MissionOrchestrator(agency_registry=ag_reg, workflow_registry=wf_reg, akasha_sink=MockAkashaSink())
    result = orch.orchestrate(_brief(setor="marketing"))
    assert result.squad_id != ""


def test_orchestrate_agency_completes_mission_on_success():
    wf_reg = _make_registry()
    ag_reg = _make_agency_registry()
    ag = ag_reg.get("AGY-MKT")
    orch = MissionOrchestrator(agency_registry=ag_reg, workflow_registry=wf_reg, akasha_sink=MockAkashaSink())
    orch.orchestrate(_brief(setor="marketing"))
    assert ag.get_health().active_missions == 0


# ── saturation / rejection ────────────────────────────────────────────────────

def test_saturated_agency_returns_failure():
    wf_reg = _make_registry()
    ag_reg = _make_agency_registry(capacity=0)
    orch = MissionOrchestrator(agency_registry=ag_reg, workflow_registry=wf_reg, akasha_sink=MockAkashaSink())
    result = orch.orchestrate(_brief(setor="marketing"))
    assert result.success is False
    assert result.error == "agency_saturated"


def test_saturated_has_run_id():
    wf_reg = _make_registry()
    ag_reg = _make_agency_registry(capacity=0)
    orch = MissionOrchestrator(agency_registry=ag_reg, workflow_registry=wf_reg, akasha_sink=MockAkashaSink())
    result = orch.orchestrate(_brief(setor="marketing"))
    assert result.run_id
    assert len(result.run_id) == 12


# ── workflow errors ───────────────────────────────────────────────────────────

def test_workflow_not_found_returns_error():
    wf_reg = _make_registry()
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=MockAkashaSink())
    result = orch.orchestrate(_brief(wf_name="nonexistent_wf"))
    assert result.success is False
    assert "workflow_not_found" in result.error


def test_workflow_exception_returns_error():
    wf_reg = _make_registry(wf_ok=False)
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=MockAkashaSink())
    result = orch.orchestrate(_brief())
    assert result.success is False
    assert "workflow_error" in result.error


# ── OrchestrationResult model ─────────────────────────────────────────────────

def test_result_to_dict_has_run_id():
    wf_reg = _make_registry()
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=MockAkashaSink())
    result = orch.orchestrate(_brief())
    d = result.to_dict()
    assert d["run_id"] == result.run_id


def test_result_to_dict_has_success():
    wf_reg = _make_registry()
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=MockAkashaSink())
    result = orch.orchestrate(_brief())
    assert result.to_dict()["success"] is True


def test_result_to_dict_has_workflow_result():
    wf_reg = _make_registry()
    orch = MissionOrchestrator(workflow_registry=wf_reg, akasha_sink=MockAkashaSink())
    result = orch.orchestrate(_brief())
    d = result.to_dict()
    assert isinstance(d["workflow_result"], dict)
