"""P20 OMNIS Supreme Activation — Fine orchestration layer."""
from src.omnis_supreme.models import (
    MissionReport,
    SupremeMission,
    SupremePlan,
    SupremeStatus,
    SupremeStep,
    VALID_SUPREME_TRANSITIONS,
)
from src.omnis_supreme.errors import (
    ApprovalDeniedError,
    DryRunBlockedError,
    ExecutionError,
    PlanError,
    StepAdapterError,
    SupremeError,
    UnknownIntentError,
)
from src.omnis_supreme.service import (
    SupremeOrchestrator,
    SupremeIntake,
    SupremeContextBuilder,
    SupremePlanner,
    SupremeExecutor,
    ExecutionResult,
)
from src.omnis_supreme.adapters import ADAPTER_REGISTRY
from src.omnis_supreme.tracer import ObservabilityTracer, Span
from src.omnis_supreme.approval_gate import SupremeApprovalGate
from src.omnis_supreme.reporter import SupremeReporter

__all__ = [
    "SupremeMission",
    "SupremePlan",
    "SupremeStep",
    "SupremeStatus",
    "MissionReport",
    "VALID_SUPREME_TRANSITIONS",
    "SupremeError",
    "PlanError",
    "ExecutionError",
    "ApprovalDeniedError",
    "UnknownIntentError",
    "StepAdapterError",
    "DryRunBlockedError",
    "SupremeOrchestrator",
    "SupremeIntake",
    "SupremeContextBuilder",
    "SupremePlanner",
    "SupremeExecutor",
    "ExecutionResult",
    "ADAPTER_REGISTRY",
    "ObservabilityTracer",
    "Span",
    "SupremeApprovalGate",
    "SupremeReporter",
]
