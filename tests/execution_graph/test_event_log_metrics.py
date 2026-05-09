"""Tests for Event Log + Metrics — P8.4."""
from __future__ import annotations

import pytest

from src.execution_graph.events import (
    EventType,
    GraphEvent,
    EventLog,
    event_log_from_step_run,
)
from src.execution_graph.metrics import (
    compute_run_metrics,
    compute_aggregate_metrics,
    RunMetrics,
    AggregateMetrics,
)
from src.execution_graph.runner import run_graph_dry
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad
from src.execution_graph.builder import build_graph


# ── Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def sample_event_log():
    """Run a real graph and convert to event log."""
    squad = compose_squad("criar post de viagem em natal")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    step_run = run_graph_dry(graph, include_snapshot=True)
    return event_log_from_step_run(step_run)


@pytest.fixture
def failed_event_log():
    """Run a graph with failure and convert to event log."""
    squad = compose_squad("criar post de viagem em natal")
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    step_run = run_graph_dry(graph, fail_at=graph.topological_order[0])
    return event_log_from_step_run(step_run)


# ── GraphEvent ─────────────────────────────────────────────────────

def test_graph_event_creation():
    evt = GraphEvent(
        event_type=EventType.STEP_STARTED,
        graph_run_id="grun_abc",
        graph_id="graph_xyz",
        step_id="step_1",
        role_id="copywriter",
        message="started",
    )
    assert evt.event_type == EventType.STEP_STARTED
    assert evt.step_id == "step_1"
    assert evt.timestamp != ""


def test_graph_event_to_dict():
    evt = GraphEvent(
        event_type=EventType.STEP_COMPLETED,
        graph_run_id="grun_abc",
        graph_id="graph_xyz",
        step_id="step_2",
        role_id="qa_auditor",
        status="done",
        metadata={"duration": "5min"},
    )
    d = evt.to_dict()
    assert d["event_type"] == "step_completed"
    assert d["metadata"]["duration"] == "5min"


def test_graph_event_from_dict():
    d = {
        "event_type": "step_failed",
        "graph_run_id": "grun_x",
        "graph_id": "graph_y",
        "step_id": "step_3",
        "role_id": "copywriter",
        "status": "failed",
        "message": "error",
        "timestamp": "2026-01-01T00:00:00Z",
        "metadata": {},
    }
    evt = GraphEvent.from_dict(d)
    assert evt.event_type == EventType.STEP_FAILED
    assert evt.step_id == "step_3"


# ── EventLog ────────────────────────────────────────────────────────

def test_event_log_empty():
    log = EventLog()
    assert len(log) == 0
    assert log.all() == []


def test_event_log_append_and_all():
    log = EventLog()
    evt = GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", step_id="s1")
    log.append(evt)
    assert len(log) == 1
    assert log.all() == [evt]


def test_event_log_filter_by_type():
    log = EventLog()
    log.append(GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", step_id="s1"))
    log.append(GraphEvent(EventType.STEP_COMPLETED, "grun_1", "graph_1", step_id="s1"))
    log.append(GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", step_id="s2"))

    started = log.filter_by_type(EventType.STEP_STARTED)
    assert len(started) == 2

    completed = log.filter_by_type(EventType.STEP_COMPLETED)
    assert len(completed) == 1


def test_event_log_filter_by_step():
    log = EventLog()
    log.append(GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", step_id="s1"))
    log.append(GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", step_id="s2"))
    log.append(GraphEvent(EventType.STEP_COMPLETED, "grun_1", "graph_1", step_id="s1"))

    s1_events = log.filter_by_step("s1")
    assert len(s1_events) == 2


def test_event_log_filter_by_role():
    log = EventLog()
    log.append(GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", step_id="s1", role_id="copywriter"))
    log.append(GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", step_id="s2", role_id="qa_auditor"))

    cw = log.filter_by_role("copywriter")
    assert len(cw) == 1


def test_event_log_step_ids():
    log = EventLog()
    log.append(GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", step_id="s1"))
    log.append(GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", step_id="s2"))
    log.append(GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", step_id="s1"))

    assert log.step_ids() == {"s1", "s2"}


def test_event_log_role_ids():
    log = EventLog()
    log.append(GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", role_id="copywriter"))
    log.append(GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", role_id="qa_auditor"))

    assert log.role_ids() == {"copywriter", "qa_auditor"}


def test_event_log_to_dicts():
    log = EventLog()
    log.append(GraphEvent(EventType.STEP_STARTED, "grun_1", "graph_1", step_id="s1"))
    dicts = log.to_dicts()
    assert len(dicts) == 1
    assert dicts[0]["step_id"] == "s1"


# ── event_log_from_step_run ────────────────────────────────────────

def test_event_log_from_step_run_has_start_and_end(sample_event_log):
    started = sample_event_log.filter_by_type(EventType.GRAPH_RUN_STARTED)
    completed = sample_event_log.filter_by_type(EventType.GRAPH_RUN_COMPLETED)
    assert len(started) == 1
    assert len(completed) == 1


def test_event_log_from_step_run_has_steps(sample_event_log):
    started = sample_event_log.filter_by_type(EventType.STEP_STARTED)
    completed = sample_event_log.filter_by_type(EventType.STEP_COMPLETED)
    assert len(started) > 0
    assert len(completed) > 0


def test_event_log_from_failed_run(sample_event_log):
    """Verify failed steps appear correctly."""
    # Use the failed_event_log fixture
    pass  # tested via failed_event_log


def test_event_log_from_step_run_handles_failed_event(failed_event_log):
    failed = failed_event_log.filter_by_type(EventType.STEP_FAILED)
    assert len(failed) == 1

    skipped = failed_event_log.filter_by_type(EventType.STEP_SKIPPED)
    assert len(skipped) > 0


# ── RunMetrics ─────────────────────────────────────────────────────

def test_compute_run_metrics(sample_event_log):
    metrics = compute_run_metrics(sample_event_log)
    assert metrics.total_steps > 0
    assert metrics.steps_done > 0
    assert metrics.steps_failed == 0
    assert metrics.success_rate == 1.0
    assert len(metrics.roles_involved) > 0
    assert metrics.events_total > 0


def test_compute_run_metrics_with_failure(failed_event_log):
    metrics = compute_run_metrics(failed_event_log)
    assert metrics.steps_failed == 1
    assert metrics.steps_skipped > 0
    assert metrics.success_rate < 1.0


def test_compute_run_metrics_empty_log():
    metrics = compute_run_metrics(EventLog())
    assert metrics.total_steps == 0
    assert metrics.success_rate == 0.0


# ── AggregateMetrics ───────────────────────────────────────────────

def test_compute_aggregate_metrics_single_run(sample_event_log):
    agg = compute_aggregate_metrics([sample_event_log])
    assert agg.total_runs == 1
    assert agg.total_steps > 0
    assert agg.overall_success_rate == 1.0
    assert agg.avg_steps_per_run > 0


def test_compute_aggregate_metrics_multiple_runs(sample_event_log, failed_event_log):
    agg = compute_aggregate_metrics([sample_event_log, failed_event_log])
    assert agg.total_runs == 2
    assert agg.steps_failed > 0
    assert agg.overall_success_rate < 1.0


def test_compute_aggregate_metrics_empty():
    agg = compute_aggregate_metrics([])
    assert agg.total_runs == 0
    assert agg.overall_success_rate == 0.0


def test_aggregate_metrics_failure_rate_by_role(failed_event_log):
    agg = compute_aggregate_metrics([failed_event_log])
    assert len(agg.failure_rate_by_role) > 0
    # At least one role has non-zero failure rate
    assert any(rate > 0 for rate in agg.failure_rate_by_role.values())


def test_aggregate_metrics_runs_by_status(sample_event_log, failed_event_log):
    agg = compute_aggregate_metrics([sample_event_log, failed_event_log])
    assert "done" in agg.runs_by_status
    assert "failed" in agg.runs_by_status


def test_aggregate_metrics_to_dict(sample_event_log):
    agg = compute_aggregate_metrics([sample_event_log])
    d = agg.to_dict()
    assert d["total_runs"] == 1
    assert "failure_rate_by_role" in d
    assert "runs_by_status" in d


# ── Integration across multiple runs ───────────────────────────────

def test_metrics_across_three_runs():
    """Run 3 different requests, collect event logs, compute aggregates."""
    logs = []
    for request in [
        "criar post de viagem",
        "fazer reels de praia",
        "campanha de marketing para hotel",
    ]:
        squad = compose_squad(request)
        task_plan = decompose_squad(squad)
        graph = build_graph(squad, task_plan)
        step_run = run_graph_dry(graph)
        logs.append(event_log_from_step_run(step_run))

    agg = compute_aggregate_metrics(logs)
    assert agg.total_runs == 3
    assert agg.overall_success_rate == 1.0
    assert agg.avg_steps_per_run > 1
    assert len(agg.failure_rate_by_role) > 0
