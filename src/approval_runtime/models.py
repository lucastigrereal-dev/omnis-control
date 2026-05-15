import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    AUTO_APPROVED = "AUTO_APPROVED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ApprovalRequest:
    request_id: str = field(default_factory=lambda: _new_id("apr"))
    action: str = ""
    target: str = ""
    risk: RiskLevel = RiskLevel.LOW
    is_destructive: bool = False
    reason: str = ""
    source_system: str = "omnis"
    dry_run_possible: bool = True
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "action": self.action,
            "target": self.target,
            "risk": self.risk.value,
            "is_destructive": self.is_destructive,
            "reason": self.reason,
            "source_system": self.source_system,
            "dry_run_possible": self.dry_run_possible,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ApprovalRequest":
        return cls(
            request_id=data.get("request_id", ""),
            action=data.get("action", ""),
            target=data.get("target", ""),
            risk=RiskLevel(data.get("risk", "LOW").upper()),
            is_destructive=data.get("is_destructive", False),
            reason=data.get("reason", ""),
            source_system=data.get("source_system", "omnis"),
            dry_run_possible=data.get("dry_run_possible", True),
            created_at=data.get("created_at", ""),
        )


@dataclass
class ApprovalDecision:
    decision_id: str = field(default_factory=lambda: _new_id("apd"))
    request_id: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    requires_human: bool = False
    requires_dry_run: bool = False
    requires_documented_reason: bool = False
    message: str = ""
    decided_at: str = ""
    decided_by: str = ""

    @property
    def is_blocked(self) -> bool:
        return self.status == ApprovalStatus.REJECTED

    @property
    def is_approved(self) -> bool:
        return self.status in (ApprovalStatus.AUTO_APPROVED, ApprovalStatus.APPROVED)

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "status": self.status.value,
            "requires_human": self.requires_human,
            "requires_dry_run": self.requires_dry_run,
            "requires_documented_reason": self.requires_documented_reason,
            "message": self.message,
            "decided_at": self.decided_at,
            "decided_by": self.decided_by,
        }
