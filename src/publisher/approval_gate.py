"""Caption Approval Gate — bridge between OMNIS approval and publisher pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class CaptionApproval:
    approval_id: str
    content_id: str
    caption: str
    approver: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: str = ""

    def approve(self, approver: str) -> None:
        self.status = ApprovalStatus.APPROVED
        self.approver = approver
        self.resolved_at = datetime.now(timezone.utc).isoformat()

    def reject(self, approver: str, reason: str = "") -> None:
        self.status = ApprovalStatus.REJECTED
        self.approver = approver
        self.reason = reason
        self.resolved_at = datetime.now(timezone.utc).isoformat()

    def is_approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED

    def to_dict(self) -> dict:
        return {
            "approval_id": self.approval_id,
            "content_id": self.content_id,
            "caption": self.caption,
            "approver": self.approver,
            "status": self.status.value,
            "reason": self.reason,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CaptionApproval":
        return cls(
            approval_id=d["approval_id"],
            content_id=d.get("content_id", ""),
            caption=d.get("caption", ""),
            approver=d.get("approver", ""),
            status=ApprovalStatus(d.get("status", "pending")),
            reason=d.get("reason", ""),
            created_at=d.get("created_at", ""),
            resolved_at=d.get("resolved_at", ""),
        )


@dataclass
class ApprovalGate:
    """Gate that checks caption approval before allowing transition to QUEUED."""

    approvals: dict[str, CaptionApproval] = field(default_factory=dict)

    def submit(self, content_id: str, caption: str) -> CaptionApproval:
        import uuid
        approval = CaptionApproval(
            approval_id=str(uuid.uuid4())[:8],
            content_id=content_id,
            caption=caption,
        )
        self.approvals[content_id] = approval
        return approval

    def approve(self, content_id: str, approver: str = "operator") -> CaptionApproval:
        approval = self.approvals.get(content_id)
        if approval is None:
            raise KeyError(f"No approval found for content {content_id}")
        approval.approve(approver)
        return approval

    def reject(self, content_id: str, approver: str, reason: str = "") -> CaptionApproval:
        approval = self.approvals.get(content_id)
        if approval is None:
            raise KeyError(f"No approval found for content {content_id}")
        approval.reject(approver, reason)
        return approval

    def check(self, content_id: str) -> ApprovalStatus:
        approval = self.approvals.get(content_id)
        if approval is None:
            return ApprovalStatus.PENDING
        return approval.status

    def can_proceed(self, content_id: str) -> bool:
        return self.check(content_id) == ApprovalStatus.APPROVED

    def to_dict(self) -> dict:
        return {
            "approvals": {k: v.to_dict() for k, v in self.approvals.items()},
        }
