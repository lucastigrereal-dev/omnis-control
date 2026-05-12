"""P12 Automation models — dry-run workflow skeleton."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# ── Trigger type constants ──────────────────────────────────────────────
TRIGGER_WEBHOOK = "webhook"
TRIGGER_SCHEDULE = "schedule"
TRIGGER_MANUAL = "manual"
TRIGGER_MISSION_COMPLETED = "mission_completed"

VALID_TRIGGERS = {TRIGGER_WEBHOOK, TRIGGER_SCHEDULE, TRIGGER_MANUAL, TRIGGER_MISSION_COMPLETED}

# ── Step type constants ─────────────────────────────────────────────────
STEP_HTTP_REQUEST = "http_request"
STEP_TRANSFORM = "transform"
STEP_FILTER = "filter"
STEP_MERGE = "merge"
STEP_DELAY = "delay"
STEP_NOTIFY = "notify"

VALID_STEPS = {STEP_HTTP_REQUEST, STEP_TRANSFORM, STEP_FILTER, STEP_MERGE, STEP_DELAY, STEP_NOTIFY}

# ── Run status constants ────────────────────────────────────────────────
RUN_PLANNED = "planned"
RUN_RUNNING = "running"
RUN_COMPLETED = "completed"
RUN_FAILED = "failed"

VALID_RUN_STATUSES = {RUN_PLANNED, RUN_RUNNING, RUN_COMPLETED, RUN_FAILED}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@dataclass
class AutomationTrigger:
    trigger_id: str
    trigger_type: str
    config: dict = field(default_factory=dict)
    enabled: bool = True

    @classmethod
    def new(cls, trigger_type: str, config: Optional[dict] = None, enabled: bool = True) -> "AutomationTrigger":
        if trigger_type not in VALID_TRIGGERS:
            raise ValueError(f"Invalid trigger type: {trigger_type!r}. Must be one of {sorted(VALID_TRIGGERS)}")
        return cls(
            trigger_id=_new_id("trig"),
            trigger_type=trigger_type,
            config=config or {},
            enabled=enabled,
        )

    def to_dict(self) -> dict:
        return {
            "trigger_id": self.trigger_id,
            "trigger_type": self.trigger_type,
            "config": self.config,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AutomationTrigger":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AutomationStep:
    step_id: str
    name: str
    step_type: str
    config: dict = field(default_factory=dict)
    position: int = 0
    depends_on: list[str] = field(default_factory=list)

    @classmethod
    def new(
        cls,
        name: str,
        step_type: str,
        config: Optional[dict] = None,
        position: int = 0,
        depends_on: Optional[list[str]] = None,
    ) -> "AutomationStep":
        if step_type not in VALID_STEPS:
            raise ValueError(f"Invalid step type: {step_type!r}. Must be one of {sorted(VALID_STEPS)}")
        return cls(
            step_id=_new_id("step"),
            name=name,
            step_type=step_type,
            config=config or {},
            position=position,
            depends_on=depends_on or [],
        )

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "step_type": self.step_type,
            "config": self.config,
            "position": self.position,
            "depends_on": self.depends_on,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AutomationStep":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AutomationWorkflow:
    workflow_id: str
    name: str
    description: str
    trigger: AutomationTrigger
    steps: list[AutomationStep] = field(default_factory=list)
    active: bool = True
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        name: str,
        description: str,
        trigger: AutomationTrigger,
        steps: Optional[list[AutomationStep]] = None,
        active: bool = True,
    ) -> "AutomationWorkflow":
        return cls(
            workflow_id=_new_id("wf"),
            name=name,
            description=description,
            trigger=trigger,
            steps=steps or [],
            active=active,
        )

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger.to_dict(),
            "steps": [s.to_dict() for s in self.steps],
            "active": self.active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AutomationWorkflow":
        trigger_data = data.pop("trigger", {})
        steps_data = data.pop("steps", [])
        trigger = AutomationTrigger.from_dict(trigger_data)
        steps = [AutomationStep.from_dict(s) for s in steps_data]
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(trigger=trigger, steps=steps, **fields)


@dataclass
class AutomationRunPlan:
    run_id: str
    workflow_id: str
    status: str
    steps_to_execute: list[str]
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    @classmethod
    def new(
        cls,
        workflow_id: str,
        steps_to_execute: list[str],
        dry_run: bool = True,
    ) -> "AutomationRunPlan":
        return cls(
            run_id=_new_id("run"),
            workflow_id=workflow_id,
            status=RUN_PLANNED,
            steps_to_execute=steps_to_execute,
            dry_run=dry_run,
        )

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "steps_to_execute": self.steps_to_execute,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AutomationRunPlan":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
