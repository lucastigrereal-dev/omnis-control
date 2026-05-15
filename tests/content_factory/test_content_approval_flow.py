"""Tests for W099 — Content Approval Flow."""
from __future__ import annotations

import pytest

from src.content_factory.approval_flow import (
    ApprovalStage,
    ApprovalDecision,
    ApprovalStep,
    ApprovalRequest,
    ApprovalFlow,
)


class TestApprovalStep:
    def test_create_step(self):
        step = ApprovalStep(step_id="s1", stage=ApprovalStage.BRAND_REVIEW.value)
        assert step.step_id == "s1"
        assert step.stage == ApprovalStage.BRAND_REVIEW.value
        assert step.decision == ""

    def test_create_full_step(self):
        step = ApprovalStep(
            step_id="s2",
            stage=ApprovalStage.SEO_REVIEW.value,
            reviewer="lucas",
            decision=ApprovalDecision.APPROVE.value,
            reason="Looks good",
        )
        assert step.reviewer == "lucas"
        assert step.decision == "approve"
        assert step.reason == "Looks good"

    def test_to_dict_roundtrip(self):
        step = ApprovalStep(
            step_id="s3",
            stage=ApprovalStage.BRAND_REVIEW.value,
            reviewer="bot",
            decision=ApprovalDecision.REJECT.value,
            reason="Bad tone",
        )
        d = step.to_dict()
        restored = ApprovalStep.from_dict(d)
        assert restored.step_id == step.step_id
        assert restored.reviewer == "bot"
        assert restored.decision == "reject"
        assert restored.reason == "Bad tone"


class TestApprovalRequest:
    def test_create_request(self):
        req = ApprovalRequest(request_id="r1", content_id="c1")
        assert req.request_id == "r1"
        assert req.content_id == "c1"
        assert req.current_stage == ApprovalStage.DRAFT.value
        assert req.is_approved is False
        assert req.is_rejected is False

    def test_can_transition_draft_to_brand_review(self):
        req = ApprovalRequest(request_id="r2", content_id="c2")
        assert req.can_transition_to(ApprovalStage.BRAND_REVIEW.value) is True

    def test_can_transition_draft_to_seo_review(self):
        req = ApprovalRequest(request_id="r3", content_id="c3")
        assert req.can_transition_to(ApprovalStage.SEO_REVIEW.value) is True

    def test_cannot_transition_draft_to_approved_directly(self):
        req = ApprovalRequest(request_id="r4", content_id="c4")
        assert req.can_transition_to(ApprovalStage.APPROVED.value) is False

    def test_to_dict_roundtrip(self):
        req = ApprovalRequest(request_id="r5", content_id="c5", content_type="caption")
        req.steps.append(ApprovalStep(step_id="s1", stage=ApprovalStage.BRAND_REVIEW.value))
        d = req.to_dict()
        restored = ApprovalRequest.from_dict(d)
        assert restored.request_id == req.request_id
        assert restored.step_count == 1
        assert restored.is_approved is False

    def test_step_count(self):
        req = ApprovalRequest(request_id="r6", content_id="c6")
        req.steps.append(ApprovalStep(step_id="s1", stage="brand_review"))
        req.steps.append(ApprovalStep(step_id="s2", stage="seo_review"))
        assert req.step_count == 2


class TestApprovalFlow:
    def setup_method(self):
        self.flow = ApprovalFlow()

    def test_create_request(self):
        req = self.flow.create_request("c1", "caption")
        assert isinstance(req, ApprovalRequest)
        assert req.content_id == "c1"
        assert req.content_type == "caption"
        assert req.current_stage == ApprovalStage.DRAFT.value

    def test_submit_step_brand_review(self):
        req = self.flow.create_request("c2")
        step = self.flow.submit_step(
            req,
            stage=ApprovalStage.BRAND_REVIEW.value,
            reviewer="lucas",
            decision=ApprovalDecision.APPROVE.value,
        )
        assert req.current_stage == ApprovalStage.BRAND_REVIEW.value
        assert step.reviewer == "lucas"

    def test_submit_step_reject(self):
        req = self.flow.create_request("c3")
        self.flow.submit_step(
            req,
            stage=ApprovalStage.BRAND_REVIEW.value,
            reviewer="lucas",
            decision=ApprovalDecision.REJECT.value,
            reason="Wrong tone",
        )
        assert req.is_rejected is True
        assert req.current_stage == ApprovalStage.REJECTED.value

    def test_resubmit_from_rejected(self):
        req = self.flow.create_request("c4")
        self.flow.submit_step(
            req,
            stage=ApprovalStage.BRAND_REVIEW.value,
            reviewer="lucas",
            decision=ApprovalDecision.REJECT.value,
        )
        assert req.is_rejected is True
        self.flow.resubmit(req)
        assert req.current_stage == ApprovalStage.DRAFT.value
        assert req.is_rejected is False

    def test_resubmit_non_rejected_raises(self):
        req = self.flow.create_request("c5")
        with pytest.raises(ValueError, match="Cannot resubmit"):
            self.flow.resubmit(req)

    def test_invalid_transition_raises(self):
        req = self.flow.create_request("c6")
        with pytest.raises(ValueError, match="Invalid transition"):
            self.flow.submit_step(
                req,
                stage=ApprovalStage.APPROVED.value,
                reviewer="lucas",
                decision=ApprovalDecision.APPROVE.value,
            )

    def test_advance_full_flow(self):
        req = self.flow.create_request("c7")
        steps = self.flow.advance_full_flow(req, reviewer="dry-run-bot")
        assert req.is_approved is True
        assert req.current_stage == ApprovalStage.APPROVED.value
        assert len(steps) == 4  # brand_review, seo_review, final_approval, approved

    def test_full_flow_stages_order(self):
        req = self.flow.create_request("c8")
        steps = self.flow.advance_full_flow(req)
        assert steps[0].stage == ApprovalStage.BRAND_REVIEW.value
        assert steps[1].stage == ApprovalStage.SEO_REVIEW.value
        assert steps[2].stage == ApprovalStage.FINAL_APPROVAL.value

    def test_request_changes_keeps_stage(self):
        req = self.flow.create_request("c9")
        self.flow.submit_step(
            req,
            stage=ApprovalStage.BRAND_REVIEW.value,
            reviewer="lucas",
            decision=ApprovalDecision.REQUEST_CHANGES.value,
            reason="Needs improvement",
        )
        # request_changes does not advance stage
        assert req.current_stage == ApprovalStage.DRAFT.value
        assert req.is_approved is False
        assert req.is_rejected is False
