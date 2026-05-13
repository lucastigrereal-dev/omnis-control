"""P20 OMNIS Supreme Activation — Core models."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


class SupremeStatus(str, Enum):
    INTAKE = "intake"
    CONTEXT_BUILDING = "context_building"
    PLANNING = "planning"
    DRY_RUN = "dry_run"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


VALID_SUPREME_TRANSITIONS: dict[SupremeStatus, set[SupremeStatus]] = {
    SupremeStatus.INTAKE: {SupremeStatus.CONTEXT_BUILDING, SupremeStatus.FAILED},
    SupremeStatus.CONTEXT_BUILDING: {SupremeStatus.PLANNING, SupremeStatus.FAILED},
    SupremeStatus.PLANNING: {SupremeStatus.DRY_RUN, SupremeStatus.FAILED},
    SupremeStatus.DRY_RUN: {SupremeStatus.AWAITING_APPROVAL, SupremeStatus.PLANNING, SupremeStatus.FAILED},
    SupremeStatus.AWAITING_APPROVAL: {SupremeStatus.EXECUTING, SupremeStatus.CANCELLED, SupremeStatus.PLANNING},
    SupremeStatus.EXECUTING: {SupremeStatus.COMPLETED, SupremeStatus.FAILED},
    SupremeStatus.COMPLETED: set(),
    SupremeStatus.FAILED: {SupremeStatus.PLANNING, SupremeStatus.CANCELLED},
    SupremeStatus.CANCELLED: set(),
}


@dataclass
class SupremeStep:
    step_id: str
    module_ref: str
    operation: str
    input_from: list[str] = field(default_factory=list)
    output_to: list[str] = field(default_factory=list)
    status: str = "pending"
    config: dict = field(default_factory=dict)
    result: Optional[dict] = None
    retry_attempt: int = 0
    retry_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    @classmethod
    def new(
        cls,
        module_ref: str,
        operation: str,
        input_from: Optional[list[str]] = None,
        output_to: Optional[list[str]] = None,
        config: Optional[dict] = None,
    ) -> "SupremeStep":
        return cls(
            step_id=_new_id("step_"),
            module_ref=module_ref,
            operation=operation,
            input_from=input_from or [],
            output_to=output_to or [],
            config=config or {},
        )

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "module_ref": self.module_ref,
            "operation": self.operation,
            "input_from": self.input_from,
            "output_to": self.output_to,
            "status": self.status,
            "config": self.config,
            "result": self.result,
            "retry_attempt": self.retry_attempt,
            "retry_at": self.retry_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SupremeStep":
        return cls(
            step_id=data["step_id"],
            module_ref=data["module_ref"],
            operation=data["operation"],
            input_from=data.get("input_from", []),
            output_to=data.get("output_to", []),
            status=data.get("status", "pending"),
            config=data.get("config", {}),
            result=data.get("result"),
            retry_attempt=data.get("retry_attempt", 0),
            retry_at=data.get("retry_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
        )


@dataclass
class SupremePlan:
    plan_id: str
    mission_id: str
    steps: list[SupremeStep] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)
    selected_modules: list[str] = field(default_factory=list)
    estimated_duration: Optional[float] = None
    dry_run: bool = True
    generated_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        mission_id: str,
        steps: Optional[list[SupremeStep]] = None,
        edges: Optional[list[tuple[str, str]]] = None,
        selected_modules: Optional[list[str]] = None,
        estimated_duration: Optional[float] = None,
        dry_run: bool = True,
    ) -> "SupremePlan":
        return cls(
            plan_id=_new_id("plan_"),
            mission_id=mission_id,
            steps=steps or [],
            edges=edges or [],
            selected_modules=selected_modules or [],
            estimated_duration=estimated_duration,
            dry_run=dry_run,
        )

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "mission_id": self.mission_id,
            "steps": [s.to_dict() for s in self.steps],
            "edges": [list(e) for e in self.edges],
            "selected_modules": self.selected_modules,
            "estimated_duration": self.estimated_duration,
            "dry_run": self.dry_run,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SupremePlan":
        steps = [SupremeStep.from_dict(s) for s in data.get("steps", [])]
        edges = [tuple(e) for e in data.get("edges", [])]
        return cls(
            plan_id=data["plan_id"],
            mission_id=data["mission_id"],
            steps=steps,
            edges=edges,
            selected_modules=data.get("selected_modules", []),
            estimated_duration=data.get("estimated_duration"),
            dry_run=data.get("dry_run", True),
            generated_at=data.get("generated_at", ""),
        )


@dataclass
class MissionReport:
    report_id: str
    mission_id: str
    summary: str = ""
    steps_summary: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    learnings: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        mission_id: str,
        summary: str = "",
        steps_summary: Optional[list[dict]] = None,
        metrics: Optional[dict] = None,
        learnings: Optional[list[dict]] = None,
        warnings: Optional[list[str]] = None,
    ) -> "MissionReport":
        return cls(
            report_id=_new_id("rpt_"),
            mission_id=mission_id,
            summary=summary,
            steps_summary=steps_summary or [],
            metrics=metrics or {},
            learnings=learnings or [],
            warnings=warnings or [],
        )

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "mission_id": self.mission_id,
            "summary": self.summary,
            "steps_summary": self.steps_summary,
            "metrics": self.metrics,
            "learnings": self.learnings,
            "warnings": self.warnings,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MissionReport":
        return cls(
            report_id=data["report_id"],
            mission_id=data["mission_id"],
            summary=data.get("summary", ""),
            steps_summary=data.get("steps_summary", []),
            metrics=data.get("metrics", {}),
            learnings=data.get("learnings", []),
            warnings=data.get("warnings", []),
            generated_at=data.get("generated_at", ""),
        )


@dataclass
class SupremeMission:
    mission_id: str
    request_text: str
    intent: str = ""
    sector: str = ""
    status: SupremeStatus = SupremeStatus.INTAKE
    context: dict = field(default_factory=dict)
    plan: dict = field(default_factory=dict)
    execution: dict = field(default_factory=dict)
    delivery: Optional[dict] = None
    report: Optional[dict] = None
    trace_events: list[dict] = field(default_factory=list)
    approval_decisions: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    dry_run: bool = True
    approval_required: bool = True
    created_at: str = field(default_factory=_now_iso)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    @classmethod
    def new(
        cls,
        request_text: str,
        intent: str = "",
        sector: str = "",
        dry_run: bool = True,
        approval_required: bool = True,
    ) -> "SupremeMission":
        return cls(
            mission_id=_new_id("spr_"),
            request_text=request_text,
            intent=intent,
            sector=sector,
            dry_run=dry_run,
            approval_required=approval_required,
        )

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "request_text": self.request_text,
            "intent": self.intent,
            "sector": self.sector,
            "status": self.status.value,
            "context": self.context,
            "plan": self.plan if isinstance(self.plan, dict) else self.plan.to_dict(),
            "execution": self.execution,
            "delivery": self.delivery,
            "report": self.report,
            "trace_events": self.trace_events,
            "approval_decisions": self.approval_decisions,
            "warnings": self.warnings,
            "blockers": self.blockers,
            "dry_run": self.dry_run,
            "approval_required": self.approval_required,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SupremeMission":
        status_raw = data.get("status", "intake")
        status = SupremeStatus(status_raw) if isinstance(status_raw, str) else status_raw
        return cls(
            mission_id=data["mission_id"],
            request_text=data["request_text"],
            intent=data.get("intent", ""),
            sector=data.get("sector", ""),
            status=status,
            context=data.get("context", {}),
            plan=data.get("plan", {}),
            execution=data.get("execution", {}),
            delivery=data.get("delivery"),
            report=data.get("report"),
            trace_events=data.get("trace_events", []),
            approval_decisions=data.get("approval_decisions", []),
            warnings=data.get("warnings", []),
            blockers=data.get("blockers", []),
            dry_run=data.get("dry_run", True),
            approval_required=data.get("approval_required", True),
            created_at=data.get("created_at", ""),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
        )

    def transition_to(self, target: SupremeStatus) -> bool:
        if target not in VALID_SUPREME_TRANSITIONS.get(self.status, set()):
            return False
        self.status = target
        return True
