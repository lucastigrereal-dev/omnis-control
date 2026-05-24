"""E2E tests — MetricsSnapshotWorkflow: MetricEvents + RunSummaries → snapshot → akasha.

Cobertura:
  - run básico (success, run_id, cost_local_pct=100)
  - metrics_count e runs_count
  - unique_tools
  - succeeded_runs / failed_runs
  - total_tokens / total_cost_usd
  - snapshot tem by_event_type, run_stats, by_tool
  - empty metrics e empty runs funcionam
  - akasha evento "metrics_snapshot_generated"
  - event source = run_id
  - event has metrics_count in payload
  - akasha_event_id starts with ske_
  - event status WRITTEN
  - by_event_type key para tipo known
  - to_dict keys
  - dry_run propagado
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.metrics.models import MetricEvent, RunSummary
from src.workflows.metrics_snapshot_workflow import (
    MetricsSnapshotWorkflow,
    MetricsSnapshotResult,
    _COST_LOCAL_PCT,
)


# ── helpers ───────────────────────────────────────────────────────────────────

_TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _metric(name: str = "run_started", tool_id: str = "", event_type: str = "run_started",
            status: str = "success", tokens_in: int = 0) -> MetricEvent:
    return MetricEvent(
        name=name,
        event_type=event_type,
        tool_id=tool_id,
        status=status,
        tokens_in=tokens_in,
    )


def _run(run_id: str = "r001", status: str = "success",
         total_tokens: int = 0, total_cost: float = 0.0,
         tools: list[str] | None = None) -> RunSummary:
    return RunSummary(
        run_id=run_id,
        status=status,
        total_tokens=total_tokens,
        total_cost_usd=total_cost,
        tools_used=tools or [],
    )


def _make_wf() -> tuple[MetricsSnapshotWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return MetricsSnapshotWorkflow(akasha_sink=sink), sink


# ── basic run ─────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf, _ = _make_wf()
    result = wf.run([_metric()], [_run()])
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run([_metric()], [_run()])
    assert result.run_id
    assert len(result.run_id) == 12


def test_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run([], [])
    assert result.cost_local_pct == _COST_LOCAL_PCT == 100


def test_dry_run_propagated():
    wf, _ = _make_wf()
    result = wf.run([], [], dry_run=True)
    assert result.dry_run is True


# ── counts ────────────────────────────────────────────────────────────────────

def test_metrics_count():
    wf, _ = _make_wf()
    result = wf.run([_metric(), _metric()], [])
    assert result.metrics_count == 2


def test_runs_count():
    wf, _ = _make_wf()
    result = wf.run([], [_run("r1"), _run("r2"), _run("r3")])
    assert result.runs_count == 3


def test_unique_tools():
    wf, _ = _make_wf()
    metrics = [
        _metric(tool_id="tool_a"),
        _metric(tool_id="tool_b"),
        _metric(tool_id="tool_a"),
    ]
    result = wf.run(metrics, [])
    assert result.unique_tools == 2


def test_succeeded_runs():
    wf, _ = _make_wf()
    runs = [_run("r1", "success"), _run("r2", "success"), _run("r3", "failed")]
    result = wf.run([], runs)
    assert result.succeeded_runs == 2


def test_failed_runs():
    wf, _ = _make_wf()
    runs = [_run("r1", "success"), _run("r2", "failed"), _run("r3", "failed")]
    result = wf.run([], runs)
    assert result.failed_runs == 2


def test_total_tokens_aggregated():
    wf, _ = _make_wf()
    runs = [_run("r1", total_tokens=100), _run("r2", total_tokens=250)]
    result = wf.run([], runs)
    assert result.total_tokens == 350


def test_total_cost_usd_aggregated():
    wf, _ = _make_wf()
    runs = [_run("r1", total_cost=0.05), _run("r2", total_cost=0.10)]
    result = wf.run([], runs)
    assert abs(result.total_cost_usd - 0.15) < 1e-9


# ── snapshot structure ────────────────────────────────────────────────────────

def test_snapshot_has_by_event_type():
    wf, _ = _make_wf()
    result = wf.run([_metric()], [])
    assert "by_event_type" in result.snapshot


def test_snapshot_has_run_stats():
    wf, _ = _make_wf()
    result = wf.run([], [_run()])
    assert "run_stats" in result.snapshot


def test_snapshot_has_by_tool():
    wf, _ = _make_wf()
    result = wf.run([_metric(tool_id="tool_x")], [])
    assert "by_tool" in result.snapshot


def test_by_event_type_key_for_known_type():
    wf, _ = _make_wf()
    result = wf.run([_metric(event_type="run_started")], [])
    assert "run_started" in result.snapshot["by_event_type"]


# ── empty inputs ──────────────────────────────────────────────────────────────

def test_empty_metrics_succeeds():
    wf, _ = _make_wf()
    result = wf.run([], [_run()])
    assert result.success is True
    assert result.metrics_count == 0


def test_empty_runs_succeeds():
    wf, _ = _make_wf()
    result = wf.run([_metric()], [])
    assert result.success is True
    assert result.runs_count == 0


def test_both_empty_succeeds():
    wf, _ = _make_wf()
    result = wf.run([], [])
    assert result.success is True
    assert result.metrics_count == 0
    assert result.runs_count == 0


# ── akasha ────────────────────────────────────────────────────────────────────

def test_emits_akasha_event():
    wf, sink = _make_wf()
    wf.run([_metric()], [_run()])
    events = sink.query_events("metrics_snapshot_generated")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run([_metric()], [_run()])
    events = sink.query_events("metrics_snapshot_generated")
    assert events[0].source == result.run_id


def test_event_has_metrics_count():
    wf, sink = _make_wf()
    wf.run([_metric(), _metric()], [])
    events = sink.query_events("metrics_snapshot_generated")
    assert events[0].payload["metrics_count"] == 2


def test_akasha_event_id_starts_with_ske():
    wf, _ = _make_wf()
    result = wf.run([], [])
    assert result.akasha_event_id.startswith("ske_")


def test_event_status_written():
    wf, sink = _make_wf()
    wf.run([], [])
    events = sink.query_events("metrics_snapshot_generated")
    assert events[0].status == SinkStatus.WRITTEN


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run([_metric()], [_run()])
    d = result.to_dict()
    for key in ["run_id", "success", "metrics_count", "runs_count",
                "unique_tools", "succeeded_runs", "failed_runs",
                "total_tokens", "total_cost_usd",
                "akasha_event_id", "cost_local_pct"]:
        assert key in d
