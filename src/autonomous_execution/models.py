"""P23 Autonomous Execution models — config, result, state machine."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Actions ──────────────────────────────────────────────────────────────────

ACTION_READ = "read"
ACTION_WRITE = "write"
ACTION_SEND = "send"
ACTION_DEPLOY = "deploy"
ACTION_DELETE = "delete"
ACTION_FINANCIAL = "financial"
ACTION_CONFIGURE = "configure"

CHECKPOINT_ACTIONS = {
    ACTION_READ: False,
    ACTION_WRITE: False,
    ACTION_SEND: True,
    ACTION_DEPLOY: True,
    ACTION_DELETE: True,
    ACTION_FINANCIAL: True,
    ACTION_CONFIGURE: False,
}


# ── Autonomous State ─────────────────────────────────────────────────────────

class AutonomousState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED_CHECKPOINT = "paused_checkpoint"
    PAUSED_ERROR = "paused_error"
    PAUSED_TIMEOUT = "paused_timeout"
    RESUMING = "resuming"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_AUTONOMOUS_STATES = {
    AutonomousState.COMPLETED,
    AutonomousState.FAILED,
    AutonomousState.CANCELLED,
}

PAUSED_STATES = {
    AutonomousState.PAUSED_CHECKPOINT,
    AutonomousState.PAUSED_ERROR,
    AutonomousState.PAUSED_TIMEOUT,
}


# ── Autonomous Config ────────────────────────────────────────────────────────

@dataclass
class AutonomousConfig:
    """Configuracao de execucao autonoma."""
    config_id: str
    max_retries_per_step: int = 3
    retry_backoff_seconds: int = 5
    step_timeout_seconds: int = 300
    mission_timeout_seconds: int = 1800
    circuit_breaker_threshold: int = 3
    checkpoint_actions: dict = field(default_factory=lambda: dict(CHECKPOINT_ACTIONS))
    notify_on_checkpoint: bool = True
    notify_on_completion: bool = True
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, dry_run: bool = True) -> "AutonomousConfig":
        return cls(
            config_id=_new_id("aut"),
            dry_run=dry_run,
        )

    @classmethod
    def load(cls) -> "AutonomousConfig":
        return cls.new()

    def is_checkpoint_action(self, action: str) -> bool:
        return self.checkpoint_actions.get(action, False)

    def to_dict(self) -> dict:
        return {
            "config_id": self.config_id,
            "max_retries_per_step": self.max_retries_per_step,
            "retry_backoff_seconds": self.retry_backoff_seconds,
            "step_timeout_seconds": self.step_timeout_seconds,
            "mission_timeout_seconds": self.mission_timeout_seconds,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "checkpoint_actions": self.checkpoint_actions,
            "notify_on_checkpoint": self.notify_on_checkpoint,
            "notify_on_completion": self.notify_on_completion,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AutonomousConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Autonomous Result ────────────────────────────────────────────────────────

@dataclass
class AutonomousResult:
    """Resultado de execucao autonoma."""
    run_id: str
    plan_id: str
    status: str = AutonomousState.IDLE.value
    steps_executed: int = 0
    steps_succeeded: int = 0
    steps_failed: int = 0
    steps_skipped: int = 0
    checkpoints_hit: list[str] = field(default_factory=list)
    current_step_id: Optional[str] = None
    elapsed_seconds: float = 0.0
    trace_events: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    resume_possible: bool = False
    created_at: str = field(default_factory=_now_iso)
    completed_at: Optional[str] = None

    @classmethod
    def new(cls, plan_id: str) -> "AutonomousResult":
        return cls(
            run_id=_new_id("aut"),
            plan_id=plan_id,
        )

    @property
    def is_terminal(self) -> bool:
        return self.status in {s.value for s in TERMINAL_AUTONOMOUS_STATES}

    @property
    def is_paused(self) -> bool:
        return self.status in {s.value for s in PAUSED_STATES}

    @property
    def is_running(self) -> bool:
        return self.status == AutonomousState.RUNNING.value

    @property
    def success_rate(self) -> float:
        total = self.steps_succeeded + self.steps_failed
        if total == 0:
            return 0.0
        return round(self.steps_succeeded / total, 2)

    def transition(self, new_state: AutonomousState) -> None:
        self.status = new_state.value
        if new_state in TERMINAL_AUTONOMOUS_STATES:
            self.completed_at = _now_iso()

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "plan_id": self.plan_id,
            "status": self.status,
            "steps_executed": self.steps_executed,
            "steps_succeeded": self.steps_succeeded,
            "steps_failed": self.steps_failed,
            "steps_skipped": self.steps_skipped,
            "checkpoints_hit": self.checkpoints_hit,
            "current_step_id": self.current_step_id,
            "elapsed_seconds": self.elapsed_seconds,
            "trace_events": self.trace_events,
            "warnings": self.warnings,
            "errors": self.errors,
            "resume_possible": self.resume_possible,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AutonomousResult":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
