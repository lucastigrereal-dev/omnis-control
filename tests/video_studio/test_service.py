"""Testes do servico VideoStudioPlanner."""
from __future__ import annotations

from src.video_studio.errors import (
    InvalidCutPlanError,
    InvalidReelScriptError,
    InvalidTranscriptError,
    InvalidVideoPackageError,
    ValidationError,
)
from src.video_studio.models import (
    CaptionOverlaySpec,
    CutPlan,
    CutType,
    HookCandidate,
    HookStrength,
    ReelFormat,
    ReelScript,
    ReelSegment,
    TranscriptSegment,
    VideoPackage,
    VideoSource,
    VideoSourceKind,
)
from src.video_studio.service import (
    VideoStudioPlanner,
    analyze_transcript_segments,
    build_cut_plan,
    build_reel_script,
    build_video_package,
    detect_hook_candidates,
    validate_video_package,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_source(duration: float = 120.0) -> VideoSource:
    return VideoSource.new(VideoSourceKind.RAW, "test/source.mp4", duration)


def _make_segments() -> list[TranscriptSegment]:
    return [
        TranscriptSegment.new(0.0, 5.0, "Hey everyone welcome back to the channel today"),
        TranscriptSegment.new(5.0, 12.0, "I am going to show you the top five destinations"),
        TranscriptSegment.new(12.0, 18.0, "for family travel this summer in Brazil"),
        TranscriptSegment.new(18.0, 22.0, "ok so"),
        TranscriptSegment.new(22.0, 30.0, "the first place is absolutely incredible you will love it"),
        TranscriptSegment.new(30.0, 45.0, "and then we have an amazing resort with pools and activities"),
        TranscriptSegment.new(45.0, 50.0, "um"),
        TranscriptSegment.new(50.0, 65.0, "dont forget to subscribe and hit the bell for more travel tips every week"),
    ]


# ---------------------------------------------------------------------------
# VideoStudioPlanner
# ---------------------------------------------------------------------------

class TestVideoStudioPlanner:
    def test_planner_instantiation(self):
        planner = VideoStudioPlanner()
        assert planner is not None
        assert planner._last_package is None

    def test_analyze_transcript_segments(self):
        planner = VideoStudioPlanner()
        segments = _make_segments()
        result = planner.analyze_transcript_segments(segments)
        assert result["total_segments"] == 8
        assert result["total_duration_seconds"] == 65.0
        assert result["total_words"] > 0
        assert 0.0 <= result["avg_confidence"] <= 1.0
        assert result["speakers"] == []

    def test_analyze_empty_raises(self):
        planner = VideoStudioPlanner()
        try:
            planner.analyze_transcript_segments([])
            assert False, "deveria ter lancado InvalidTranscriptError"
        except InvalidTranscriptError:
            pass

    def test_detect_hook_candidates(self):
        planner = VideoStudioPlanner()
        segments = _make_segments()
        hooks = planner.detect_hook_candidates(segments)
        assert len(hooks) > 0
        for hook in hooks:
            assert hook.hook_id.startswith("hk_")
            assert hook.strength in HookStrength
            assert 0.0 <= hook.score <= 1.0

    def test_detect_hook_candidates_empty(self):
        planner = VideoStudioPlanner()
        hooks = planner.detect_hook_candidates([])
        assert hooks == []

    def test_detect_hook_candidates_short_segments_ignored(self):
        planner = VideoStudioPlanner()
        segments = [
            TranscriptSegment.new(0.0, 2.0, "hi"),       # 1 word, < 5
            TranscriptSegment.new(2.0, 4.0, "ok um uh"),  # 3 words, < 5
        ]
        hooks = planner.detect_hook_candidates(segments)
        assert hooks == []

    def test_build_cut_plan(self):
        planner = VideoStudioPlanner()
        source = _make_source()
        segments = _make_segments()
        hooks = planner.detect_hook_candidates(segments)
        plan = planner.build_cut_plan(source, segments, hooks)
        assert plan.source_id == source.source_id
        assert len(plan.cuts) == len(segments)
        assert len(plan.keep_cuts) > 0

    def test_build_cut_plan_with_target(self):
        planner = VideoStudioPlanner()
        source = _make_source(120.0)
        segments = _make_segments()
        hooks = planner.detect_hook_candidates(segments)
        plan = planner.build_cut_plan(source, segments, hooks, target_duration=20.0)
        assert plan.total_duration_seconds <= 20.0

    def test_build_cut_plan_null_source_raises(self):
        planner = VideoStudioPlanner()
        try:
            planner.build_cut_plan(None, [], [])
            assert False, "deveria ter lancado InvalidCutPlanError"
        except InvalidCutPlanError:
            pass

    def test_build_cut_plan_empty_segments_raises(self):
        planner = VideoStudioPlanner()
        source = _make_source()
        try:
            planner.build_cut_plan(source, [], [])
            assert False, "deveria ter lancado InvalidCutPlanError"
        except InvalidCutPlanError:
            pass

    def test_build_reel_script(self):
        planner = VideoStudioPlanner()
        source = _make_source()
        segments = _make_segments()
        hooks = planner.detect_hook_candidates(segments)
        plan = planner.build_cut_plan(source, segments, hooks)
        script = planner.build_reel_script(source, plan, ReelFormat.SHORT, "Test Reel")
        assert script.script_id.startswith("rs_")
        assert script.format == ReelFormat.SHORT
        assert script.title == "Test Reel"
        assert script.segment_count > 0

    def test_build_reel_script_default_title(self):
        planner = VideoStudioPlanner()
        source = _make_source()
        plan = CutPlan.new(source.source_id)
        plan.add_cut(_make_keep_cut(0, 10))
        script = planner.build_reel_script(source, plan)
        assert source.source_id in script.title

    def test_build_reel_script_null_source_raises(self):
        planner = VideoStudioPlanner()
        try:
            planner.build_reel_script(None, CutPlan.new("cp_x"), ReelFormat.SHORT, "Title")
            assert False, "deveria ter lancado InvalidReelScriptError"
        except InvalidReelScriptError:
            pass

    def test_build_reel_script_null_plan_raises(self):
        planner = VideoStudioPlanner()
        source = _make_source()
        try:
            planner.build_reel_script(source, None, ReelFormat.SHORT, "Title")
            assert False, "deveria ter lancado InvalidReelScriptError"
        except InvalidReelScriptError:
            pass

    def test_build_video_package_full_pipeline(self):
        planner = VideoStudioPlanner()
        source = _make_source()
        segments = _make_segments()
        pkg = planner.build_video_package(source, segments, ReelFormat.STANDARD, "Full Test")
        assert pkg.package_id.startswith("vp_")
        assert pkg.source == source
        assert len(pkg.cut_plan.cuts) > 0
        assert pkg.reel_script.segment_count > 0
        assert len(pkg.hook_candidates) > 0
        assert len(pkg.caption_specs) > 0

    def test_build_video_package_null_source_raises(self):
        planner = VideoStudioPlanner()
        try:
            planner.build_video_package(None, _make_segments())
            assert False, "deveria ter lancado InvalidVideoPackageError"
        except InvalidVideoPackageError:
            pass

    def test_build_video_package_empty_segments_raises(self):
        planner = VideoStudioPlanner()
        try:
            planner.build_video_package(_make_source(), [])
            assert False, "deveria ter lancado InvalidVideoPackageError"
        except InvalidVideoPackageError:
            pass

    def test_validate_video_package_valid(self):
        planner = VideoStudioPlanner()
        source = _make_source()
        segments = _make_segments()
        pkg = planner.build_video_package(source, segments)
        result = planner.validate_video_package(pkg)
        assert result["valid"] is True
        assert result["summary"]["hooks_detected"] > 0

    def test_validate_video_package_invalid(self):
        planner = VideoStudioPlanner()
        source = _make_source()
        plan = CutPlan.new(source.source_id)
        script = ReelScript.new(source.source_id, plan.plan_id, ReelFormat.SHORT, "Bad")
        pkg = VideoPackage.new(source, plan, script)
        result = planner.validate_video_package(pkg)
        assert result["valid"] is False
        assert len(result["validation_errors"]) > 0

    def test_validate_video_package_null_raises(self):
        planner = VideoStudioPlanner()
        try:
            planner.validate_video_package(None)
            assert False, "deveria ter lancado ValidationError"
        except ValidationError:
            pass

    def test_validate_long_source_warns(self):
        planner = VideoStudioPlanner()
        source = _make_source(900.0)
        segments = _make_segments()
        pkg = planner.build_video_package(source, segments)
        result = planner.validate_video_package(pkg)
        assert any("10 minutos" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

class TestModuleLevelFunctions:
    def test_analyze_transcript_segments_func(self):
        result = analyze_transcript_segments(_make_segments())
        assert result["total_segments"] == 8

    def test_detect_hook_candidates_func(self):
        hooks = detect_hook_candidates(_make_segments())
        assert len(hooks) > 0

    def test_build_cut_plan_func(self):
        source = _make_source()
        segments = _make_segments()
        hooks = detect_hook_candidates(segments)
        plan = build_cut_plan(source, segments, hooks)
        assert plan.source_id == source.source_id

    def test_build_reel_script_func(self):
        source = _make_source()
        plan = CutPlan.new(source.source_id)
        plan.add_cut(_make_keep_cut(0, 10))
        script = build_reel_script(source, plan, ReelFormat.SHORT, "Module Test")
        assert script.title == "Module Test"

    def test_build_video_package_func(self):
        source = _make_source()
        pkg = build_video_package(source, _make_segments(), title="Module Pkg")
        assert pkg.package_id.startswith("vp_")

    def test_validate_video_package_func(self):
        source = _make_source()
        pkg = build_video_package(source, _make_segments())
        result = validate_video_package(pkg)
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def _make_keep_cut(start: float, end: float):
    from src.video_studio.models import CutInstruction, CutType
    return CutInstruction.new(start, end, CutType.KEEP, f"keep_{start}_{end}")


class TestEdgeCases:
    def test_all_segments_are_hooks(self):
        planner = VideoStudioPlanner()
        segments = [
            TranscriptSegment.new(0.0, 5.0, "This is an amazing hook with many words here"),
            TranscriptSegment.new(5.0, 10.0, "Another incredible segment full of great content"),
            TranscriptSegment.new(10.0, 15.0, "Yet one more fantastic segment with lots of text"),
        ]
        source = _make_source(30.0)
        pkg = planner.build_video_package(source, segments)
        hooks = pkg.hook_candidates
        assert len(hooks) == 3
        assert all(h.score > 0 for h in hooks)

    def test_no_segments_qualify_as_hooks(self):
        planner = VideoStudioPlanner()
        segments = [
            TranscriptSegment.new(0.0, 2.0, "ok"),       # 1 word
            TranscriptSegment.new(2.0, 4.0, "um uh"),     # 2 words
            TranscriptSegment.new(4.0, 6.0, "yeah so"),    # 2 words
        ]
        source = _make_source(10.0)
        pkg = planner.build_video_package(source, segments)
        assert pkg.hook_candidates == []

    def test_roundtrip_serialization(self):
        planner = VideoStudioPlanner()
        source = _make_source()
        segments = _make_segments()
        pkg = planner.build_video_package(source, segments, notes="serialization test")
        pkg.validate()

        data = pkg.to_dict()
        restored = VideoPackage.from_dict(data)
        result = planner.validate_video_package(restored)
        assert result["valid"] is True
        assert restored.notes == "serialization test"
        assert restored.hook_candidates == pkg.hook_candidates or len(restored.hook_candidates) == len(pkg.hook_candidates)

    def test_target_duration_exact(self):
        planner = VideoStudioPlanner()
        source = _make_source(120.0)
        segments = _make_segments()
        hooks = planner.detect_hook_candidates(segments)
        plan = planner.build_cut_plan(source, segments, hooks, target_duration=10.0)
        assert plan.total_duration_seconds <= 10.0

    def test_target_duration_larger_than_content(self):
        planner = VideoStudioPlanner()
        source = _make_source(120.0)
        segments = _make_segments()
        hooks = planner.detect_hook_candidates(segments)
        plan = planner.build_cut_plan(source, segments, hooks, target_duration=9999.0)
        assert plan.total_duration_seconds > 0
