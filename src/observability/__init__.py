"""OMNIS Observability Layer — unified observability for the OMNIS operating system.

Sub-modules:
    schemas/     — Canonical Pydantic models + JSON Schema definitions
    events/      — Redis Streams event bus (append-only, replay-safe)
    telemetry/   — Provider observability (tokens, latency, cost, hallucination)
    traces/      — Distributed tracing with W3C Trace Context
    health/      — Composite health scoring with anomaly detection
    metrics/     — Runtime metrics with SLO/SLI tracking
    replay/      — Deterministic mission replay from event log
    audit/       — Append-only immutable audit trail

Legacy (preserved):
    models.py, error_taxonomy.py, stage_events.py, tracer_local.py,
    audit.py, rollback.py, run_log.py, logging_config.py
"""

# New unified observability
from .audit import AuditAction, AuditEntry, AuditLog, get_audit_log
from .events import EventBus, get_event_bus
from .health import HealthScorer, get_health_scorer
from .metrics import RuntimeMetricsCollector, get_runtime_metrics
from .replay import ReplayAuditor, ReplayEngine
from .schemas import (
    ALL_EVENT_TYPES,
    AnomalySignal,
    EventEnvelope,
    EventType,
    HealthComponent,
    HealthScore,
    HealthStatus,
    LatencyRecord,
    MetricType,
    ProviderMetric,
    RuntimeMetric,
    SLIDefinition,
    SLOStatus,
    SpanContext,
    SpanKind,
    TelemetryPayload,
    TokenUsage,
    TraceSpan,
)
from .telemetry import TelemetryCollector, get_telemetry_collector
from .traces import SpanHandle, Tracer, get_tracer

# Legacy re-exports (backward compatible)
from .audit import AuditEntry
from .error_taxonomy import ErrorClassifier, ErrorCategory, ErrorSeverity
from .logging_config import configure_logging
from .models import RollbackPlan, RunStatus
from .stage_events import StageEvent
from .tracer_local import LocalTracer, record_metric, skill_traced

__all__ = [
    # New observability
    "EventBus",
    "get_event_bus",
    "TelemetryCollector",
    "get_telemetry_collector",
    "Tracer",
    "SpanHandle",
    "get_tracer",
    "HealthScorer",
    "get_health_scorer",
    "RuntimeMetricsCollector",
    "get_runtime_metrics",
    "ReplayEngine",
    "ReplayAuditor",
    "AuditLog",
    "AuditEntry",
    "AuditAction",
    "get_audit_log",
    # Schemas
    "EventEnvelope",
    "EventType",
    "ALL_EVENT_TYPES",
    "TelemetryPayload",
    "ProviderMetric",
    "TokenUsage",
    "LatencyRecord",
    "SpanContext",
    "TraceSpan",
    "SpanKind",
    "HealthScore",
    "HealthComponent",
    "HealthStatus",
    "AnomalySignal",
    "RuntimeMetric",
    "SLIDefinition",
    "SLOStatus",
    "MetricType",
    # Legacy
    "LocalTracer",
    "skill_traced",
    "record_metric",
    "StageEvent",
    "ErrorClassifier",
    "ErrorCategory",
    "ErrorSeverity",
    "RollbackPlan",
    "RunStatus",
    "configure_logging",
]
