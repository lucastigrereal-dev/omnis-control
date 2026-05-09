"""Models for Squad Composer."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _make_squad_id() -> str:
    raw = os.urandom(8)
    return "squad_" + hashlib.sha256(raw).hexdigest()[:8]


@dataclass
class SquadRoleAssignment:
    role_id: str
    role_name: str
    reason: str
    expected_outputs: list[str]
    risk_level: str


@dataclass
class SquadPlan:
    squad_id: str
    request: str
    sector: str
    roles: list[SquadRoleAssignment]
    capabilities: list[str]
    risk_level: str
    approval_required: bool
    rationale: str
    warnings: list[str]
    next_actions: list[str]
    created_at: str

    @classmethod
    def new(
        cls,
        request: str,
        sector: str,
        roles: list[SquadRoleAssignment],
        capabilities: list[str],
        rationale: str = "",
        warnings: Optional[list[str]] = None,
    ) -> "SquadPlan":
        role_risks = [r.risk_level for r in roles]
        risk_level = "high" if "high" in role_risks else ("medium" if "medium" in role_risks else "low")
        approval_required = risk_level in ("medium", "high")
        next_actions = []
        if approval_required:
            next_actions.append(f"jarvis approvals-center request-approval for squad")
        else:
            next_actions.append(f"jarvis squad-run plan \"{request}\"")

        return cls(
            squad_id=_make_squad_id(),
            request=request,
            sector=sector,
            roles=roles,
            capabilities=capabilities,
            risk_level=risk_level,
            approval_required=approval_required,
            rationale=rationale or f"Sector '{sector}' — {len(roles)} roles assigned.",
            warnings=warnings or [],
            next_actions=next_actions,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "squad_id": self.squad_id,
            "request": self.request,
            "sector": self.sector,
            "roles": [
                {
                    "role_id": r.role_id,
                    "role_name": r.role_name,
                    "reason": r.reason,
                    "expected_outputs": r.expected_outputs,
                    "risk_level": r.risk_level,
                }
                for r in self.roles
            ],
            "capabilities": self.capabilities,
            "risk_level": self.risk_level,
            "approval_required": self.approval_required,
            "rationale": self.rationale,
            "warnings": self.warnings,
            "next_actions": self.next_actions,
            "created_at": self.created_at,
        }
