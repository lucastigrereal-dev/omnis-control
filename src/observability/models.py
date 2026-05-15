import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class AuditEntryType(str, Enum):
    DECISION = "DECISION"
    EXECUTION = "EXECUTION"
    ROLLBACK = "ROLLBACK"
    APPROVAL = "APPROVAL"
    ERROR = "ERROR"


class RollbackStatus(str, Enum):
    PLANNED = "PLANNED"
    POSSIBLE = "POSSIBLE"
    NOT_POSSIBLE = "NOT_POSSIBLE"
    EXECUTED = "EXECUTED"


@dataclass
class AuditEntry:
    entry_id: str = field(default_factory=lambda: _new_id("aud"))
    action: str = ""
    result: str = ""
    source: str = ""
    entry_type: AuditEntryType = AuditEntryType.EXECUTION
    detail: dict = field(default_factory=dict)
    recorded_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "action": self.action,
            "result": self.result,
            "source": self.source,
            "entry_type": self.entry_type.value,
            "detail": self.detail,
            "recorded_at": self.recorded_at,
        }


@dataclass
class RollbackPlan:
    plan_id: str = field(default_factory=lambda: _new_id("rbp"))
    contract_id: str = ""
    status: RollbackStatus = RollbackStatus.PLANNED
    steps: list[str] = field(default_factory=list)
    is_reversible: bool = True
    hint: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "contract_id": self.contract_id,
            "status": self.status.value,
            "steps": self.steps,
            "is_reversible": self.is_reversible,
            "hint": self.hint,
            "created_at": self.created_at,
        }


@dataclass
class RunStatus:
    run_id: str = field(default_factory=lambda: _new_id("run"))
    phase: str = ""
    status: str = ""
    detail: str = ""
    started_at: str = ""
    finished_at: str = ""
    tests_passed: int = 0
    tests_failed: int = 0
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "phase": self.phase,
            "status": self.status,
            "detail": self.detail,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "updated_at": self.updated_at,
        }
