"""Tests for P3 Caption Approval V2 models."""

import pytest

from src.caption_approval_v2.models import (
    CaptionDraftV2,
    CaptionVariant,
    CaptionChecklist,
    ApprovalDecision,
    ApprovalPolicy,
    CaptionApprovalPackage,
    DraftStatusV2,
    DecisionOutcome,
    ChecklistSeverity,
    PolicyEffect,
    PolicyRule,
)


class TestCaptionDraftV2:
    def test_defaults(self):
        draft = CaptionDraftV2()
        assert draft.draft_id
        assert draft.status == DraftStatusV2.DRAFT
        assert draft.version == 1
        assert draft.hashtags == []
        assert draft.account_handle == ""

    def test_custom_values(self):
        draft = CaptionDraftV2(
            account_handle="lucastigrereal",
            caption_text="Hello world",
            hashtags=["travel", "family"],
            cta="Click the link!",
            hook="You won't believe this...",
            objective="alcance",
            content_format="carrossel",
            topic="viagem em família",
        )
        assert draft.account_handle == "lucastigrereal"
        assert draft.caption_text == "Hello world"
        assert len(draft.hashtags) == 2
        assert draft.cta == "Click the link!"
        assert draft.hook == "You won't believe this..."

    def test_to_dict(self):
        draft = CaptionDraftV2(
            account_handle="test",
            caption_text="Test caption",
        )
        d = draft.to_dict()
        assert d["account_handle"] == "test"
        assert d["caption_text"] == "Test caption"
        assert d["status"] == "draft"
        assert isinstance(d["hashtags"], list)

    def test_with_status_returns_new_instance(self):
        draft = CaptionDraftV2(account_handle="test")
        updated = draft.with_status(DraftStatusV2.CHECKLIST_BUILT)
        assert updated.status == DraftStatusV2.CHECKLIST_BUILT
        assert draft.status == DraftStatusV2.DRAFT
        assert updated.draft_id == draft.draft_id
        assert updated is not draft

    def test_each_draft_has_unique_id(self):
        a = CaptionDraftV2()
        b = CaptionDraftV2()
        assert a.draft_id != b.draft_id


class TestCaptionVariant:
    def test_defaults(self):
        v = CaptionVariant()
        assert v.variant_id
        assert v.score == 0.0
        assert v.hashtags == []

    def test_custom_values(self):
        v = CaptionVariant(
            draft_id="abc123",
            label="B",
            caption_text="Test variant",
            hook="Variant hook",
            cta="Variant CTA",
            score=0.85,
        )
        assert v.label == "B"
        assert v.score == 0.85
        assert v.draft_id == "abc123"

    def test_to_dict(self):
        v = CaptionVariant(draft_id="x", label="A", score=0.5)
        d = v.to_dict()
        assert d["draft_id"] == "x"
        assert d["label"] == "A"
        assert d["score"] == 0.5


class TestCaptionChecklist:
    def test_defaults(self):
        c = CaptionChecklist()
        assert c.checklist_id
        assert c.items == []
        assert c.blocks == 0
        assert c.warnings == 0
        assert not c.passed

    def test_passed_when_no_blocks(self):
        c = CaptionChecklist(blocks=0, passed=True)
        assert c.passed

    def test_not_passed_when_blocks(self):
        c = CaptionChecklist(blocks=2, passed=False)
        assert not c.passed

    def test_to_dict(self):
        c = CaptionChecklist(
            draft_id="d1",
            items=[{"rule": "min_chars", "severity": "info"}],
            blocks=0, warnings=1, infos=5, passed=True,
        )
        d = c.to_dict()
        assert d["draft_id"] == "d1"
        assert len(d["items"]) == 1
        assert d["passed"] is True


class TestApprovalDecision:
    def test_defaults(self):
        d = ApprovalDecision()
        assert d.decision_id
        assert d.outcome == DecisionOutcome.PENDING
        assert d.policy_checks == {}

    def test_approved_outcome(self):
        d = ApprovalDecision(
            draft_id="d1",
            outcome=DecisionOutcome.APPROVED,
            reason="All checks passed",
            policy_checks={"min_chars": True, "has_cta": True},
        )
        assert d.outcome == DecisionOutcome.APPROVED
        assert len(d.policy_checks) == 2

    def test_to_dict(self):
        d = ApprovalDecision(
            draft_id="d1",
            outcome=DecisionOutcome.REJECTED,
            reason="Blocked placeholder",
        )
        out = d.to_dict()
        assert out["outcome"] == "rejected"
        assert out["reason"] == "Blocked placeholder"


class TestApprovalPolicy:
    def test_default_policy(self):
        p = ApprovalPolicy.default_policy()
        assert p.name == "default"
        assert PolicyRule.MIN_CHARS in p.rules
        assert p.rules[PolicyRule.MIN_CHARS] == PolicyEffect.DENY
        assert p.rules[PolicyRule.NO_BLOCKED_PLACEHOLDER] == PolicyEffect.DENY

    def test_lenient_policy(self):
        p = ApprovalPolicy.lenient_policy()
        assert p.name == "lenient"
        assert p.rules[PolicyRule.HAS_CTA] == PolicyEffect.ALLOW

    def test_strict_policy(self):
        p = ApprovalPolicy.strict_policy()
        assert p.name == "strict"
        assert p.rules[PolicyRule.HAS_HOOK] == PolicyEffect.DENY

    def test_to_dict(self):
        p = ApprovalPolicy.default_policy()
        d = p.to_dict()
        assert d["name"] == "default"
        assert "min_chars" in d["rules"]
        assert d["min_chars"] == 10

    def test_blocked_placeholders_default(self):
        p = ApprovalPolicy.default_policy()
        assert "[HOOK A REVISAR]" in p.blocked_placeholders


class TestCaptionApprovalPackage:
    def test_defaults(self):
        pkg = CaptionApprovalPackage()
        assert pkg.package_id
        assert not pkg.valid
        assert pkg.variants == []
        assert pkg.validation_errors == []

    def test_valid_package(self):
        draft = CaptionDraftV2(account_handle="test")
        pkg = CaptionApprovalPackage(
            draft=draft,
            variants=[CaptionVariant(draft_id=draft.draft_id)],
            checklist=CaptionChecklist(draft_id=draft.draft_id),
            decision=ApprovalDecision(draft_id=draft.draft_id),
            policy=ApprovalPolicy.default_policy(),
            valid=True,
        )
        assert pkg.valid
        assert pkg.draft.account_handle == "test"

    def test_to_dict(self):
        pkg = CaptionApprovalPackage(
            draft=CaptionDraftV2(account_handle="test"),
            valid=True,
        )
        d = pkg.to_dict()
        assert d["valid"] is True
        assert d["draft"]["account_handle"] == "test"


class TestEnums:
    def test_draft_status_values(self):
        assert DraftStatusV2.DRAFT.value == "draft"
        assert DraftStatusV2.PACKAGE_VALID.value == "package_valid"

    def test_decision_outcome_values(self):
        assert DecisionOutcome.APPROVED.value == "approved"
        assert DecisionOutcome.NEEDS_REVISION.value == "needs_revision"

    def test_checklist_severity_values(self):
        assert ChecklistSeverity.BLOCK.value == "block"
        assert ChecklistSeverity.WARN.value == "warn"

    def test_policy_effect_values(self):
        assert PolicyEffect.DENY.value == "deny"
        assert PolicyEffect.ALLOW.value == "allow"

    def test_policy_rule_values(self):
        assert PolicyRule.MIN_CHARS.value == "min_chars"
        assert PolicyRule.HAS_HOOK.value == "has_hook"
