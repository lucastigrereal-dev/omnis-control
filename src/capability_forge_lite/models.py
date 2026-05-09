"""Models for Capability Forge Lite."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

PROPOSAL_STATUS_DRAFT = "draft"
PROPOSAL_STATUS_NEEDS_APPROVAL = "needs_approval"
PROPOSAL_STATUS_APPROVED = "approved"
PROPOSAL_STATUS_REJECTED = "rejected"
PROPOSAL_STATUS_REGISTERED = "registered"

IMPL_TYPE_MANUAL_PROCESS = "manual_process"
IMPL_TYPE_CLI_WRAPPER = "cli_wrapper"
IMPL_TYPE_OFFLINE_PACKAGE = "offline_package"
IMPL_TYPE_EXTERNAL_FUTURE = "external_integration_future"
IMPL_TYPE_APP_FACTORY_FUTURE = "app_factory_future"

VALID_IMPL_TYPES = {
    IMPL_TYPE_MANUAL_PROCESS,
    IMPL_TYPE_CLI_WRAPPER,
    IMPL_TYPE_OFFLINE_PACKAGE,
    IMPL_TYPE_EXTERNAL_FUTURE,
    IMPL_TYPE_APP_FACTORY_FUTURE,
}


def _make_proposal_id() -> str:
    raw = os.urandom(8)
    return "prop_" + hashlib.sha256(raw).hexdigest()[:8]


@dataclass
class CapabilityProposal:
    proposal_id: str
    gap_id: str
    capability_name: str
    sector: str
    desired_output: str
    risk_level: str
    implementation_type: str
    approval_required: bool
    status: str
    created_at: str
    warnings: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    approval_id: Optional[str] = None

    @classmethod
    def from_gap(
        cls,
        gap_id: str,
        capability_name: str,
        sector: str,
        desired_output: str,
        risk_level: str = "medium",
        implementation_type: str = IMPL_TYPE_MANUAL_PROCESS,
    ) -> "CapabilityProposal":
        approval_required = risk_level in ("medium", "high")
        status = PROPOSAL_STATUS_NEEDS_APPROVAL if approval_required else PROPOSAL_STATUS_DRAFT
        now = datetime.now(timezone.utc).isoformat()
        warnings = []
        next_actions = []
        if implementation_type not in VALID_IMPL_TYPES:
            warnings.append(f"Unknown implementation_type: {implementation_type}")
        if approval_required:
            next_actions.append(f"jarvis forge-lite request-approval <proposal_id>")
        else:
            next_actions.append(f"jarvis forge-lite export-spec <proposal_id>")
        return cls(
            proposal_id=_make_proposal_id(),
            gap_id=gap_id,
            capability_name=capability_name,
            sector=sector,
            desired_output=desired_output,
            risk_level=risk_level,
            implementation_type=implementation_type,
            approval_required=approval_required,
            status=status,
            created_at=now,
            warnings=warnings,
            next_actions=next_actions,
        )

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "gap_id": self.gap_id,
            "capability_name": self.capability_name,
            "sector": self.sector,
            "desired_output": self.desired_output,
            "risk_level": self.risk_level,
            "implementation_type": self.implementation_type,
            "approval_required": self.approval_required,
            "status": self.status,
            "created_at": self.created_at,
            "warnings": self.warnings,
            "next_actions": self.next_actions,
            "approval_id": self.approval_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CapabilityProposal":
        return cls(
            proposal_id=d["proposal_id"],
            gap_id=d["gap_id"],
            capability_name=d["capability_name"],
            sector=d["sector"],
            desired_output=d["desired_output"],
            risk_level=d.get("risk_level", "medium"),
            implementation_type=d.get("implementation_type", IMPL_TYPE_MANUAL_PROCESS),
            approval_required=d.get("approval_required", True),
            status=d["status"],
            created_at=d["created_at"],
            warnings=d.get("warnings", []),
            next_actions=d.get("next_actions", []),
            approval_id=d.get("approval_id"),
        )
