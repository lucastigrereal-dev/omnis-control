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


class WorkOrderStatus(str, Enum):
    DRAFT = "DRAFT"
    WAITING = "WAITING"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class WorkOrderDecision(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    INVALID = "INVALID"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass
class WorkOrder:
    order_id: str = field(default_factory=lambda: _new_id("wo"))
    title: str = ""
    aba: str = ""
    type: str = ""
    status: WorkOrderStatus = WorkOrderStatus.DRAFT
    risk: str = "LOW"
    project: str = ""
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    requires_approval: bool = False
    dry_run: bool = True
    description: str = ""
    body: str = ""
    created_at: str = field(default_factory=_now_iso)

    @property
    def is_executable(self) -> bool:
        return self.status in (WorkOrderStatus.READY, WorkOrderStatus.IN_PROGRESS)

    @property
    def is_high_risk(self) -> bool:
        return self.risk.upper() in ("HIGH", "CRITICAL")

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "title": self.title,
            "aba": self.aba,
            "type": self.type,
            "status": self.status.value,
            "risk": self.risk,
            "project": self.project,
            "allowed_paths": self.allowed_paths,
            "forbidden_paths": self.forbidden_paths,
            "requires_approval": self.requires_approval,
            "dry_run": self.dry_run,
            "description": self.description,
            "body": self.body,
            "created_at": self.created_at,
        }
