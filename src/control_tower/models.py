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


def _short_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionType(str, Enum):
    OBSERVE = "OBSERVE"
    PLAN = "PLAN"
    DRY_RUN = "DRY_RUN"
    EXECUTE_WITH_APPROVAL = "EXECUTE_WITH_APPROVAL"
    BLOCK = "BLOCK"


class BoundarySystem(str, Enum):
    KRATOS = "KRATOS"
    AURORA = "AURORA"
    OMNIS = "OMNIS"
    SKILLS = "SKILLS"
    AKASHA = "AKASHA"
    LUCAS = "LUCAS"


@dataclass
class BoundaryRule:
    source_system: BoundarySystem
    target_system: BoundarySystem
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)

    def allows(self, action: str) -> bool:
        if action in self.forbidden_actions:
            return False
        return action in self.allowed_actions

    def to_dict(self) -> dict:
        return {
            "source_system": self.source_system.value,
            "target_system": self.target_system.value,
            "allowed_actions": self.allowed_actions,
            "forbidden_actions": self.forbidden_actions,
        }


@dataclass
class TowerRequest:
    request_id: str = field(default_factory=lambda: _new_id("ctr"))
    title: str = ""
    description: str = ""
    source_system: BoundarySystem = BoundarySystem.OMNIS
    target_system: BoundarySystem = BoundarySystem.OMNIS
    action: str = ""
    paths_touched: list[str] = field(default_factory=list)
    is_external: bool = False
    is_destructive: bool = False
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "title": self.title,
            "description": self.description,
            "source_system": self.source_system.value,
            "target_system": self.target_system.value,
            "action": self.action,
            "paths_touched": self.paths_touched,
            "is_external": self.is_external,
            "is_destructive": self.is_destructive,
            "created_at": self.created_at,
        }


@dataclass
class Decision:
    decision_id: str = field(default_factory=lambda: _new_id("ctd"))
    title: str = ""
    recommendation: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    action_type: ActionType = ActionType.OBSERVE
    requires_human_approval: bool = False
    rationale: str = ""
    do_not_do: list[str] = field(default_factory=list)
    next_step: str = ""
    request_id: str = ""
    created_at: str = field(default_factory=_now_iso)

    @property
    def is_blocked(self) -> bool:
        return self.action_type == ActionType.BLOCK

    @property
    def is_safe(self) -> bool:
        return self.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "recommendation": self.recommendation,
            "risk_level": self.risk_level.value,
            "action_type": self.action_type.value,
            "requires_human_approval": self.requires_human_approval,
            "rationale": self.rationale,
            "do_not_do": self.do_not_do,
            "next_step": self.next_step,
            "request_id": self.request_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Decision":
        return cls(
            decision_id=data.get("decision_id", ""),
            title=data.get("title", ""),
            recommendation=data.get("recommendation", ""),
            risk_level=RiskLevel(data.get("risk_level", "LOW")),
            action_type=ActionType(data.get("action_type", "OBSERVE")),
            requires_human_approval=data.get("requires_human_approval", False),
            rationale=data.get("rationale", ""),
            do_not_do=data.get("do_not_do", []),
            next_step=data.get("next_step", ""),
            request_id=data.get("request_id", ""),
            created_at=data.get("created_at", ""),
        )


@dataclass
class NextAction:
    action_id: str = field(default_factory=lambda: _new_id("ctn"))
    decision_id: str = ""
    title: str = ""
    description: str = ""
    target_system: BoundarySystem = BoundarySystem.OMNIS
    action: str = ""
    dry_run_required: bool = True
    requires_approval: bool = False
    expected_output: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "action_id": self.action_id,
            "decision_id": self.decision_id,
            "title": self.title,
            "description": self.description,
            "target_system": self.target_system.value,
            "action": self.action,
            "dry_run_required": self.dry_run_required,
            "requires_approval": self.requires_approval,
            "expected_output": self.expected_output,
            "created_at": self.created_at,
        }
