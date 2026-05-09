"""Metrics aggregator for Execution Graph events."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from src.execution_graph.events import EventLog, EventType


@dataclass
class RunMetrics:
    """Aggregated metrics from a single graph run's event log."""
    graph_run_id: str
    total_steps: int = 0
    steps_done: int = 0
    steps_failed: int = 0
    steps_skipped: int = 0
    success_rate: float = 0.0
    roles_involved: list[str] = field(default_factory=list)
    events_total: int = 0


def compute_run_metrics(event_log: EventLog) -> RunMetrics:
    """Compute metrics for a single graph run from its event log."""
    completed = event_log.filter_by_type(EventType.STEP_COMPLETED)
    failed = event_log.filter_by_type(EventType.STEP_FAILED)
    skipped = event_log.filter_by_type(EventType.STEP_SKIPPED)

    done = len(completed)
    failed_count = len(failed)
    skipped_count = len(skipped)
    total = done + failed_count + skipped_count

    graph_run_id = ""
    if event_log._events:
        graph_run_id = event_log._events[0].graph_run_id

    return RunMetrics(
        graph_run_id=graph_run_id,
        total_steps=total,
        steps_done=done,
        steps_failed=failed_count,
        steps_skipped=skipped_count,
        success_rate=(done / total) if total > 0 else 0.0,
        roles_involved=sorted(event_log.role_ids()),
        events_total=len(event_log),
    )


@dataclass
class AggregateMetrics:
    """Aggregated metrics across multiple graph runs."""
    total_runs: int = 0
    total_steps: int = 0
    steps_done: int = 0
    steps_failed: int = 0
    steps_skipped: int = 0
    overall_success_rate: float = 0.0
    avg_steps_per_run: float = 0.0
    failure_rate_by_role: dict[str, float] = field(default_factory=dict)
    runs_by_status: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "total_runs": self.total_runs,
            "total_steps": self.total_steps,
            "steps_done": self.steps_done,
            "steps_failed": self.steps_failed,
            "steps_skipped": self.steps_skipped,
            "overall_success_rate": self.overall_success_rate,
            "avg_steps_per_run": self.avg_steps_per_run,
            "failure_rate_by_role": self.failure_rate_by_role,
            "runs_by_status": self.runs_by_status,
        }


def compute_aggregate_metrics(event_logs: list[EventLog]) -> AggregateMetrics:
    """Compute aggregate metrics across multiple runs."""
    run_metrics = [compute_run_metrics(log) for log in event_logs]

    total = len(run_metrics)
    if total == 0:
        return AggregateMetrics()

    total_steps = sum(m.total_steps for m in run_metrics)
    done = sum(m.steps_done for m in run_metrics)
    failed = sum(m.steps_failed for m in run_metrics)
    skipped = sum(m.steps_skipped for m in run_metrics)

    # Failure rate by role
    role_failures: Counter[str] = Counter()
    role_totals: Counter[str] = Counter()
    for log in event_logs:
        for e in log.filter_by_type(EventType.STEP_FAILED):
            if e.role_id:
                role_failures[e.role_id] += 1
        for e in log.filter_by_type(EventType.STEP_COMPLETED):
            if e.role_id:
                role_totals[e.role_id] += 1
        for e in log.filter_by_type(EventType.STEP_FAILED):
            if e.role_id:
                role_totals[e.role_id] += 1

    failure_rate_by_role: dict[str, float] = {}
    for role_id in set(list(role_failures.keys()) + list(role_totals.keys())):
        t = role_totals.get(role_id, 0)
        f = role_failures.get(role_id, 0)
        failure_rate_by_role[role_id] = (f / t) if t > 0 else 0.0

    # Runs by status
    runs_by_status: dict[str, int] = {}
    for log in event_logs:
        completed_events = log.filter_by_type(EventType.GRAPH_RUN_COMPLETED)
        if completed_events:
            status = completed_events[0].status
            runs_by_status[status] = runs_by_status.get(status, 0) + 1

    return AggregateMetrics(
        total_runs=total,
        total_steps=total_steps,
        steps_done=done,
        steps_failed=failed,
        steps_skipped=skipped,
        overall_success_rate=(done / total_steps) if total_steps > 0 else 0.0,
        avg_steps_per_run=(total_steps / total) if total > 0 else 0.0,
        failure_rate_by_role=failure_rate_by_role,
        runs_by_status=runs_by_status,
    )
