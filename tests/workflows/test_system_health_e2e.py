"""Tests — SystemHealthWorkflow (Onda 15).

Cobertura:
  - run() com registry vazio e default
  - overall_ok baseado em workflows
  - akasha snapshot gravado com run_id
  - agencies: active/saturated count
  - summary property
  - default() factory com 8 workflows
  - to_dict keys
"""
from __future__ import annotations

from src.agentic.agency import Agency, AgencyConfig, AgencyRegistry
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.workflow_registry import WorkflowEntry, WorkflowRegistry
from src.workflows.system_health_workflow import SystemHealthWorkflow, SystemHealthResult


# ── helpers ───────────────────────────────────────────────────────────────────

class _FakeWorkflow:
    def run(self, **kwargs): return {}


def _wf_reg(n: int = 2) -> WorkflowRegistry:
    reg = WorkflowRegistry()
    for i in range(n):
        reg.register(WorkflowEntry(
            name=f"wf_{i}", version="1.0", description="",
            cost_local_pct=100, dry_run_safe=True, factory=_FakeWorkflow,
        ))
    return reg


def _agency_reg(n: int = 2) -> AgencyRegistry:
    reg = AgencyRegistry()
    for i in range(n):
        config = AgencyConfig(agency_id=f"AGY-{i}", name=f"Agency {i}", sector=f"sector_{i}")
        reg.register(Agency(config=config, akasha_sink=MockAkashaSink()))
    return reg


# ── basic ─────────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf = SystemHealthWorkflow(workflow_registry=_wf_reg(), akasha_sink=MockAkashaSink())
    result = wf.run(dry_run=True)
    assert result.overall_ok is True


def test_run_creates_run_id():
    wf = SystemHealthWorkflow(workflow_registry=_wf_reg(), akasha_sink=MockAkashaSink())
    result = wf.run()
    assert result.run_id
    assert len(result.run_id) == 12


def test_run_workflows_total():
    wf = SystemHealthWorkflow(workflow_registry=_wf_reg(3), akasha_sink=MockAkashaSink())
    result = wf.run()
    assert result.workflows_total == 3


def test_run_workflows_importable():
    wf = SystemHealthWorkflow(workflow_registry=_wf_reg(3), akasha_sink=MockAkashaSink())
    result = wf.run()
    assert result.workflows_importable == 3


def test_run_workflows_failed_zero():
    wf = SystemHealthWorkflow(workflow_registry=_wf_reg(2), akasha_sink=MockAkashaSink())
    result = wf.run()
    assert result.workflows_failed == 0


def test_run_not_ok_when_workflow_fails():
    reg = WorkflowRegistry()
    reg.register(WorkflowEntry(
        name="broken", version="1.0", description="",
        cost_local_pct=0, dry_run_safe=False, factory=None,
    ))
    wf = SystemHealthWorkflow(workflow_registry=reg, akasha_sink=MockAkashaSink())
    result = wf.run()
    assert result.overall_ok is False


def test_run_agencies_total():
    wf = SystemHealthWorkflow(
        workflow_registry=_wf_reg(),
        agency_registry=_agency_reg(3),
        akasha_sink=MockAkashaSink(),
    )
    result = wf.run()
    assert result.agencies_total == 3


def test_run_agencies_active_when_mission_running():
    from src.agentic.mission_engine import MissionContract
    reg = _agency_reg(2)
    ag = list(reg.list_all())[0]
    ag.accept_mission(MissionContract("M-001", "t", "open", f"sector_0", "obj", "test"))
    wf = SystemHealthWorkflow(
        workflow_registry=_wf_reg(),
        agency_registry=reg,
        akasha_sink=MockAkashaSink(),
    )
    result = wf.run()
    assert result.agencies_active >= 1


# ── akasha ────────────────────────────────────────────────────────────────────

def test_run_emits_akasha_event():
    sink = MockAkashaSink()
    wf = SystemHealthWorkflow(workflow_registry=_wf_reg(), akasha_sink=sink)
    wf.run()
    events = sink.query_events("system_health_snapshot")
    assert len(events) == 1


def test_run_event_source_is_run_id():
    sink = MockAkashaSink()
    wf = SystemHealthWorkflow(workflow_registry=_wf_reg(), akasha_sink=sink)
    result = wf.run()
    events = sink.query_events("system_health_snapshot")
    assert events[0].source == result.run_id


def test_run_akasha_event_id_nonempty():
    wf = SystemHealthWorkflow(workflow_registry=_wf_reg(), akasha_sink=MockAkashaSink())
    result = wf.run()
    assert result.akasha_event_id.startswith("ske_")


def test_run_event_status_written():
    sink = MockAkashaSink()
    wf = SystemHealthWorkflow(workflow_registry=_wf_reg(), akasha_sink=sink)
    wf.run()
    events = sink.query_events("system_health_snapshot")
    assert events[0].status == SinkStatus.WRITTEN


# ── summary + to_dict ────────────────────────────────────────────────────────

def test_summary_ok():
    wf = SystemHealthWorkflow(workflow_registry=_wf_reg(), akasha_sink=MockAkashaSink())
    result = wf.run()
    assert "OK" in result.summary or "DEGRADED" in result.summary


def test_to_dict_has_required_keys():
    wf = SystemHealthWorkflow(workflow_registry=_wf_reg(), akasha_sink=MockAkashaSink())
    result = wf.run()
    d = result.to_dict()
    for key in ["run_id", "overall_ok", "workflows_total", "agencies_total",
                "cost_local_pct", "summary", "akasha_event_id"]:
        assert key in d


def test_cost_local_pct_100():
    wf = SystemHealthWorkflow(workflow_registry=_wf_reg(), akasha_sink=MockAkashaSink())
    result = wf.run()
    assert result.cost_local_pct == 100


# ── default() factory ─────────────────────────────────────────────────────────

def test_default_has_8_workflows():
    wf = SystemHealthWorkflow.default()
    wf._sink = MockAkashaSink()
    result = wf.run()
    assert result.workflows_total == 8


def test_default_all_workflows_ok():
    wf = SystemHealthWorkflow.default()
    wf._sink = MockAkashaSink()
    result = wf.run()
    assert result.workflows_ok is True
    assert result.overall_ok is True
