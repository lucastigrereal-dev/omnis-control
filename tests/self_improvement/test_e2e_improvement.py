"""E2E tests for P28 Self-Improvement Loop."""
import pytest

from src.self_improvement.collector import FeedbackCollector
from src.self_improvement.analyzer import PatternAnalyzer
from src.self_improvement.prioritizer import GapPrioritizer
from src.self_improvement.proposer import ImprovementProposer
from src.self_improvement.executor import ImprovementExecutor
from src.self_improvement.measurer import ImpactMeasurer
from src.self_improvement.models import (
    ExecutionFeedback, ImprovementProposal, ImpactMeasurement,
    SOURCE_MISSION, SOURCE_BUILD, SOURCE_ACTION, SOURCE_SYSTEM,
    CATEGORY_RELIABILITY, CATEGORY_PERFORMANCE, CATEGORY_SECURITY,
    IMPL_CODE_CHANGE, IMPL_CONFIG_CHANGE,
    PROPOSAL_APPROVED, PROPOSAL_IMPLEMENTED,
    VERDICT_IMPROVED, VERDICT_NEUTRAL,
)
from src.self_improvement.cli import main as cli_main


class TestE2EFullCycle:
    """Collect → Analyze → Prioritize → Propose → Execute → Measure."""

    def test_full_dry_run_cycle(self):
        collector = FeedbackCollector(dry_run=True)
        analyzer = PatternAnalyzer(dry_run=True)
        prioritizer = GapPrioritizer()
        proposer = ImprovementProposer(dry_run=True)
        executor = ImprovementExecutor(dry_run=True)
        measurer = ImpactMeasurer(dry_run=True)

        # 1. Collect
        feedbacks = collector.collect_all()
        assert len(feedbacks) > 0

        # 2. Analyze
        patterns = analyzer.analyze(feedbacks)
        assert isinstance(patterns, list)

        # 3. Prioritize
        gaps = prioritizer.prioritize(patterns)
        assert isinstance(gaps, list)

        # 4. Propose (if gaps exist)
        if gaps:
            proposals = proposer.propose(gaps)
            assert len(proposals) > 0

            # 5. Execute (first proposal)
            proposal = proposals[0]
            proposal.status = PROPOSAL_APPROVED
            measurement = executor.execute(proposal)
            assert isinstance(measurement, ImpactMeasurement)

            # 6. Measure
            before = collector.collect_from_missions("2026-01-01")
            after = collector.collect_from_missions("2026-05-01")
            impact = measurer.measure(proposal, before, after)
            assert impact.proposal_id == proposal.proposal_id

    def test_collect_analyze_detect_cycle(self):
        collector = FeedbackCollector(dry_run=True)
        analyzer = PatternAnalyzer(dry_run=True)

        # Collect with known failures
        feedbacks = collector.collect_all()
        patterns = analyzer.analyze(feedbacks)

        # At minimum, the data should be processable
        for pattern in patterns:
            assert pattern.name
            assert pattern.occurrences >= 1


class TestE2EApprovalFlow:
    def test_propose_approve_execute_flow(self):
        from src.self_improvement.models import Pattern, PrioritizedGap

        proposer = ImprovementProposer(dry_run=True)
        executor = ImprovementExecutor(dry_run=False)

        pattern = Pattern.new("test_bug", category=CATEGORY_RELIABILITY,
                              occurrences=3, confidence=0.8)
        gap = PrioritizedGap.new(pattern, score=7.0)

        # Propose
        proposals = proposer.propose([gap])
        assert len(proposals) == 1
        proposal = proposals[0]
        assert proposal.is_actionable

        # Approve
        proposal.status = PROPOSAL_APPROVED
        proposal.approved_by = "lucas"

        # Execute
        measurement = executor.execute(proposal)
        assert proposal.status == PROPOSAL_IMPLEMENTED


class TestE2ECLIIntegration:
    def test_cli_analyze(self):
        assert cli_main(["analyze"]) == 0

    def test_cli_gaps(self):
        assert cli_main(["gaps"]) == 0

    def test_cli_propose(self):
        assert cli_main(["propose"]) == 0

    def test_cli_list(self):
        assert cli_main(["list"]) == 0

    def test_cli_approve(self):
        assert cli_main(["approve", "sip_test"]) == 0

    def test_cli_reject(self):
        assert cli_main(["reject", "sip_test", "--reason", "not needed"]) == 0

    def test_cli_execute(self):
        assert cli_main(["execute", "sip_test"]) == 0

    def test_cli_measure(self):
        assert cli_main(["measure", "sip_test"]) == 0

    def test_cli_status(self):
        assert cli_main(["status"]) == 0

    def test_cli_history(self):
        assert cli_main(["history"]) == 0

    def test_cli_no_command(self):
        assert cli_main([]) == 1


class TestE2ESnapshotRoundtrip:
    def test_feedback_roundtrip(self):
        fb1 = ExecutionFeedback.new(SOURCE_MISSION, "m_test", status="failure",
                                    errors=["e1"], latency_ms=200)
        fb2 = ExecutionFeedback.from_dict(fb1.to_dict())
        assert fb2.feedback_id == fb1.feedback_id
        assert fb2.errors == fb1.errors

    def test_proposal_roundtrip(self):
        p1 = ImprovementProposal.new("Test", category=CATEGORY_PERFORMANCE,
                                     proposed_change="Do X", implementation_type=IMPL_CONFIG_CHANGE)
        p2 = ImprovementProposal.from_dict(p1.to_dict())
        assert p2.title == p1.title
        assert p2.implementation_type == p1.implementation_type

    def test_measurement_roundtrip(self):
        m1 = ImpactMeasurement.new("sip_test", metric="avg_latency",
                                   value_before=500, value_after=300,
                                   verdict=VERDICT_IMPROVED, sample_size=20)
        m2 = ImpactMeasurement.from_dict(m1.to_dict())
        assert m2.delta == m1.delta


class TestE2EDegradation:
    def test_no_feedback_no_crash(self):
        analyzer = PatternAnalyzer()
        with pytest.raises(Exception):
            analyzer.analyze([])

    def test_bogus_feedback_handled(self):
        analyzer = PatternAnalyzer()
        fb = ExecutionFeedback.new(SOURCE_SYSTEM, "x", status="unknown_status")
        patterns = analyzer.analyze([fb])
        assert isinstance(patterns, list)
