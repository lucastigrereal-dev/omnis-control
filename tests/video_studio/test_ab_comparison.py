"""Tests for A/B comparison."""

import pytest

from src.video_studio.models import (
    VideoSource, VideoSourceKind, CutPlan, CutInstruction, CutType,
    ReelScript, ReelFormat, ReelSegment, VideoPackage, HookCandidate, HookStrength,
)
from src.video_studio.ab_comparison import ABComparator, ABComparison, ABDiff


@pytest.fixture
def source():
    return VideoSource.new(
        kind=VideoSourceKind.RAW,
        uri_hint="/videos/reel.mp4",
        duration_seconds=60.0,
        width=1920,
        height=1080,
    )


@pytest.fixture
def sample_package_a(source):
    plan = CutPlan.new(source.source_id)
    plan.add_cut(CutInstruction.new(0, 10, CutType.KEEP, "Intro"))
    plan.add_cut(CutInstruction.new(15, 25, CutType.KEEP, "Main"))

    script = ReelScript.new(source.source_id, plan.plan_id, ReelFormat.SHORT, "Hotel Natal")
    script.add_segment(ReelSegment(position=1, start_seconds=0, end_seconds=10, narration="Intro narration"))
    script.add_segment(ReelSegment(position=2, start_seconds=15, end_seconds=25, narration="Main content"))

    pkg = VideoPackage.new(source, plan, script)
    pkg.add_hook(HookCandidate.new(
        plan.cuts[0].cut_id, 0, 3, "Voce precisa conhecer esse hotel!",
        HookStrength.HIGH, 0.9, "Strong emotional hook",
    ))
    pkg.add_hook(HookCandidate.new(
        plan.cuts[1].cut_id, 15, 18, "Look at this view!",
        HookStrength.MEDIUM, 0.6, "Visual hook",
    ))
    pkg.validate()
    return pkg


@pytest.fixture
def sample_package_b(source):
    plan = CutPlan.new(source.source_id)
    plan.add_cut(CutInstruction.new(5, 20, CutType.KEEP, "Extended Intro"))
    plan.add_cut(CutInstruction.new(25, 35, CutType.KEEP, "Main"))
    plan.add_cut(CutInstruction.new(40, 55, CutType.KEEP, "Outro"))

    script = ReelScript.new(source.source_id, plan.plan_id, ReelFormat.STANDARD, "Hotel Natal Extended")
    script.add_segment(ReelSegment(position=1, start_seconds=5, end_seconds=20, narration="Extended intro"))
    script.add_segment(ReelSegment(position=2, start_seconds=25, end_seconds=35, narration="Main"))
    script.add_segment(ReelSegment(position=3, start_seconds=40, end_seconds=55, narration="Outro"))

    pkg = VideoPackage.new(source, plan, script)
    pkg.add_hook(HookCandidate.new(
        plan.cuts[0].cut_id, 5, 8, "Hotel incrivel no nordeste!",
        HookStrength.HIGH, 0.7, "Informative hook",
    ))
    pkg.validate()
    return pkg


class TestABComparison:
    def test_construction(self):
        c = ABComparison(
            comparison_id="test-01", title="Test Comparison",
            package_a_id="pkg-a", package_b_id="pkg-b",
        )
        assert c.package_a_id == "pkg-a"
        assert c.winner is None
        assert not c.is_tie

    def test_to_dict_roundtrip(self):
        c = ABComparison(
            comparison_id="c1", title="T1",
            package_a_id="a", package_b_id="b",
            winner="A", score_a=10.0, score_b=5.0,
            differences=[ABDiff(field="test", value_a="1", value_b="2", verdict="a_better")],
        )
        d = c.to_dict()
        restored = ABComparison.from_dict(d)
        assert restored.winner == "A"
        assert restored.score_a == 10.0
        assert len(restored.differences) == 1


class TestABDiff:
    def test_construction(self):
        d = ABDiff(field="hook_count", value_a="3", value_b="1", verdict="a_better", weight=1.5)
        assert d.field == "hook_count"
        assert d.weight == 1.5

    def test_to_dict_roundtrip(self):
        d = ABDiff(field="f1", value_a="a", value_b="b", verdict="b_better")
        data = d.to_dict()
        restored = ABDiff.from_dict(data)
        assert restored.field == "f1"
        assert restored.verdict == "b_better"


class TestABComparator:
    def test_compare_returns_result(self, sample_package_a, sample_package_b):
        comparator = ABComparator()
        result = comparator.compare(sample_package_a, sample_package_b, "Test A/B")
        assert result.comparison_id
        assert result.package_a_id == sample_package_a.package_id
        assert result.package_b_id == sample_package_b.package_id
        assert result.winner is not None  # A, B, or tie
        assert len(result.differences) >= 4
        assert result.recommendation

    def test_compare_identical(self, sample_package_a):
        comparator = ABComparator()
        result = comparator.compare(sample_package_a, sample_package_a, "Same vs Same")
        assert result.winner == "tie"
        assert result.is_tie

    def test_winner_has_higher_score(self, sample_package_a, sample_package_b):
        comparator = ABComparator()
        result = comparator.compare(sample_package_a, sample_package_b)
        if result.winner == "A":
            assert result.score_a >= result.score_b
        elif result.winner == "B":
            assert result.score_b >= result.score_a
        else:
            assert abs(result.score_a - result.score_b) < 0.5

    def test_differences_cover_key_fields(self, sample_package_a, sample_package_b):
        comparator = ABComparator()
        result = comparator.compare(sample_package_a, sample_package_b)
        fields = {d.field for d in result.differences}
        assert "strongest_hook_score" in fields
        assert "hook_count" in fields
        assert "total_clips" in fields
        assert "validation" in fields
