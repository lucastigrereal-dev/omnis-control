"""P3 Caption Approval V2 — CaptionApprovalPlanner service.

All methods are pure functions operating on models.
No I/O, no network, no LLM, no DB, no queue mutation.
Every result is a plan/model — never executed against real systems.
"""

from typing import Optional

from .models import (
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
    _short_id,
)


class CaptionApprovalPlanner:
    """Plans approval decisions without executing them.

    All methods return models. Nothing is persisted, published, or enqueued.
    """

    # ------------------------------------------------------------------
    # build_caption_draft
    # ------------------------------------------------------------------

    @staticmethod
    def build_caption_draft(
        account_handle: str = "",
        caption_text: str = "",
        hashtags: Optional[list[str]] = None,
        cta: str = "",
        hook: str = "",
        objective: str = "alcance",
        content_format: str = "unknown",
        topic: str = "",
        notes: str = "",
    ) -> CaptionDraftV2:
        """Build a CaptionDraftV2 model. Dry-run — no persistence."""
        return CaptionDraftV2(
            account_handle=account_handle,
            caption_text=caption_text,
            hashtags=list(hashtags or []),
            cta=cta,
            hook=hook,
            objective=objective,
            content_format=content_format,
            topic=topic,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # generate_caption_variants
    # ------------------------------------------------------------------

    @staticmethod
    def generate_caption_variants(
        draft: CaptionDraftV2,
        variant_specs: Optional[list[dict]] = None,
    ) -> list[CaptionVariant]:
        """Generate caption variants from a draft.

        Each variant_spec is {"label": str, "hook": str, "cta": str, ...}
        If no specs given, produces a single identity variant.
        """
        if not variant_specs:
            return [
                CaptionVariant(
                    draft_id=draft.draft_id,
                    label="original",
                    caption_text=draft.caption_text,
                    hook=draft.hook,
                    cta=draft.cta,
                    hashtags=list(draft.hashtags),
                    score=1.0,
                    notes="Identity variant — original draft",
                )
            ]

        variants = []
        for i, spec in enumerate(variant_specs):
            label = spec.get("label", f"variant-{i}")
            variants.append(
                CaptionVariant(
                    draft_id=draft.draft_id,
                    label=label,
                    caption_text=spec.get("caption_text", draft.caption_text),
                    hook=spec.get("hook", draft.hook),
                    cta=spec.get("cta", draft.cta),
                    hashtags=spec.get("hashtags", list(draft.hashtags)),
                    score=float(spec.get("score", 0.0)),
                    notes=spec.get("notes", ""),
                )
            )
        return variants

    # ------------------------------------------------------------------
    # build_approval_checklist
    # ------------------------------------------------------------------

    @staticmethod
    def build_approval_checklist(
        draft: CaptionDraftV2,
        policy: Optional[ApprovalPolicy] = None,
    ) -> CaptionChecklist:
        """Build a validation checklist for a draft against a policy.

        If no policy given, uses the default policy.
        """
        policy = policy or ApprovalPolicy.default_policy()
        items: list[dict] = []

        # Min chars
        text = draft.caption_text or ""
        char_count = len(text)
        if char_count < policy.min_chars:
            items.append({
                "rule": PolicyRule.MIN_CHARS.value,
                "severity": ChecklistSeverity.BLOCK.value,
                "message": f"Caption too short ({char_count} < {policy.min_chars} chars)",
                "value": char_count,
                "threshold": policy.min_chars,
            })
        else:
            items.append({
                "rule": PolicyRule.MIN_CHARS.value,
                "severity": ChecklistSeverity.INFO.value,
                "message": f"Min chars OK ({char_count} >= {policy.min_chars})",
                "value": char_count,
                "threshold": policy.min_chars,
            })

        # Max chars
        if char_count > policy.max_chars:
            items.append({
                "rule": PolicyRule.MAX_CHARS.value,
                "severity": ChecklistSeverity.BLOCK.value,
                "message": f"Caption too long ({char_count} > {policy.max_chars} chars)",
                "value": char_count,
                "threshold": policy.max_chars,
            })
        else:
            items.append({
                "rule": PolicyRule.MAX_CHARS.value,
                "severity": ChecklistSeverity.INFO.value,
                "message": f"Max chars OK ({char_count} <= {policy.max_chars})",
                "value": char_count,
                "threshold": policy.max_chars,
            })

        # Has hook
        if policy.require_hook:
            if draft.hook and len(draft.hook.strip()) >= 3:
                items.append({
                    "rule": PolicyRule.HAS_HOOK.value,
                    "severity": ChecklistSeverity.INFO.value,
                    "message": "Hook present",
                    "value": draft.hook,
                    "threshold": None,
                })
            else:
                items.append({
                    "rule": PolicyRule.HAS_HOOK.value,
                    "severity": ChecklistSeverity.WARN.value,
                    "message": "Hook missing or too short",
                    "value": draft.hook or "",
                    "threshold": ">= 3 chars",
                })

        # Has CTA
        if policy.require_cta:
            if draft.cta and len(draft.cta.strip()) >= 3:
                items.append({
                    "rule": PolicyRule.HAS_CTA.value,
                    "severity": ChecklistSeverity.INFO.value,
                    "message": "CTA present",
                    "value": draft.cta,
                    "threshold": None,
                })
            else:
                items.append({
                    "rule": PolicyRule.HAS_CTA.value,
                    "severity": ChecklistSeverity.WARN.value,
                    "message": "CTA missing or too short",
                    "value": draft.cta or "",
                    "threshold": ">= 3 chars",
                })

        # Has hashtags
        if len(draft.hashtags) < policy.min_hashtags:
            items.append({
                "rule": PolicyRule.HAS_HASHTAGS.value,
                "severity": ChecklistSeverity.WARN.value,
                "message": f"Fewer than {policy.min_hashtags} hashtags ({len(draft.hashtags)})",
                "value": len(draft.hashtags),
                "threshold": policy.min_hashtags,
            })
        else:
            items.append({
                "rule": PolicyRule.HAS_HASHTAGS.value,
                "severity": ChecklistSeverity.INFO.value,
                "message": f"Hashtags OK ({len(draft.hashtags)} >= {policy.min_hashtags})",
                "value": len(draft.hashtags),
                "threshold": policy.min_hashtags,
            })

        # No blocked placeholders
        blocked_found = [p for p in policy.blocked_placeholders if p in text]
        if blocked_found:
            items.append({
                "rule": PolicyRule.NO_BLOCKED_PLACEHOLDER.value,
                "severity": ChecklistSeverity.BLOCK.value,
                "message": f"Blocked placeholders found: {', '.join(blocked_found)}",
                "value": blocked_found,
                "threshold": None,
            })
        else:
            items.append({
                "rule": PolicyRule.NO_BLOCKED_PLACEHOLDER.value,
                "severity": ChecklistSeverity.INFO.value,
                "message": "No blocked placeholders",
                "value": None,
                "threshold": None,
            })

        # Tally
        blocks = sum(1 for i in items if i["severity"] == ChecklistSeverity.BLOCK.value)
        warnings = sum(1 for i in items if i["severity"] == ChecklistSeverity.WARN.value)
        infos = sum(1 for i in items if i["severity"] == ChecklistSeverity.INFO.value)

        return CaptionChecklist(
            draft_id=draft.draft_id,
            items=items,
            blocks=blocks,
            warnings=warnings,
            infos=infos,
            passed=(blocks == 0),
        )

    # ------------------------------------------------------------------
    # evaluate_caption_policy
    # ------------------------------------------------------------------

    @staticmethod
    def evaluate_caption_policy(
        checklist: CaptionChecklist,
        policy: ApprovalPolicy,
    ) -> dict[str, bool]:
        """Evaluate each policy rule against checklist results.

        Returns {rule_name: passed} for each policy rule.
        """
        results: dict[str, bool] = {}
        item_map = {i["rule"]: i for i in checklist.items}

        for rule, effect in policy.rules.items():
            item = item_map.get(rule.value)
            if item is None:
                results[rule.value] = True
                continue

            is_block = item["severity"] == ChecklistSeverity.BLOCK.value
            is_warn = item["severity"] == ChecklistSeverity.WARN.value
            is_non_info = is_block or is_warn

            if effect == PolicyEffect.DENY and is_non_info:
                results[rule.value] = False
            elif effect == PolicyEffect.ALLOW:
                results[rule.value] = True
            elif effect == PolicyEffect.FLAG:
                results[rule.value] = not is_block
            elif effect == PolicyEffect.REQUIRE_REVIEW and is_non_info:
                results[rule.value] = False
            else:
                results[rule.value] = True

        return results

    # ------------------------------------------------------------------
    # plan_approval_decision
    # ------------------------------------------------------------------

    @staticmethod
    def plan_approval_decision(
        draft: CaptionDraftV2,
        checklist: CaptionChecklist,
        policy_checks: dict[str, bool],
    ) -> ApprovalDecision:
        """Plan an approval decision. Never executes — model only."""
        all_passed = all(policy_checks.values())

        if not checklist.passed:
            outcome = DecisionOutcome.NEEDS_REVISION
            failed = [r for r, v in policy_checks.items() if not v]
            reason = f"Checklist has {checklist.blocks} block(s). Failed rules: {', '.join(failed)}"
        elif all_passed:
            outcome = DecisionOutcome.APPROVED
            reason = "All policy checks passed"
        else:
            outcome = DecisionOutcome.NEEDS_REVISION
            failed = [r for r, v in policy_checks.items() if not v]
            reason = f"Policy checks failed: {', '.join(failed)}"

        return ApprovalDecision(
            draft_id=draft.draft_id,
            outcome=outcome,
            reason=reason,
            policy_checks=policy_checks,
            checklist_id=checklist.checklist_id,
        )

    # ------------------------------------------------------------------
    # validate_caption_package
    # ------------------------------------------------------------------

    @staticmethod
    def validate_caption_package(package: CaptionApprovalPackage) -> CaptionApprovalPackage:
        """Validate a complete approval package.

        Checks that all required components are present and consistent.
        Returns the package with `valid` and `validation_errors` populated.
        """
        errors: list[str] = []

        if package.draft is None:
            errors.append("Missing draft")
        else:
            if not package.draft.draft_id:
                errors.append("Draft has no draft_id")
            if not package.draft.account_handle:
                errors.append("Draft has no account_handle")

        if not package.variants:
            errors.append("No variants generated")

        if package.checklist is None:
            errors.append("Missing checklist")
        elif package.draft and package.checklist.draft_id != package.draft.draft_id:
            errors.append("Checklist draft_id mismatch")

        if package.decision is None:
            errors.append("Missing decision")
        elif package.draft and package.decision.draft_id != package.draft.draft_id:
            errors.append("Decision draft_id mismatch")

        if package.policy is None:
            errors.append("Missing policy")

        # Cross-reference: decision ↔ checklist
        if package.decision and package.checklist:
            if package.decision.checklist_id != package.checklist.checklist_id:
                errors.append("Decision checklist_id mismatch")

        package.valid = len(errors) == 0
        package.validation_errors = errors
        return package

    # ------------------------------------------------------------------
    # full_pipeline (convenience)
    # ------------------------------------------------------------------

    @classmethod
    def plan_full_approval(
        cls,
        account_handle: str,
        caption_text: str,
        hashtags: Optional[list[str]] = None,
        cta: str = "",
        hook: str = "",
        objective: str = "alcance",
        content_format: str = "unknown",
        topic: str = "",
        notes: str = "",
        variant_specs: Optional[list[dict]] = None,
        policy: Optional[ApprovalPolicy] = None,
    ) -> CaptionApprovalPackage:
        """Run the full approval planning pipeline.

        Builds draft → variants → checklist → policy eval → decision → validate.
        Returns a complete CaptionApprovalPackage.
        """
        policy = policy or ApprovalPolicy.default_policy()

        draft = cls.build_caption_draft(
            account_handle=account_handle,
            caption_text=caption_text,
            hashtags=hashtags,
            cta=cta,
            hook=hook,
            objective=objective,
            content_format=content_format,
            topic=topic,
            notes=notes,
        )

        variants = cls.generate_caption_variants(draft, variant_specs)
        checklist = cls.build_approval_checklist(draft, policy)
        policy_checks = cls.evaluate_caption_policy(checklist, policy)
        decision = cls.plan_approval_decision(draft, checklist, policy_checks)

        package = CaptionApprovalPackage(
            draft=draft,
            variants=variants,
            checklist=checklist,
            decision=decision,
            policy=policy,
        )

        return cls.validate_caption_package(package)
