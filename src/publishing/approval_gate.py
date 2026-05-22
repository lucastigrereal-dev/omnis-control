"""ApprovalGate — human approval before publishing. CLI-based, Telegram-ready."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    request_id: str = ""
    content_type: str = "caption"  # caption | carousel | reel | batch
    content_preview: str = ""  # first 200 chars
    full_content: str = ""
    score: int = 0  # 0-100
    page: str = ""
    scheduled_at: str | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = field(default_factory=_now_iso)
    decided_at: str = ""

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "content_type": self.content_type,
            "content_preview": self.content_preview,
            "score": self.score,
            "page": self.page,
            "scheduled_at": self.scheduled_at,
            "status": self.status.value,
            "created_at": self.created_at,
            "decided_at": self.decided_at,
        }


@dataclass
class ApprovalDecision:
    request_id: str = ""
    approved: bool = False
    reason: str = ""
    decided_by: str = "auto"
    decided_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "approved": self.approved,
            "reason": self.reason,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
        }


class ApprovalGate:
    """Human approval gate for publishing operations.

    Two modes:
    - auto: approves everything above score threshold (default: 85)
    - cli: prompts on the terminal (requires human input)
    - telegram: sends message via Telegram bot (future)

    All decisions are logged to self.decisions list.
    """

    def __init__(self, mode: str = "auto", auto_approve_threshold: int = 85):
        self.mode = mode  # auto | cli | telegram
        self.auto_approve_threshold = auto_approve_threshold
        self.decisions: list[ApprovalDecision] = []
        self.pending: list[ApprovalRequest] = []

    def request_approval(
        self,
        content: str,
        content_type: str = "caption",
        page: str = "",
        score: int = 0,
        scheduled_at: str | None = None,
    ) -> ApprovalDecision:
        """Request approval for content. Returns decision."""
        import uuid
        req = ApprovalRequest(
            request_id=f"apr_{uuid.uuid4().hex[:8]}",
            content_type=content_type,
            content_preview=content[:200],
            full_content=content,
            score=score,
            page=page,
            scheduled_at=scheduled_at,
        )

        if self.mode == "auto":
            decision = self._auto_decide(req)
        elif self.mode == "cli":
            decision = self._cli_decide(req)
        elif self.mode == "telegram":
            decision = self._queue_for_telegram(req)
        else:
            decision = ApprovalDecision(request_id=req.request_id, approved=False, reason=f"unknown mode: {self.mode}")

        req.status = ApprovalStatus.APPROVED if decision.approved else ApprovalStatus.REJECTED
        req.decided_at = decision.decided_at
        self.decisions.append(decision)
        return decision

    def _auto_decide(self, req: ApprovalRequest) -> ApprovalDecision:
        if req.score >= self.auto_approve_threshold:
            return ApprovalDecision(
                request_id=req.request_id,
                approved=True,
                reason=f"auto-approved: score {req.score} >= {self.auto_approve_threshold}",
                decided_by="auto",
            )
        return ApprovalDecision(
            request_id=req.request_id,
            approved=False,
            reason=f"score {req.score} < threshold {self.auto_approve_threshold}",
            decided_by="auto",
        )

    def _cli_decide(self, req: ApprovalRequest) -> ApprovalDecision:
        print(f"\n{'='*60}")
        print(f"APPROVAL REQUIRED — {req.content_type} for {req.page}")
        print(f"Score: {req.score}/100")
        print(f"Scheduled: {req.scheduled_at or 'now'}")
        print(f"\n{req.full_content[:300]}")
        if len(req.full_content) > 300:
            print("...")
        print(f"{'='*60}")
        answer = input("Approve? [y/N]: ").strip().lower()
        approved = answer in ("y", "yes", "sim", "s")
        return ApprovalDecision(
            request_id=req.request_id,
            approved=approved,
            reason="manual CLI approval" if approved else "rejected via CLI",
            decided_by="human",
        )

    def _queue_for_telegram(self, req: ApprovalRequest) -> ApprovalDecision:
        self.pending.append(req)
        return ApprovalDecision(
            request_id=req.request_id,
            approved=False,
            reason="queued for Telegram approval",
            decided_by="pending_telegram",
        )

    def approve_all_pending(self) -> list[ApprovalDecision]:
        """Approve all queued requests (for CLI batch approval flow)."""
        decisions = []
        for req in self.pending:
            d = ApprovalDecision(request_id=req.request_id, approved=True, reason="batch approved", decided_by="human")
            decisions.append(d)
            self.decisions.append(d)
            req.status = ApprovalStatus.APPROVED
        self.pending.clear()
        return decisions

    def approval_rate(self) -> float:
        if not self.decisions:
            return 1.0
        approved = sum(1 for d in self.decisions if d.approved)
        return approved / len(self.decisions)

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "auto_approve_threshold": self.auto_approve_threshold,
            "decisions": [d.to_dict() for d in self.decisions],
            "pending_count": len(self.pending),
            "approval_rate": self.approval_rate(),
        }
