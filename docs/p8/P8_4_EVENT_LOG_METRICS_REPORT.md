# P8.4 — Event Log + Metrics Report

**Data:** 2026-05-09 | **Bloco:** P8.4 | **Status:** ✅ done

---

## Scope

Structured event log and metrics aggregation for Execution Graph runs.

## Files

| File | Action | Lines |
|---|---|---|
| `src/execution_graph/events.py` | created | 140 |
| `src/execution_graph/metrics.py` | created | 125 |
| `tests/execution_graph/test_event_log_metrics.py` | created | 250 |

## Events Module (`events.py`)

### EventType enum

| Type | Description |
|---|---|
| `GRAPH_RUN_STARTED` | Run began |
| `GRAPH_RUN_COMPLETED` | Run finished (done/failed/blocked) |
| `STEP_STARTED` | Step began executing |
| `STEP_COMPLETED` | Step finished successfully |
| `STEP_FAILED` | Step errored |
| `STEP_SKIPPED` | Skipped due to upstream failure |
| `APPROVAL_REQUESTED` | Approval was required |
| `APPROVAL_RESOLVED` | Approval was approved/rejected |

### GraphEvent dataclass

Fields: `event_type`, `graph_run_id`, `graph_id`, `step_id`, `role_id`, `status`, `message`, `timestamp`, `metadata` (free dict).

### EventLog

In-memory append-only log with filtering:
- `filter_by_type(EventType)` — by event category
- `filter_by_step(step_id)` — by step
- `filter_by_role(role_id)` — by role
- `step_ids()`, `role_ids()` — unique sets
- `to_dicts()` — full serialization

### `event_log_from_step_run(step_run) → EventLog`

Converts a `StepRun`'s flat log list into typed `GraphEvent` objects.

## Metrics Module (`metrics.py`)

### `compute_run_metrics(event_log) → RunMetrics`

Per-run: total_steps, done/failed/skipped counts, success_rate, roles, event count.

### `compute_aggregate_metrics(event_logs) → AggregateMetrics`

Cross-run: total_runs, overall_success_rate, avg_steps_per_run, failure_rate_by_role, runs_by_status.

## Tests — 25/10 PASS

| Category | Tests |
|---|---|
| GraphEvent creation/serialization | 3 |
| EventLog CRUD + filtering | 8 |
| event_log_from_step_run | 4 |
| RunMetrics | 3 |
| AggregateMetrics | 6 |
| Integration (3-run aggregate) | 1 |

## Cumulative

```
P8.0 execution_graph:      16/10 PASS
P8.1 step_runner:          21/15 PASS
P8.2 replay_resume:        15/12 PASS
P8.3 approval_graph:       20/12 PASS
P8.4 event_log_metrics:    25/10 PASS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL P8:                   97/59
```
