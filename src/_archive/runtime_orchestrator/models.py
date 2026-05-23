import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass
class PipelineStep:
    step_id: str = field(default_factory=lambda: _new_id("stp"))
    name: str = ""
    status: StepStatus = StepStatus.PENDING
    input_data: dict = field(default_factory=dict)
    output_data: dict = field(default_factory=dict)
    error: str = ""
    started_at: str = ""
    finished_at: str = ""

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "status": self.status.value,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


@dataclass
class PipelineResult:
    result_id: str = field(default_factory=lambda: _new_id("plr"))
    status: StepStatus = StepStatus.PENDING
    steps: list[PipelineStep] = field(default_factory=list)
    final_output: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    @property
    def is_success(self) -> bool:
        return self.status == StepStatus.COMPLETED

    @property
    def failed_steps(self) -> list[PipelineStep]:
        return [s for s in self.steps if s.status == StepStatus.FAILED]

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "final_output": self.final_output,
            "errors": self.errors,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }
