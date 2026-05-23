"""Models for Approval Center."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone

APPROVAL_STATUS_PENDING = "pending"
APPROVAL_STATUS_APPROVED = "approved"
APPROVAL_STATUS_REJECTED = "rejected"


def _make_request_id() -> str:
    raw = os.urandom(8)
    return "req_" + hashlib.sha256(raw).hexdigest()[:8]


@dataclass
class ApprovalRequest:
    request_id: str
    subject: str
    description: str
    capability_id: str
    risk_level: str
    status: str
    requested_at: str
    resolved_at: str | None
    resolution_note: str

    @classmethod
    def new(
        cls,
        subject: str,
        description: str = "",
        capability_id: str = "unknown",
        risk_level: str = "high",
    ) -> "ApprovalRequest":
        return cls(
            request_id=_make_request_id(),
            subject=subject,
            description=description,
            capability_id=capability_id,
            risk_level=risk_level,
            status=APPROVAL_STATUS_PENDING,
            requested_at=datetime.now(timezone.utc).isoformat(),
            resolved_at=None,
            resolution_note="",
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "subject": self.subject,
            "description": self.description,
            "capability_id": self.capability_id,
            "risk_level": self.risk_level,
            "status": self.status,
            "requested_at": self.requested_at,
            "resolved_at": self.resolved_at,
            "resolution_note": self.resolution_note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> "ApprovalRequest":
        return cls(
            request_id=d["request_id"],
            subject=d["subject"],
            description=d.get("description", ""),
            capability_id=d.get("capability_id", "unknown"),
            risk_level=d.get("risk_level", "high"),
            status=d["status"],
            requested_at=d["requested_at"],
            resolved_at=d.get("resolved_at"),
            resolution_note=d.get("resolution_note", ""),
        )
