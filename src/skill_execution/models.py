import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class BoundaryRiskLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BoundaryAction(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    REQUIRE_DRY_RUN = "REQUIRE_DRY_RUN"


@dataclass
class SkillExecutionBoundary:
    boundary_id: str = field(default_factory=lambda: _new_id("seb"))
    name: str = ""
    risk: BoundaryRiskLevel = BoundaryRiskLevel.NONE
    action: BoundaryAction = BoundaryAction.ALLOW
    requires_human: bool = False
    requires_dry_run: bool = False
    requires_permission_check: bool = False
    allowed_zones: list[str] = field(default_factory=list)
    forbidden_zones: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "boundary_id": self.boundary_id,
            "name": self.name,
            "risk": self.risk.value,
            "action": self.action.value,
            "requires_human": self.requires_human,
            "requires_dry_run": self.requires_dry_run,
            "requires_permission_check": self.requires_permission_check,
            "allowed_zones": self.allowed_zones,
            "forbidden_zones": self.forbidden_zones,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SkillExecutionBoundary":
        return cls(
            boundary_id=data.get("boundary_id", ""),
            name=data.get("name", ""),
            risk=BoundaryRiskLevel(data.get("risk", "NONE")),
            action=BoundaryAction(data.get("action", "ALLOW")),
            requires_human=data.get("requires_human", False),
            requires_dry_run=data.get("requires_dry_run", False),
            requires_permission_check=data.get("requires_permission_check", False),
            allowed_zones=data.get("allowed_zones", []),
            forbidden_zones=data.get("forbidden_zones", []),
            description=data.get("description", ""),
        )


@dataclass
class ExecutionBoundaryResult:
    result_id: str = field(default_factory=lambda: _new_id("ebr"))
    boundary_id: str = ""
    passed: bool = False
    action: BoundaryAction = BoundaryAction.BLOCK
    message: str = ""
    violations: list[str] = field(default_factory=list)
    checked_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "boundary_id": self.boundary_id,
            "passed": self.passed,
            "action": self.action.value,
            "message": self.message,
            "violations": self.violations,
            "checked_at": self.checked_at,
        }
