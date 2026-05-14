"""Tests for P28 GapPrioritizer."""
import pytest

from src.self_improvement.prioritizer import GapPrioritizer
from src.self_improvement.models import (
    Pattern, PrioritizedGap,
    CATEGORY_SECURITY, CATEGORY_RELIABILITY, CATEGORY_PERFORMANCE, CATEGORY_COST,
    SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW,
)


class TestGapPrioritizer:
    @pytest.fixture
    def prioritizer(self):
        return GapPrioritizer()

    def test_prioritize_returns_gaps(self, prioritizer):
        patterns = [
            Pattern.new("p1", category=CATEGORY_SECURITY, occurrences=5, confidence=0.9),
            Pattern.new("p2", category=CATEGORY_PERFORMANCE, occurrences=2, confidence=0.5),
        ]
        gaps = prioritizer.prioritize(patterns)
        assert len(gaps) == 2
        assert all(isinstance(g, PrioritizedGap) for g in gaps)

    def test_security_scores_higher_than_performance(self, prioritizer):
        security = [Pattern.new("s", category=CATEGORY_SECURITY, occurrences=2, confidence=0.5)]
        performance = [Pattern.new("p", category=CATEGORY_PERFORMANCE, occurrences=2, confidence=0.5)]

        sec_gap = prioritizer.prioritize(security)[0]
        perf_gap = prioritizer.prioritize(performance)[0]
        assert sec_gap.score > perf_gap.score

    def test_more_occurrences_scores_higher(self, prioritizer):
        p_few = [Pattern.new("f", category=CATEGORY_PERFORMANCE, occurrences=1, confidence=0.5)]
        p_many = [Pattern.new("m", category=CATEGORY_PERFORMANCE, occurrences=10, confidence=0.5)]

        few_gap = prioritizer.prioritize(p_few)[0]
        many_gap = prioritizer.prioritize(p_many)[0]
        assert many_gap.score > few_gap.score

    def test_rank_assigns_sequential(self, prioritizer):
        patterns = [
            Pattern.new("a", category=CATEGORY_RELIABILITY, occurrences=5),
            Pattern.new("b", category=CATEGORY_PERFORMANCE, occurrences=2),
            Pattern.new("c", category=CATEGORY_COST, occurrences=1),
        ]
        gaps = prioritizer.prioritize(patterns)
        ranks = [g.rank for g in gaps]
        assert ranks == [1, 2, 3]

    def test_top_n_limits(self, prioritizer):
        patterns = [Pattern.new(f"p{i}", category=CATEGORY_PERFORMANCE, occurrences=i) for i in range(1, 8)]
        prioritizer.prioritize(patterns)
        assert len(prioritizer.top_n(3)) == 3

    def test_gaps_count(self, prioritizer):
        patterns = [Pattern.new("a", category=CATEGORY_PERFORMANCE, occurrences=1)]
        prioritizer.prioritize(patterns)
        assert prioritizer.count == 1

    def test_high_occurrences_derives_critical_urgency(self, prioritizer):
        patterns = [Pattern.new("h", category=CATEGORY_PERFORMANCE, occurrences=7)]
        gaps = prioritizer.prioritize(patterns)
        assert gaps[0].urgency == SEVERITY_CRITICAL

    def test_medium_occurrences_high_urgency(self, prioritizer):
        patterns = [Pattern.new("m", category=CATEGORY_PERFORMANCE, occurrences=3)]
        gaps = prioritizer.prioritize(patterns)
        assert gaps[0].urgency == SEVERITY_HIGH

    def test_get_gaps_returns_all(self, prioritizer):
        patterns = [Pattern.new("a", category=CATEGORY_RELIABILITY), Pattern.new("b", category=CATEGORY_PERFORMANCE)]
        prioritizer.prioritize(patterns)
        assert len(prioritizer.get_gaps()) == 2

    def test_empty_list(self, prioritizer):
        gaps = prioritizer.prioritize([])
        assert gaps == []
        assert prioritizer.count == 0
        assert prioritizer.top_n(5) == []
