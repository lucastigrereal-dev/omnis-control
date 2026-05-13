# P16 Observability Local Skeleton

## Overview

Deterministic, dry-run, stdlib-only observability module. No real logging, no external services, no OpenTelemetry/Langfuse calls.

## Architecture

```
src/observability_local/
├── __init__.py          # Public API exports
├── models.py            # 6 data classes + 4 enums
└── service.py           # ObservabilityPlanner + sanitization
```

## Models

| Model | Purpose |
|---|---|
| `TraceEvent` | Dry-run trace span (trace_id, span_id, parent_span_id, attributes) |
| `MetricPoint` | Dry-run metric point (gauge, counter, histogram) |
| `RunLogEntry` | Dry-run log entry (no file writes) |
| `HealthSignal` | Dry-run health check per component |
| `ObservabilitySnapshot` | Aggregate of traces + metrics + logs + health |
| `AlertPlan` | Alert as a plan only (no real alerts fired) |

## Enums

| Enum | Values |
|---|---|
| `MetricType` | gauge, counter, histogram |
| `HealthStatus` | healthy, degraded, unhealthy |
| `AlertSeverity` | info, warning, critical |
| `RunLogLevel` | debug, info, warning, error |

## Service: ObservabilityPlanner

All methods are `@staticmethod` — fully deterministic, zero side effects.

### Methods

- `record_trace_event_plan(name, attributes?, span_id?, parent_span_id?, trace_id?)` → `TraceEvent`
- `build_metric_point(name, value, unit?, labels?, metric_type?)` → `MetricPoint`
- `build_run_log_entry(run_id, message, level?, module?, metadata?)` → `RunLogEntry`
- `build_health_snapshot(components?)` → `ObservabilitySnapshot`
- `plan_alerts(snapshot, thresholds?)` → `list[AlertPlan]`
- `sanitize_observability_payload(payload)` → sanitized dict

### Convenience

- `build_snapshot_from_planner(traces?, metrics?, logs?, health?)` → `ObservabilitySnapshot`

## Sanitization

Sensitive keys are redacted to `[REDACTED]`:

- `token`, `secret`, `password`, `api_key`, `bearer`
- `authorization`, `access_key`, `private_key`

Matching is case-insensitive and recursive through nested dicts and lists.

## Rules

1. No real logs written to disk or services
2. No Langfuse/OpenTelemetry integration
3. No external service calls
4. Sanitization mandatory on all payloads
5. Alerts are plans only — never dispatched
6. Stdlib only — dataclasses, enums, uuid, re, datetime

## Scope Boundaries

- **Allowed**: `src/observability_local/`, `tests/observability_local/`, `docs/observability_local/`
- **Forbidden**: `src/observability/`, all other `src/*/` modules, `logs/`, `data/`, `config/`
