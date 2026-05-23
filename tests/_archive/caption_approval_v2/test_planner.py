"""Tests for P3 Caption Approval V2 planner service."""

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
from src.caption_approval_v2.planner import CaptionApprovalPlanner


class TestBuildCaptionDraft:
    def test_build_minimal(self):
        draft = CaptionApprovalPlanner.build_caption_draft()
        assert isinstance(draft, CaptionDraftV2)
        assert draft.draft_id
        assert draft.status == DraftStatusV2.DRAFT

    def test_build_full(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="lucastigrereal",
            caption_text="Explore as praias de Natal!",
            hashtags=["natal", "praias", "viagem"],
            cta="Arraste para ver mais!",
            hook="Você não vai acreditar no paraíso escondido...",
            objective="engajamento",
            content_format="carrossel",
            topic="Praias de Natal RN",
            notes="Cliente: Hotel X",
        )
        assert draft.account_handle == "lucastigrereal"
        assert "praias" in draft.caption_text
        assert len(draft.hashtags) == 3
        assert draft.hook.startswith("Você não vai")
        assert draft.content_format == "carrossel"

    def test_build_draft_is_deterministic_structure(self):
        """Same inputs produce same field values (except auto-generated IDs)."""
        a = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test", caption_text="Hello"
        )
        b = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test", caption_text="Hello"
        )
        assert a.account_handle == b.account_handle
        assert a.caption_text == b.caption_text
        # IDs are unique
        assert a.draft_id != b.draft_id


class TestGenerateCaptionVariants:
    def test_no_specs_produces_identity_variant(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="Original caption",
            hook="Original hook",
            cta="Original CTA",
        )
        variants = CaptionApprovalPlanner.generate_caption_variants(draft)
        assert len(variants) == 1
        assert variants[0].label == "original"
        assert variants[0].caption_text == "Original caption"
        assert variants[0].score == 1.0

    def test_with_specs_produces_multiple_variants(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="Base caption",
            hook="Base hook",
            cta="Base CTA",
        )
        specs = [
            {"label": "A", "hook": "Hook A", "score": 0.9},
            {"label": "B", "hook": "Hook B", "score": 0.7},
            {"label": "C", "cta": "CTA C", "score": 0.5},
        ]
        variants = CaptionApprovalPlanner.generate_caption_variants(draft, specs)
        assert len(variants) == 3
        assert variants[0].label == "A"
        assert variants[0].hook == "Hook A"
        assert variants[1].label == "B"
        assert variants[2].cta == "CTA C"

    def test_variants_inherit_from_draft(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="Inherited text",
            hashtags=["tag1", "tag2"],
        )
        specs = [{"label": "X"}]
        variants = CaptionApprovalPlanner.generate_caption_variants(draft, specs)
        assert variants[0].caption_text == "Inherited text"
        assert variants[0].hashtags == ["tag1", "tag2"]

    def test_variants_reference_draft_id(self):
        draft = CaptionApprovalPlanner.build_caption_draft(account_handle="test")
        variants = CaptionApprovalPlanner.generate_caption_variants(draft)
        assert variants[0].draft_id == draft.draft_id


class TestBuildApprovalChecklist:
    def test_valid_draft_passes(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="This is a valid caption with enough characters to pass",
            hook="Amazing hook here",
            cta="Click the link in bio!",
            hashtags=["tag1", "tag2", "tag3"],
        )
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft)
        assert checklist.passed
        assert checklist.blocks == 0
        assert len(checklist.items) > 0

    def test_short_caption_blocks(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="Short",
            hook="Hook",
            cta="CTA",
        )
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft)
        assert not checklist.passed
        assert checklist.blocks >= 1

    def test_empty_caption_blocks(self):
        draft = CaptionApprovalPlanner.build_caption_draft(account_handle="test")
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft)
        assert not checklist.passed
        assert checklist.blocks >= 1

    def test_blocked_placeholder_blocks(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="A caption with [HOOK A REVISAR] in the middle of text that is long enough",
        )
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft)
        assert not checklist.passed
        assert checklist.blocks >= 1

    def test_missing_hook_warns(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="A valid caption with enough characters to pass the min check",
            cta="Valid CTA here",
            hashtags=["t1", "t2", "t3"],
        )
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft)
        assert checklist.warnings >= 1

    def test_missing_cta_warns(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="A valid caption with enough characters to pass the min check",
            hook="Valid hook here",
            hashtags=["t1", "t2", "t3"],
        )
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft)
        assert checklist.warnings >= 1

    def test_few_hashtags_warns(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="A valid caption with enough characters to pass",
            hook="Hook", cta="CTA",
            hashtags=["t1"],
        )
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft)
        assert checklist.warnings >= 1

    def test_respects_custom_policy(self):
        policy = ApprovalPolicy(
            name="custom",
            rules={},
            min_chars=50,
            min_hashtags=10,
        )
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="Short",
            hashtags=["t1"],
        )
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft, policy)
        assert not checklist.passed

    def test_checklist_items_have_correct_structure(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="A valid caption with enough characters to pass the minimum check",
            hook="Hook here", cta="CTA here",
            hashtags=["t1", "t2", "t3"],
        )
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft)
        for item in checklist.items:
            assert "rule" in item
            assert "severity" in item
            assert "message" in item
            assert item["severity"] in ("block", "warn", "info")


class TestEvaluateCaptionPolicy:
    def test_all_pass_with_clean_checklist(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="A valid caption with enough characters to pass",
            hook="Hook", cta="CTA",
            hashtags=["t1", "t2", "t3"],
        )
        policy = ApprovalPolicy.default_policy()
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft, policy)
        results = CaptionApprovalPlanner.evaluate_caption_policy(checklist, policy)
        assert isinstance(results, dict)
        assert all(results.values())

    def test_fails_with_blocked_placeholder(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="Text with [HOOK A REVISAR] that is long enough for the test to run",
        )
        policy = ApprovalPolicy.default_policy()
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft, policy)
        results = CaptionApprovalPlanner.evaluate_caption_policy(checklist, policy)
        assert not results[PolicyRule.NO_BLOCKED_PLACEHOLDER.value]

    def test_lenient_policy_allows_more(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="A valid caption with enough characters to pass the minimum check",
            hook="Hook", cta="CTA",
            hashtags=["t1", "t2", "t3"],
        )
        policy = ApprovalPolicy.lenient_policy()
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft, policy)
        results = CaptionApprovalPlanner.evaluate_caption_policy(checklist, policy)
        # Lenient allows HAS_CTA unconditionally
        assert results[PolicyRule.HAS_CTA.value] is True

    def test_strict_policy_denies_warnings(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="This caption is long enough to pass the minimum character check",
            # No hook, no CTA — should fail strict
            hashtags=["t1", "t2", "t3"],
        )
        policy = ApprovalPolicy.strict_policy()
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft, policy)
        results = CaptionApprovalPlanner.evaluate_caption_policy(checklist, policy)
        # Strict policy denies missing hook
        assert not results[PolicyRule.HAS_HOOK.value]
        assert not results[PolicyRule.HAS_CTA.value]


class TestPlanApprovalDecision:
    def test_approved_when_all_pass(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="A valid caption with enough characters to pass",
            hook="Hook", cta="CTA",
            hashtags=["t1", "t2", "t3"],
        )
        policy = ApprovalPolicy.default_policy()
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft, policy)
        policy_checks = CaptionApprovalPlanner.evaluate_caption_policy(checklist, policy)
        decision = CaptionApprovalPlanner.plan_approval_decision(draft, checklist, policy_checks)
        assert decision.outcome == DecisionOutcome.APPROVED
        assert decision.draft_id == draft.draft_id
        assert decision.checklist_id == checklist.checklist_id

    def test_needs_revision_when_checklist_blocks(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="Short",
        )
        policy = ApprovalPolicy.default_policy()
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft, policy)
        policy_checks = CaptionApprovalPlanner.evaluate_caption_policy(checklist, policy)
        decision = CaptionApprovalPlanner.plan_approval_decision(draft, checklist, policy_checks)
        assert decision.outcome == DecisionOutcome.NEEDS_REVISION

    def test_decision_references_draft(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="A valid caption with enough characters to pass",
            hook="Hook", cta="CTA",
            hashtags=["t1", "t2", "t3"],
        )
        policy = ApprovalPolicy.default_policy()
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft, policy)
        policy_checks = CaptionApprovalPlanner.evaluate_caption_policy(checklist, policy)
        decision = CaptionApprovalPlanner.plan_approval_decision(draft, checklist, policy_checks)
        assert decision.draft_id == draft.draft_id


class TestValidateCaptionPackage:
    def test_complete_package_validates(self):
        draft = CaptionApprovalPlanner.build_caption_draft(
            account_handle="test",
            caption_text="A valid caption with enough characters to pass",
            hook="Hook", cta="CTA",
            hashtags=["t1", "t2", "t3"],
        )
        variants = CaptionApprovalPlanner.generate_caption_variants(draft)
        policy = ApprovalPolicy.default_policy()
        checklist = CaptionApprovalPlanner.build_approval_checklist(draft, policy)
        policy_checks = CaptionApprovalPlanner.evaluate_caption_policy(checklist, policy)
        decision = CaptionApprovalPlanner.plan_approval_decision(draft, checklist, policy_checks)

        pkg = CaptionApprovalPackage(
            draft=draft,
            variants=variants,
            checklist=checklist,
            decision=decision,
            policy=policy,
        )
        result = CaptionApprovalPlanner.validate_caption_package(pkg)
        assert result.valid
        assert result.validation_errors == []

    def test_missing_draft_fails(self):
        pkg = CaptionApprovalPackage(
            variants=[CaptionVariant()],
            checklist=CaptionChecklist(),
            decision=ApprovalDecision(),
            policy=ApprovalPolicy.default_policy(),
        )
        result = CaptionApprovalPlanner.validate_caption_package(pkg)
        assert not result.valid
        assert any("Missing draft" in e for e in result.validation_errors)

    def test_missing_checklist_fails(self):
        pkg = CaptionApprovalPackage(
            draft=CaptionDraftV2(account_handle="test"),
            variants=[CaptionVariant()],
            decision=ApprovalDecision(),
            policy=ApprovalPolicy.default_policy(),
        )
        result = CaptionApprovalPlanner.validate_caption_package(pkg)
        assert not result.valid
        assert any("Missing checklist" in e for e in result.validation_errors)

    def test_missing_decision_fails(self):
        pkg = CaptionApprovalPackage(
            draft=CaptionDraftV2(account_handle="test"),
            variants=[CaptionVariant()],
            checklist=CaptionChecklist(),
            policy=ApprovalPolicy.default_policy(),
        )
        result = CaptionApprovalPlanner.validate_caption_package(pkg)
        assert not result.valid
        assert any("Missing decision" in e for e in result.validation_errors)

    def test_no_variants_fails(self):
        pkg = CaptionApprovalPackage(
            draft=CaptionDraftV2(account_handle="test"),
            checklist=CaptionChecklist(),
            decision=ApprovalDecision(),
            policy=ApprovalPolicy.default_policy(),
        )
        result = CaptionApprovalPlanner.validate_caption_package(pkg)
        assert not result.valid
        assert any("No variants" in e for e in result.validation_errors)

    def test_missing_policy_fails(self):
        pkg = CaptionApprovalPackage(
            draft=CaptionDraftV2(account_handle="test"),
            variants=[CaptionVariant()],
            checklist=CaptionChecklist(),
            decision=ApprovalDecision(),
        )
        result = CaptionApprovalPlanner.validate_caption_package(pkg)
        assert not result.valid
        assert any("Missing policy" in e for e in result.validation_errors)

    def test_draft_without_account_handle_fails(self):
        draft = CaptionDraftV2(account_handle="")
        pkg = CaptionApprovalPackage(
            draft=draft,
            variants=[CaptionVariant()],
            checklist=CaptionChecklist(),
            decision=ApprovalDecision(),
            policy=ApprovalPolicy.default_policy(),
        )
        result = CaptionApprovalPlanner.validate_caption_package(pkg)
        assert not result.valid
        assert any("no account_handle" in e.lower() for e in result.validation_errors)

    def test_checklist_draft_id_mismatch_fails(self):
        draft = CaptionDraftV2(account_handle="test")
        pkg = CaptionApprovalPackage(
            draft=draft,
            variants=[CaptionVariant()],
            checklist=CaptionChecklist(draft_id="different-id"),
            decision=ApprovalDecision(),
            policy=ApprovalPolicy.default_policy(),
        )
        result = CaptionApprovalPlanner.validate_caption_package(pkg)
        assert not result.valid
        assert any("mismatch" in e.lower() for e in result.validation_errors)


class TestPlanFullApproval:
    def test_plan_full_pipeline(self):
        pkg = CaptionApprovalPlanner.plan_full_approval(
            account_handle="lucastigrereal",
            caption_text="Descubra as melhores praias de Natal em um carrossel imperdível!",
            hook="Você sabia que existe um paraíso escondido no RN?",
            cta="Salve para sua próxima viagem!",
            hashtags=["natal", "praias", "viagem", "turismo"],
            topic="Praias RN",
        )
        assert isinstance(pkg, CaptionApprovalPackage)
        assert pkg.draft is not None
        assert len(pkg.variants) >= 1
        assert pkg.checklist is not None
        assert pkg.decision is not None
        assert pkg.policy is not None
        assert pkg.valid

    def test_plan_full_with_variants(self):
        variant_specs = [
            {"label": "A", "hook": "Hook variante A", "score": 0.9},
            {"label": "B", "hook": "Hook variante B", "score": 0.8},
        ]
        pkg = CaptionApprovalPlanner.plan_full_approval(
            account_handle="afamiliatigrereal",
            caption_text="Dicas incríveis para viajar em família sem gastar muito!",
            hook="Viajar em família é mais fácil do que parece...",
            cta="Compartilhe com quem precisa ver isso!",
            hashtags=["família", "viagem", "dicas", "economia"],
            variant_specs=variant_specs,
        )
        assert len(pkg.variants) == 2
        assert pkg.variants[0].label == "A"
        assert pkg.variants[1].label == "B"

    def test_plan_full_with_custom_policy(self):
        policy = ApprovalPolicy.strict_policy()
        pkg = CaptionApprovalPlanner.plan_full_approval(
            account_handle="test",
            caption_text="A valid caption with enough characters",
            hook="Hook", cta="CTA",
            hashtags=["t1", "t2", "t3"],
            policy=policy,
        )
        assert pkg.policy.name == "strict"
        # With strict policy and all fields present, should be valid
        assert pkg.valid

    def test_plan_full_fails_with_blocked_placeholder(self):
        pkg = CaptionApprovalPlanner.plan_full_approval(
            account_handle="test",
            caption_text="Check out [HOOK A REVISAR] in this post about travel",
        )
        # Package structure is valid but checklist will have blocks
        # → decision outcome should not be APPROVED
        assert pkg.decision.outcome != DecisionOutcome.APPROVED

    def test_plan_full_result_is_serializable(self):
        pkg = CaptionApprovalPlanner.plan_full_approval(
            account_handle="lucastigrereal",
            caption_text="Conteúdo válido com caracteres suficientes para aprovação automática",
            hook="Gancho sensacional aqui",
            cta="Link na bio!",
            hashtags=["viagem", "brasil", "dicas"],
        )
        d = pkg.to_dict()
        assert isinstance(d, dict)
        assert d["valid"] is True
        assert d["draft"] is not None
        assert d["checklist"] is not None
        assert d["decision"] is not None
