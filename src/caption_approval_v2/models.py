"""P3 Caption Approval V2 — Data models.

All models are pure dataclasses. No I/O, no network, no LLM, no DB.
Deterministic and dry-run only.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_id() -> str:
    return uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DraftStatusV2(str, Enum):
    DRAFT = "draft"
    VARIANT_PROPOSED = "variant_proposed"
    CHECKLIST_BUILT = "checklist_built"
    POLICY_EVALUATED = "policy_evaluated"
    DECISION_PLANNED = "decision_planned"
    PACKAGE_VALID = "package_valid"
    PACKAGE_INVALID = "package_invalid"


class DecisionOutcome(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    PENDING = "pending"


class ChecklistSeverity(str, Enum):
    BLOCK = "block"
    WARN = "warn"
    INFO = "info"


class PolicyEffect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    FLAG = "flag"
    REQUIRE_REVIEW = "require_review"


class PolicyRule(str, Enum):
    MIN_CHARS = "min_chars"
    MAX_CHARS = "max_chars"
    HAS_HOOK = "has_hook"
    HAS_CTA = "has_cta"
    HAS_HASHTAGS = "has_hashtags"
    NO_BLOCKED_PLACEHOLDER = "no_blocked_placeholder"
    BRAND_VOICE_MATCH = "brand_voice_match"
    COMPLIANCE_CHECK = "compliance_check"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class CaptionDraftV2:
    """Immutable caption draft — plan only, never publishes."""

    draft_id: str = field(default_factory=_short_id)
    account_handle: str = ""
    caption_text: str = ""
    hashtags: list[str] = field(default_factory=list)
    cta: str = ""
    hook: str = ""
    objective: str = "alcance"
    content_format: str = "unknown"
    topic: str = ""
    notes: str = ""
    status: DraftStatusV2 = DraftStatusV2.DRAFT
    version: int = 1
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "draft_id": self.draft_id,
            "account_handle": self.account_handle,
            "caption_text": self.caption_text,
            "hashtags": self.hashtags,
            "cta": self.cta,
            "hook": self.hook,
            "objective": self.objective,
            "content_format": self.content_format,
            "topic": self.topic,
            "notes": self.notes,
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at,
        }

    def with_status(self, status: DraftStatusV2) -> "CaptionDraftV2":
        """Return a copy with a new status (immutable-style)."""
        return CaptionDraftV2(
            draft_id=self.draft_id,
            account_handle=self.account_handle,
            caption_text=self.caption_text,
            hashtags=list(self.hashtags),
            cta=self.cta,
            hook=self.hook,
            objective=self.objective,
            content_format=self.content_format,
            topic=self.topic,
            notes=self.notes,
            status=status,
            version=self.version,
            created_at=self.created_at,
        )


@dataclass
class CaptionVariant:
    """A single caption variant for A/B planning."""

    variant_id: str = field(default_factory=_short_id)
    draft_id: str = ""
    label: str = ""  # e.g. "A", "B", "curto", "longo"
    caption_text: str = ""
    hook: str = ""
    cta: str = ""
    hashtags: list[str] = field(default_factory=list)
    score: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "variant_id": self.variant_id,
            "draft_id": self.draft_id,
            "label": self.label,
            "caption_text": self.caption_text,
            "hook": self.hook,
            "cta": self.cta,
            "hashtags": self.hashtags,
            "score": self.score,
            "notes": self.notes,
        }


@dataclass
class CaptionChecklist:
    """Checklist of validation items for a caption draft."""

    checklist_id: str = field(default_factory=_short_id)
    draft_id: str = ""
    items: list[dict] = field(default_factory=list)
    blocks: int = 0
    warnings: int = 0
    infos: int = 0
    passed: bool = False

    def to_dict(self) -> dict:
        return {
            "checklist_id": self.checklist_id,
            "draft_id": self.draft_id,
            "items": self.items,
            "blocks": self.blocks,
            "warnings": self.warnings,
            "infos": self.infos,
            "passed": self.passed,
        }


@dataclass
class ApprovalDecision:
    """Planned approval decision — never executed against real queues."""

    decision_id: str = field(default_factory=_short_id)
    draft_id: str = ""
    outcome: DecisionOutcome = DecisionOutcome.PENDING
    reason: str = ""
    policy_checks: dict[str, bool] = field(default_factory=dict)
    checklist_id: str = ""
    decided_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "draft_id": self.draft_id,
            "outcome": self.outcome.value,
            "reason": self.reason,
            "policy_checks": self.policy_checks,
            "checklist_id": self.checklist_id,
            "decided_at": self.decided_at,
        }


@dataclass
class ApprovalPolicy:
    """Approval policy — set of rules that govern decisions."""

    policy_id: str = field(default_factory=_short_id)
    name: str = "default"
    rules: dict[PolicyRule, PolicyEffect] = field(default_factory=dict)
    min_chars: int = 10
    max_chars: int = 2200
    min_hashtags: int = 3
    blocked_placeholders: list[str] = field(default_factory=lambda: [
        "[HOOK A REVISAR]",
        "[CORPO DA LEGENDA A REVISAR]",
        "[CTA A DEFINIR]",
    ])
    require_hook: bool = True
    require_cta: bool = True

    def to_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "rules": {k.value: v.value for k, v in self.rules.items()},
            "min_chars": self.min_chars,
            "max_chars": self.max_chars,
            "min_hashtags": self.min_hashtags,
            "blocked_placeholders": self.blocked_placeholders,
            "require_hook": self.require_hook,
            "require_cta": self.require_cta,
        }

    @classmethod
    def default_policy(cls) -> "ApprovalPolicy":
        """Factory: standard policy with all rules set to FLAG."""
        return cls(
            name="default",
            rules={
                PolicyRule.MIN_CHARS: PolicyEffect.DENY,
                PolicyRule.MAX_CHARS: PolicyEffect.DENY,
                PolicyRule.HAS_HOOK: PolicyEffect.FLAG,
                PolicyRule.HAS_CTA: PolicyEffect.FLAG,
                PolicyRule.HAS_HASHTAGS: PolicyEffect.FLAG,
                PolicyRule.NO_BLOCKED_PLACEHOLDER: PolicyEffect.DENY,
                PolicyRule.BRAND_VOICE_MATCH: PolicyEffect.FLAG,
                PolicyRule.COMPLIANCE_CHECK: PolicyEffect.DENY,
            },
        )

    @classmethod
    def lenient_policy(cls) -> "ApprovalPolicy":
        """Factory: lenient policy — most rules are FLAG only."""
        return cls(
            name="lenient",
            rules={
                PolicyRule.MIN_CHARS: PolicyEffect.FLAG,
                PolicyRule.MAX_CHARS: PolicyEffect.FLAG,
                PolicyRule.HAS_HOOK: PolicyEffect.FLAG,
                PolicyRule.HAS_CTA: PolicyEffect.ALLOW,
                PolicyRule.HAS_HASHTAGS: PolicyEffect.ALLOW,
                PolicyRule.NO_BLOCKED_PLACEHOLDER: PolicyEffect.DENY,
                PolicyRule.BRAND_VOICE_MATCH: PolicyEffect.ALLOW,
                PolicyRule.COMPLIANCE_CHECK: PolicyEffect.FLAG,
            },
        )

    @classmethod
    def strict_policy(cls) -> "ApprovalPolicy":
        """Factory: strict policy — most rules DENY on violation."""
        return cls(
            name="strict",
            rules={
                PolicyRule.MIN_CHARS: PolicyEffect.DENY,
                PolicyRule.MAX_CHARS: PolicyEffect.DENY,
                PolicyRule.HAS_HOOK: PolicyEffect.DENY,
                PolicyRule.HAS_CTA: PolicyEffect.DENY,
                PolicyRule.HAS_HASHTAGS: PolicyEffect.DENY,
                PolicyRule.NO_BLOCKED_PLACEHOLDER: PolicyEffect.DENY,
                PolicyRule.BRAND_VOICE_MATCH: PolicyEffect.DENY,
                PolicyRule.COMPLIANCE_CHECK: PolicyEffect.DENY,
            },
        )


@dataclass
class CaptionApprovalPackage:
    """Complete approval package bundling draft + variants + checklist + decision."""

    package_id: str = field(default_factory=_short_id)
    draft: Optional[CaptionDraftV2] = None
    variants: list[CaptionVariant] = field(default_factory=list)
    checklist: Optional[CaptionChecklist] = None
    decision: Optional[ApprovalDecision] = None
    policy: Optional[ApprovalPolicy] = None
    valid: bool = False
    validation_errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "draft": self.draft.to_dict() if self.draft else None,
            "variants": [v.to_dict() for v in self.variants],
            "checklist": self.checklist.to_dict() if self.checklist else None,
            "decision": self.decision.to_dict() if self.decision else None,
            "policy": self.policy.to_dict() if self.policy else None,
            "valid": self.valid,
            "validation_errors": self.validation_errors,
            "created_at": self.created_at,
        }
