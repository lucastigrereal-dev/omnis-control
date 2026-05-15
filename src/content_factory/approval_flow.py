"""W099 — Content Approval Flow model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ApprovalStage(str, Enum):
    DRAFT = "draft"
    BRAND_REVIEW = "brand_review"
    SEO_REVIEW = "seo_review"
    FINAL_APPROVAL = "final_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


VALID_TRANSITIONS: dict[str, list[str]] = {
    ApprovalStage.DRAFT.value: [ApprovalStage.BRAND_REVIEW.value, ApprovalStage.SEO_REVIEW.value],
    ApprovalStage.BRAND_REVIEW.value: [ApprovalStage.SEO_REVIEW.value, ApprovalStage.REJECTED.value],
    ApprovalStage.SEO_REVIEW.value: [ApprovalStage.FINAL_APPROVAL.value, ApprovalStage.REJECTED.value],
    ApprovalStage.FINAL_APPROVAL.value: [ApprovalStage.APPROVED.value, ApprovalStage.REJECTED.value],
    ApprovalStage.APPROVED.value: [],
    ApprovalStage.REJECTED.value: [ApprovalStage.DRAFT.value],
}


@dataclass
class ApprovalStep:
    step_id: str
    stage: str
    reviewer: str = ""
    decision: str = ""
    reason: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "stage": self.stage,
            "reviewer": self.reviewer,
            "decision": self.decision,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalStep":
        return cls(
            step_id=d["step_id"],
            stage=d.get("stage", ""),
            reviewer=d.get("reviewer", ""),
            decision=d.get("decision", ""),
            reason=d.get("reason", ""),
            timestamp=d.get("timestamp", ""),
        )


@dataclass
class ApprovalRequest:
    request_id: str
    content_id: str
    content_type: str = ""  # caption, carousel, reels, stories
    current_stage: str = ApprovalStage.DRAFT.value
    steps: list[ApprovalStep] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    @property
    def is_approved(self) -> bool:
        return self.current_stage == ApprovalStage.APPROVED.value

    @property
    def is_rejected(self) -> bool:
        return self.current_stage == ApprovalStage.REJECTED.value

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def can_transition_to(self, target: str) -> bool:
        allowed = VALID_TRANSITIONS.get(self.current_stage, [])
        return target in allowed

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "content_id": self.content_id,
            "content_type": self.content_type,
            "current_stage": self.current_stage,
            "steps": [s.to_dict() for s in self.steps],
            "is_approved": self.is_approved,
            "is_rejected": self.is_rejected,
            "step_count": self.step_count,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalRequest":
        req = cls(
            request_id=d["request_id"],
            content_id=d.get("content_id", ""),
            content_type=d.get("content_type", ""),
            current_stage=d.get("current_stage", ApprovalStage.DRAFT.value),
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )
        for s in d.get("steps", []):
            req.steps.append(ApprovalStep.from_dict(s))
        return req


class ApprovalFlow:
    """Deterministic approval flow manager. No LLM, no API."""

    STAGES = [
        ApprovalStage.BRAND_REVIEW.value,
        ApprovalStage.SEO_REVIEW.value,
        ApprovalStage.FINAL_APPROVAL.value,
    ]

    def create_request(self, content_id: str, content_type: str = "caption") -> ApprovalRequest:
        import uuid

        return ApprovalRequest(
            request_id=str(uuid.uuid4())[:8],
            content_id=content_id,
            content_type=content_type,
        )

    def submit_step(
        self,
        request: ApprovalRequest,
        stage: str,
        reviewer: str,
        decision: str,
        reason: str = "",
    ) -> ApprovalStep:
        import uuid

        if not request.can_transition_to(stage):
            raise ValueError(
                f"Invalid transition: {request.current_stage} -> {stage}. "
                f"Allowed: {VALID_TRANSITIONS.get(request.current_stage, [])}"
            )

        step = ApprovalStep(
            step_id=str(uuid.uuid4())[:8],
            stage=stage,
            reviewer=reviewer,
            decision=decision,
            reason=reason,
        )

        request.steps.append(step)

        if decision == ApprovalDecision.REJECT.value:
            request.current_stage = ApprovalStage.REJECTED.value
        elif decision == ApprovalDecision.REQUEST_CHANGES.value:
            pass  # stay at current stage for revision
        else:
            request.current_stage = stage

        return step

    def resubmit(self, request: ApprovalRequest) -> None:
        if not request.is_rejected:
            raise ValueError(f"Cannot resubmit request in state: {request.current_stage}")
        request.current_stage = ApprovalStage.DRAFT.value

    def advance_full_flow(
        self,
        request: ApprovalRequest,
        reviewer: str = "dry-run-bot",
    ) -> list[ApprovalStep]:
        steps: list[ApprovalStep] = []
        for stage in self.STAGES:
            step = self.submit_step(
                request,
                stage=stage,
                reviewer=reviewer,
                decision=ApprovalDecision.APPROVE.value,
            )
            steps.append(step)
        final_step = self.submit_step(
            request,
            stage=ApprovalStage.APPROVED.value,
            reviewer=reviewer,
            decision=ApprovalDecision.APPROVE.value,
        )
        steps.append(final_step)
        return steps
