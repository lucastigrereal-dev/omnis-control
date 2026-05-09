"""Models for Squad Execution Plan (dry-run only)."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

SQUAD_RUN_STATUS_PLANNED_READY = "planned_ready"
SQUAD_RUN_STATUS_BLOCKED_APPROVAL = "blocked_pending_approval"

FORBIDDEN_MANIFEST_PREFIXES = (
    "meta_", "instagram_", "secret", "token", "password", "api_key", "client_secret",
)


def _make_run_id() -> str:
    raw = os.urandom(8)
    return "srun_" + hashlib.sha256(raw).hexdigest()[:8]


@dataclass
class SquadExecutionPlan:
    squad_run_id: str
    request: str
    sector: str
    squad_id: str
    task_plan_id: str
    roles: list[str]
    capabilities: list[str]
    risk_level: str
    approval_required: bool
    status: str
    next_actions: list[str]
    created_at: str

    def to_dict(self) -> dict:
        return {
            "squad_run_id": self.squad_run_id,
            "request": self.request,
            "sector": self.sector,
            "squad_id": self.squad_id,
            "task_plan_id": self.task_plan_id,
            "roles": self.roles,
            "capabilities": self.capabilities,
            "risk_level": self.risk_level,
            "approval_required": self.approval_required,
            "status": self.status,
            "next_actions": self.next_actions,
            "created_at": self.created_at,
        }

    @classmethod
    def from_plans(cls, squad_plan, task_plan) -> "SquadExecutionPlan":
        status = (
            SQUAD_RUN_STATUS_BLOCKED_APPROVAL
            if task_plan.approval_required
            else SQUAD_RUN_STATUS_PLANNED_READY
        )
        next_actions = []
        if task_plan.approval_required:
            next_actions.append("Request approval before executing squad")
        else:
            next_actions.append(f"Squad run {status} — review task plan and proceed")

        return cls(
            squad_run_id=_make_run_id(),
            request=squad_plan.request,
            sector=squad_plan.sector,
            squad_id=squad_plan.squad_id,
            task_plan_id=task_plan.task_plan_id,
            roles=[r.role_id for r in squad_plan.roles],
            capabilities=squad_plan.capabilities,
            risk_level=task_plan.risk_level,
            approval_required=task_plan.approval_required,
            status=status,
            next_actions=next_actions,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
