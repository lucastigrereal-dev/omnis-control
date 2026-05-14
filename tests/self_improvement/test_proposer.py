"""Tests for P28 ImprovementProposer."""
import pytest

from src.self_improvement.proposer import ImprovementProposer
from src.self_improvement.models import (
    Pattern, PrioritizedGap,
    CATEGORY_CAPABILITY_GAP, CATEGORY_PERFORMANCE, CATEGORY_RELIABILITY,
    CATEGORY_COST, CATEGORY_SECURITY,
    IMPL_CODE_CHANGE, IMPL_CONFIG_CHANGE, IMPL_NEW_CAPABILITY, IMPL_PROCESS_CHANGE,
    SEVERITY_HIGH, SEVERITY_CRITICAL,
    PROPOSAL_DRAFT,
)


class TestImprovementProposer:
    @pytest.fixture
    def proposer(self):
        return ImprovementProposer(dry_run=True)

    def test_propose_from_gaps(self, proposer):
        pattern = Pattern.new("missing_auth", category=CATEGORY_CAPABILITY_GAP,
                              occurrences=4, confidence=0.8,
                              related_feedback_ids=["sif_a", "sif_b"])
        gap = PrioritizedGap.new(pattern, score=9.0, urgency=SEVERITY_HIGH)
        proposals = proposer.propose([gap])
        assert len(proposals) == 1
        assert proposals[0].category == CATEGORY_CAPABILITY_GAP
        assert proposals[0].severity == SEVERITY_HIGH
        assert proposals[0].is_actionable is True

    def test_capability_gap_becomes_new_capability(self, proposer):
        pattern = Pattern.new("missing X", category=CATEGORY_CAPABILITY_GAP, occurrences=2)
        gap = PrioritizedGap.new(pattern, score=5.0)
        proposal = proposer.generate_proposal(gap)
        assert proposal.implementation_type == IMPL_NEW_CAPABILITY
        assert "P22" in proposal.proposed_change

    def test_performance_gap_becomes_config_change(self, proposer):
        pattern = Pattern.new("slow_latency", category=CATEGORY_PERFORMANCE, occurrences=3)
        gap = PrioritizedGap.new(pattern, score=5.0)
        proposal = proposer.generate_proposal(gap)
        assert proposal.implementation_type == IMPL_CONFIG_CHANGE

    def test_security_gap_becomes_process_change(self, proposer):
        pattern = Pattern.new("vulnerable endpoint", category=CATEGORY_SECURITY, occurrences=2)
        gap = PrioritizedGap.new(pattern, score=10.0, urgency=SEVERITY_CRITICAL)
        proposal = proposer.generate_proposal(gap)
        assert proposal.implementation_type == IMPL_PROCESS_CHANGE

    def test_reliability_gap_becomes_code_change(self, proposer):
        pattern = Pattern.new("flakey_test", category=CATEGORY_RELIABILITY, occurrences=5)
        gap = PrioritizedGap.new(pattern, score=7.0)
        proposal = proposer.generate_proposal(gap)
        assert proposal.implementation_type == IMPL_CODE_CHANGE

    def test_auto_implementable_for_config(self, proposer):
        pattern = Pattern.new("tune", category=CATEGORY_PERFORMANCE)
        gap = PrioritizedGap.new(pattern, score=3.0)
        proposal = proposer.generate_proposal(gap)
        assert proposal.auto_implementable is True

    def test_not_auto_implementable_for_process(self, proposer):
        pattern = Pattern.new("process", category=CATEGORY_SECURITY)
        gap = PrioritizedGap.new(pattern, score=10.0, urgency=SEVERITY_CRITICAL)
        proposal = proposer.generate_proposal(gap)
        assert proposal.auto_implementable is False

    def test_validate_proposal_empty_title(self, proposer):
        from src.self_improvement.models import ImprovementProposal
        p = ImprovementProposal.new("")
        issues = proposer.validate_proposal(p)
        assert len(issues) >= 1

    def test_validate_proposal_empty_change(self, proposer):
        from src.self_improvement.models import ImprovementProposal
        p = ImprovementProposal.new("title")
        issues = proposer.validate_proposal(p)
        assert len(issues) >= 1  # no proposed_change = not actionable

    def test_validate_proposal_critical_without_approval(self, proposer):
        from src.self_improvement.models import ImprovementProposal
        p = ImprovementProposal.new("critical fix", category=CATEGORY_SECURITY,
                                    severity=SEVERITY_CRITICAL,
                                    proposed_change="Do X", implementation_type=IMPL_PROCESS_CHANGE)
        issues = proposer.validate_proposal(p)
        assert any("approval" in i.lower() for i in issues)

    def test_estimate_impact(self, proposer):
        from src.self_improvement.models import ImprovementProposal
        p = ImprovementProposal.new("test", category=CATEGORY_PERFORMANCE,
                                    proposed_change="Do X",
                                    implementation_type=IMPL_CONFIG_CHANGE,
                                    auto_implementable=True)
        impact = proposer.estimate_impact(p)
        assert "category" in impact
        assert "confidence" in impact
        assert "estimated_effort" in impact

    def test_count_increments(self, proposer):
        pattern = Pattern.new("p1", category=CATEGORY_RELIABILITY)
        gap = PrioritizedGap.new(pattern, score=1.0)
        assert proposer.count == 0
        proposer.propose([gap])
        assert proposer.count == 1

    def test_get_proposals_returns_all(self, proposer):
        gaps = [
            PrioritizedGap.new(Pattern.new("a", category=CATEGORY_RELIABILITY), score=2.0),
            PrioritizedGap.new(Pattern.new("b", category=CATEGORY_PERFORMANCE), score=1.0),
        ]
        proposer.propose(gaps)
        assert len(proposer.get_proposals()) == 2

    def test_cost_gap_becomes_config_change(self, proposer):
        pattern = Pattern.new("expensive calls", category=CATEGORY_COST, occurrences=3)
        gap = PrioritizedGap.new(pattern, score=4.0)
        proposal = proposer.generate_proposal(gap)
        assert proposal.implementation_type == IMPL_CONFIG_CHANGE
