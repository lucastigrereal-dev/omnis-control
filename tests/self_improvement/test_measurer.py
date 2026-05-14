"""Tests for P28 ImpactMeasurer."""
import pytest

from src.self_improvement.measurer import ImpactMeasurer
from src.self_improvement.models import (
    ImprovementProposal, ExecutionFeedback, ImpactMeasurement,
    SOURCE_MISSION, SOURCE_BUILD,
    CATEGORY_PERFORMANCE, CATEGORY_RELIABILITY, CATEGORY_COST, CATEGORY_SECURITY,
    VERDICT_IMPROVED, VERDICT_DEGRADED, VERDICT_NEUTRAL, VERDICT_INSUFFICIENT_DATA,
    PROPOSAL_MEASURED,
)


class TestImpactMeasurer:
    @pytest.fixture
    def measurer(self):
        return ImpactMeasurer(dry_run=True)

    def test_measure_computes_delta(self, measurer):
        proposal = ImprovementProposal.new("Tune latency", category=CATEGORY_PERFORMANCE,
                                           proposed_change="Do X",
                                           implementation_type="config_change")
        before = [
            ExecutionFeedback.new(SOURCE_MISSION, "m1", latency_ms=500),
            ExecutionFeedback.new(SOURCE_MISSION, "m2", latency_ms=600),
        ]
        after = [
            ExecutionFeedback.new(SOURCE_MISSION, "m3", latency_ms=300),
            ExecutionFeedback.new(SOURCE_MISSION, "m4", latency_ms=400),
        ]
        m = measurer.measure(proposal, before, after)
        assert m.metric == "avg_latency_ms"
        assert m.value_before == pytest.approx(550)
        assert m.value_after == pytest.approx(350)
        assert m.delta == pytest.approx(-200)

    def test_measure_latency_reduction_verdict_improved(self, measurer):
        proposal = ImprovementProposal.new("Tune", category=CATEGORY_PERFORMANCE,
                                           proposed_change="X", implementation_type="config")
        before = [ExecutionFeedback.new(SOURCE_MISSION, "m1", latency_ms=1000)]
        after = [ExecutionFeedback.new(SOURCE_MISSION, "m2", latency_ms=500)]
        m = measurer.measure(proposal, before, after)
        assert m.verdict == VERDICT_IMPROVED

    def test_measure_success_rate_improvement_verdict_improved(self, measurer):
        proposal = ImprovementProposal.new("Fix", category="capability_gap",
                                           proposed_change="X", implementation_type="code")
        before = [ExecutionFeedback.new(SOURCE_MISSION, "m1", status="failure")]
        after = [ExecutionFeedback.new(SOURCE_MISSION, "m2", status="success")]
        m = measurer.measure(proposal, before, after)
        assert m.verdict == VERDICT_IMPROVED

    def test_measure_insufficient_with_empty_data(self, measurer):
        proposal = ImprovementProposal.new("Test", category=CATEGORY_RELIABILITY,
                                           proposed_change="X", implementation_type="code")
        m = measurer.measure(proposal, [], [])
        assert m.verdict == VERDICT_INSUFFICIENT_DATA

    def test_measure_sets_proposal_status(self, measurer):
        proposal = ImprovementProposal.new("Test", category=CATEGORY_RELIABILITY,
                                           proposed_change="X", implementation_type="code")
        before = [ExecutionFeedback.new(SOURCE_MISSION, "m1")]
        after = [ExecutionFeedback.new(SOURCE_MISSION, "m2")]
        measurer.measure(proposal, before, after)
        assert proposal.status == PROPOSAL_MEASURED

    def test_compare_metrics(self, measurer):
        result = measurer.compare_metrics("latency", [500, 600], [300, 400])
        assert result["avg_before"] == pytest.approx(550)
        assert result["avg_after"] == pytest.approx(350)
        assert "change_pct" in result

    def test_compare_metrics_empty_data(self, measurer):
        result = measurer.compare_metrics("test", [], [])
        assert result["verdict"] == VERDICT_INSUFFICIENT_DATA

    def test_is_significant_requires_min_samples(self, measurer):
        m = ImpactMeasurement.new("sip_test", sample_size=3, value_before=1.0,
                                  value_after=2.0)  # delta=1 but not enough samples
        # Recalculate verdict with proper delta
        import copy
        m2 = copy.copy(m)
        m2.sample_size = 3
        m2.delta = 1.0
        assert measurer.is_significant(m2) is False  # sample < 5

        m3 = copy.copy(m)
        m3.sample_size = 10
        m3.delta = 1.0
        assert measurer.is_significant(m3) is True

    def test_count_tracks_measurements(self, measurer):
        proposal = ImprovementProposal.new("Test", category=CATEGORY_RELIABILITY,
                                           proposed_change="X", implementation_type="code")
        before = [ExecutionFeedback.new(SOURCE_MISSION, "m1")]
        after = [ExecutionFeedback.new(SOURCE_MISSION, "m2")]
        assert measurer.count == 0
        measurer.measure(proposal, before, after)
        assert measurer.count == 1

    def test_failure_rate_improvement_detected(self, measurer):
        proposal = ImprovementProposal.new("Fix bug", category=CATEGORY_RELIABILITY,
                                           proposed_change="X", implementation_type="code")
        before = [
            ExecutionFeedback.new(SOURCE_MISSION, "m1", status="failure", errors=["e"]),
            ExecutionFeedback.new(SOURCE_MISSION, "m2", status="failure", errors=["e"]),
        ]
        after = [
            ExecutionFeedback.new(SOURCE_MISSION, "m3", status="success"),
            ExecutionFeedback.new(SOURCE_MISSION, "m4", status="success"),
        ]
        m = measurer.measure(proposal, before, after)
        assert m.metric == "failure_rate"
        assert m.value_before == pytest.approx(1.0)
        assert m.value_after == pytest.approx(0.0)
        assert m.verdict == VERDICT_IMPROVED
