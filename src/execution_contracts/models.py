import uuid
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class ContractStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class OutcomeStatus(str, Enum):
    PLANNED = "PLANNED"
    DRY_RUN_OK = "DRY_RUN_OK"
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"


@dataclass
class ExecutionContract:
    contract_id: str = field(default_factory=lambda: _new_id("exc"))
    title: str = ""
    project: str = ""
    requested_by: str = ""
    target_system: str = ""
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    requires_approval: bool = False
    dry_run_required: bool = True
    expected_outputs: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    rollback_hint: str = ""
    report_path: str = ""
    status: ContractStatus = ContractStatus.DRAFT
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "contract_id": self.contract_id,
            "title": self.title,
            "project": self.project,
            "requested_by": self.requested_by,
            "target_system": self.target_system,
            "allowed_paths": self.allowed_paths,
            "forbidden_paths": self.forbidden_paths,
            "allowed_actions": self.allowed_actions,
            "forbidden_actions": self.forbidden_actions,
            "requires_approval": self.requires_approval,
            "dry_run_required": self.dry_run_required,
            "expected_outputs": self.expected_outputs,
            "acceptance_criteria": self.acceptance_criteria,
            "rollback_hint": self.rollback_hint,
            "report_path": self.report_path,
            "status": self.status.value,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionContract":
        return cls(
            contract_id=data.get("contract_id", ""),
            title=data.get("title", ""),
            project=data.get("project", ""),
            requested_by=data.get("requested_by", ""),
            target_system=data.get("target_system", ""),
            allowed_paths=data.get("allowed_paths", []),
            forbidden_paths=data.get("forbidden_paths", []),
            allowed_actions=data.get("allowed_actions", []),
            forbidden_actions=data.get("forbidden_actions", []),
            requires_approval=data.get("requires_approval", False),
            dry_run_required=data.get("dry_run_required", True),
            expected_outputs=data.get("expected_outputs", []),
            acceptance_criteria=data.get("acceptance_criteria", []),
            rollback_hint=data.get("rollback_hint", ""),
            report_path=data.get("report_path", ""),
            status=ContractStatus(data.get("status", "DRAFT")),
            created_at=data.get("created_at", ""),
        )


@dataclass
class ContractOutcome:
    outcome_id: str = field(default_factory=lambda: _new_id("exo"))
    contract_id: str = ""
    status: OutcomeStatus = OutcomeStatus.PLANNED
    summary: str = ""
    changed_files: list[str] = field(default_factory=list)
    tests_run: int = 0
    tests_passed: int = 0
    reports_generated: list[str] = field(default_factory=list)
    next_recommendation: str = ""
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    @property
    def all_tests_passed(self) -> bool:
        return self.tests_run > 0 and self.tests_run == self.tests_passed

    def to_dict(self) -> dict:
        return {
            "outcome_id": self.outcome_id,
            "contract_id": self.contract_id,
            "status": self.status.value,
            "summary": self.summary,
            "changed_files": self.changed_files,
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "reports_generated": self.reports_generated,
            "next_recommendation": self.next_recommendation,
            "errors": self.errors,
            "created_at": self.created_at,
        }
