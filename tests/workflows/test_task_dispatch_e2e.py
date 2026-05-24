"""E2E tests — TaskDispatchWorkflow: manifests → DispatchPlan lote → akasha.

Cobertura:
  - run básico (success, run_id, cost_local_pct=100)
  - missions_count
  - plans length = missions_count
  - total_tasks > 0
  - executors_used list length = total_tasks
  - unique_executors property
  - avg_tasks_per_mission property
  - marketing sector → publisher executor
  - sales sector → sales executor
  - dry_run propagado para plano
  - error: empty_missions
  - akasha evento "task_dispatch_plans_generated"
  - event source = run_id
  - event has missions_count in payload
  - akasha_event_id starts with ske_
  - event status WRITTEN
  - to_dict keys
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.agentic.deliverable_mapper import (
    DeliverableManifest, DeliverableSpec
)
from src.workflows.task_dispatch_workflow import (
    TaskDispatchWorkflow,
    TaskDispatchResult,
    _COST_LOCAL_PCT,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _manifest(setor: str = "marketing", tipo: str = "content",
              n_deliverables: int = 2) -> DeliverableManifest:
    specs = [
        DeliverableSpec(
            filename=f"file_{i}.md",
            description=f"Deliverable {i}",
            format="md",
        )
        for i in range(n_deliverables)
    ]
    return DeliverableManifest(
        mission_id=None,
        setor=setor,
        tipo=tipo,
        deliverables=specs,
    )


def _mission(mission_id: str = "M-001", setor: str = "marketing",
             n_deliverables: int = 2) -> dict:
    return {
        "mission_id": mission_id,
        "manifest": _manifest(setor=setor, n_deliverables=n_deliverables),
    }


def _make_wf() -> tuple[TaskDispatchWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return TaskDispatchWorkflow(akasha_sink=sink), sink


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


# ── plans + tasks ─────────────────────────────────────────────────────────────

def test_missions_count():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1"), _mission("M-2")])
    assert result.missions_count == 2


def test_plans_length_matches_missions():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1"), _mission("M-2"), _mission("M-3")])
    assert len(result.plans) == 3


def test_total_tasks_matches_deliverables():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", n_deliverables=3)])
    assert result.total_tasks == 3


def test_executors_used_length_equals_total_tasks():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", n_deliverables=2), _mission("M-2", n_deliverables=3)])
    assert len(result.executors_used) == result.total_tasks


def test_unique_executors_property():
    wf, _ = _make_wf()
    result = wf.run([
        _mission("M-1", "marketing"),
        _mission("M-2", "sales"),
    ])
    assert result.unique_executors >= 2


def test_avg_tasks_per_mission():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", n_deliverables=4)])
    assert result.avg_tasks_per_mission == 4.0


# ── executor routing ──────────────────────────────────────────────────────────

def test_marketing_routes_to_publisher():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", "marketing")])
    executors = {e.executor for e in result.plans[0].entries}
    assert "publisher" in executors


def test_sales_routes_to_sales():
    wf, _ = _make_wf()
    result = wf.run([_mission("M-1", "sales")])
    executors = {e.executor for e in result.plans[0].entries}
    assert "sales" in executors


def test_plan_dry_run_matches_workflow_dry_run():
    wf, _ = _make_wf()
    result = wf.run([_mission()], dry_run=True)
    assert result.plans[0].dry_run is True


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
    events = sink.query_events("task_dispatch_plans_generated")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run([_mission()])
    events = sink.query_events("task_dispatch_plans_generated")
    assert events[0].source == result.run_id


def test_event_has_missions_count():
    wf, sink = _make_wf()
    wf.run([_mission("M-1"), _mission("M-2")])
    events = sink.query_events("task_dispatch_plans_generated")
    assert events[0].payload["missions_count"] == 2


def test_akasha_event_id_starts_with_ske():
    wf, _ = _make_wf()
    result = wf.run([_mission()])
    assert result.akasha_event_id.startswith("ske_")


def test_event_status_written():
    wf, sink = _make_wf()
    wf.run([_mission()])
    events = sink.query_events("task_dispatch_plans_generated")
    assert events[0].status == SinkStatus.WRITTEN


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run([_mission()])
    d = result.to_dict()
    for key in ["run_id", "success", "missions_count", "total_tasks",
                "unique_executors", "avg_tasks_per_mission", "executors_used",
                "akasha_event_id", "cost_local_pct"]:
        assert key in d
