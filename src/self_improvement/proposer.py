"""P28 ImprovementProposer — generates concrete proposals from prioritised gaps."""
from typing import Optional

from src.self_improvement.models import (
    ImprovementProposal, PrioritizedGap,
    CATEGORY_CAPABILITY_GAP, CATEGORY_PERFORMANCE, CATEGORY_RELIABILITY,
    CATEGORY_COST, CATEGORY_SECURITY,
    IMPL_CODE_CHANGE, IMPL_CONFIG_CHANGE, IMPL_NEW_CAPABILITY, IMPL_PROCESS_CHANGE,
    SEVERITY_CRITICAL, SEVERITY_HIGH,
)


class ImprovementProposer:
    """Generates concrete, actionable improvement proposals from gaps."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._proposals: list[ImprovementProposal] = []

    def propose(self, gaps: list[PrioritizedGap]) -> list[ImprovementProposal]:
        """Generate proposals for all gaps."""
        proposals = []
        for gap in gaps:
            p = self.generate_proposal(gap)
            proposals.append(p)
        self._proposals = proposals
        return proposals

    def generate_proposal(self, gap: PrioritizedGap) -> ImprovementProposal:
        """Generate a single concrete proposal from a gap."""
        title = self._generate_title(gap)
        impl_type = self._determine_implementation_type(gap)
        auto = self._can_auto_implement(impl_type)

        return ImprovementProposal.new(
            title=title,
            category=gap.pattern.category,
            severity=gap.urgency,
            current_state=gap.pattern.description,
            proposed_change=self._generate_change(gap),
            expected_impact=gap.impact_estimate,
            implementation_type=impl_type,
            auto_implementable=auto,
            evidence=gap.pattern.related_feedback_ids,
        )

    # ── Heuristics ────────────────────────────────────────────────

    def _generate_title(self, gap: PrioritizedGap) -> str:
        return f"Address: {gap.pattern.name}"

    def _determine_implementation_type(self, gap: PrioritizedGap) -> str:
        cat = gap.pattern.category
        if cat == CATEGORY_CAPABILITY_GAP:
            return IMPL_NEW_CAPABILITY
        if cat == CATEGORY_PERFORMANCE:
            return IMPL_CONFIG_CHANGE
        if cat == CATEGORY_SECURITY:
            return IMPL_PROCESS_CHANGE
        if cat == CATEGORY_COST:
            return IMPL_CONFIG_CHANGE
        return IMPL_CODE_CHANGE

    def _can_auto_implement(self, impl_type: str) -> bool:
        return impl_type in (IMPL_CODE_CHANGE, IMPL_CONFIG_CHANGE)

    def _generate_change(self, gap: PrioritizedGap) -> str:
        cat = gap.pattern.category
        if cat == CATEGORY_CAPABILITY_GAP:
            return f"Use P22 CapabilityForge to build: {gap.pattern.name}"
        if cat == CATEGORY_PERFORMANCE:
            return f"Tune configuration to reduce: {gap.pattern.name}"
        if cat == CATEGORY_RELIABILITY:
            return f"Add error handling for: {gap.pattern.name}"
        if cat == CATEGORY_COST:
            return f"Switch to cheaper model/provider for: {gap.pattern.name}"
        if cat == CATEGORY_SECURITY:
            return f"Add policy rule to detect: {gap.pattern.name}"
        return f"Investigate and fix: {gap.pattern.name}"

    # ── Validation ────────────────────────────────────────────────

    def validate_proposal(self, proposal: ImprovementProposal) -> list[str]:
        """Validate proposal quality. Returns list of issues (empty = valid)."""
        issues: list[str] = []
        if not proposal.title:
            issues.append("Proposal has empty title")
        if not proposal.proposed_change:
            issues.append("Proposal has no proposed change")
        if not proposal.implementation_type:
            issues.append("Proposal has no implementation type")
        if proposal.severity == SEVERITY_CRITICAL and not proposal.approved_by:
            issues.append("Critical proposal requires explicit approval")
        return issues

    def estimate_impact(self, proposal: ImprovementProposal) -> dict:
        """Estimate the expected impact of implementing a proposal."""
        return {
            "category": proposal.category,
            "confidence": "high" if proposal.auto_implementable else "medium",
            "estimated_effort": "low" if proposal.auto_implementable else "medium",
            "risk_of_regression": "high" if proposal.category == CATEGORY_SECURITY else "low",
        }

    # ── Query ─────────────────────────────────────────────────────

    def get_proposals(self) -> list[ImprovementProposal]:
        return list(self._proposals)

    @property
    def count(self) -> int:
        return len(self._proposals)
