import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class ExecutionStatus(str, Enum):
    DRY_RUN_OK = "DRY_RUN_OK"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    FALLBACK = "FALLBACK"


@dataclass
class SkillExecutionResult:
    result_id: str = field(default_factory=lambda: _new_id("srr"))
    request_id: str = ""
    skill_id: str = ""
    status: ExecutionStatus = ExecutionStatus.DRY_RUN_OK
    summary: str = ""
    artifacts: list[dict] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    next_action: str = ""
    executed_at: str = field(default_factory=_now_iso)
    duration_ms: int = 0

    @property
    def is_ok(self) -> bool:
        return self.status in (ExecutionStatus.DRY_RUN_OK, ExecutionStatus.COMPLETED)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0 or self.status == ExecutionStatus.FAILED

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "request_id": self.request_id,
            "skill_id": self.skill_id,
            "status": self.status.value,
            "summary": self.summary,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "warnings": self.warnings,
            "errors": self.errors,
            "next_action": self.next_action,
            "executed_at": self.executed_at,
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SkillExecutionResult":
        return cls(
            result_id=data.get("result_id", ""),
            request_id=data.get("request_id", ""),
            skill_id=data.get("skill_id", ""),
            status=ExecutionStatus(data.get("status", "DRY_RUN_OK")),
            summary=data.get("summary", ""),
            artifacts=data.get("artifacts", []),
            logs=data.get("logs", []),
            warnings=data.get("warnings", []),
            errors=data.get("errors", []),
            next_action=data.get("next_action", ""),
            executed_at=data.get("executed_at", ""),
            duration_ms=data.get("duration_ms", 0),
        )
