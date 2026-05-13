"""Testes dos modelos do Video Studio."""
from __future__ import annotations

from src.video_studio.models import (
    CaptionOverlaySpec,
    CaptionPosition,
    CaptionStyle,
    CutInstruction,
    CutPlan,
    CutType,
    HookCandidate,
    HookStrength,
    PackageStatus,
    ReelFormat,
    ReelScript,
    ReelSegment,
    TranscriptSegment,
    VideoPackage,
    VideoSource,
    VideoSourceKind,
)


# ---------------------------------------------------------------------------
# VideoSource
# ---------------------------------------------------------------------------

class TestVideoSource:
    def test_new_defaults(self):
        vs = VideoSource.new(
            kind=VideoSourceKind.RAW,
            uri_hint="test/video.mp4",
            duration_seconds=120.0,
        )
        assert vs.source_id.startswith("vs_")
        assert vs.kind == VideoSourceKind.RAW
        assert vs.width == 1920
        assert vs.height == 1080
        assert vs.fps == 30.0
        assert vs.codec_hint == "h264"

    def test_new_vertical(self):
        vs = VideoSource.new(
            kind=VideoSourceKind.RECORDING,
            uri_hint="test/reel.mp4",
            duration_seconds=30.0,
            width=1080,
            height=1920,
        )
        assert vs.is_vertical is True
        assert vs.aspect_ratio == 1080 / 1920

    def test_new_horizontal(self):
        vs = VideoSource.new(
            kind=VideoSourceKind.RAW,
            uri_hint="test/horizontal.mp4",
            duration_seconds=60.0,
            width=1920,
            height=1080,
        )
        assert vs.is_vertical is False
        assert vs.aspect_ratio == 1920 / 1080

    def test_new_invalid_duration_raises(self):
        try:
            VideoSource.new(
                kind=VideoSourceKind.RAW,
                uri_hint="test/video.mp4",
                duration_seconds=-1.0,
            )
            assert False, "deveria ter lancado ValueError"
        except ValueError:
            pass

    def test_to_dict_and_from_dict_roundtrip(self):
        vs = VideoSource.new(
            kind=VideoSourceKind.IMPORTED,
            uri_hint="imported/video.mp4",
            duration_seconds=300.0,
        )
        data = vs.to_dict()
        restored = VideoSource.from_dict(data)
        assert restored.source_id == vs.source_id
        assert restored.kind == vs.kind
        assert restored.duration_seconds == 300.0
        assert restored.width == 1920


# ---------------------------------------------------------------------------
# TranscriptSegment
# ---------------------------------------------------------------------------

class TestTranscriptSegment:
    def test_new_valid(self):
        seg = TranscriptSegment.new(
            start_seconds=0.0,
            end_seconds=5.0,
            text="Hello world this is a test segment",
        )
        assert seg.segment_id.startswith("ts_")
        assert seg.duration == 5.0
        assert seg.word_count == 7
        assert seg.confidence == 1.0

    def test_new_invalid_timestamps_raises(self):
        try:
            TranscriptSegment.new(
                start_seconds=5.0,
                end_seconds=3.0,
                text="Invalid timestamps",
            )
            assert False, "deveria ter lancado ValueError"
        except ValueError:
            pass

    def test_new_empty_text_raises(self):
        try:
            TranscriptSegment.new(
                start_seconds=0.0,
                end_seconds=5.0,
                text="   ",
            )
            assert False, "deveria ter lancado ValueError"
        except ValueError:
            pass

    def test_new_negative_confidence_raises(self):
        try:
            TranscriptSegment.new(
                start_seconds=0.0,
                end_seconds=5.0,
                text="Test",
                confidence=-0.5,
            )
            assert False, "deveria ter lancado ValueError"
        except ValueError:
            pass

    def test_to_dict_and_from_dict_roundtrip(self):
        seg = TranscriptSegment.new(
            start_seconds=10.0,
            end_seconds=25.0,
            text="Este e um segmento de teste em portugues",
            speaker_label="Speaker A",
        )
        data = seg.to_dict()
        restored = TranscriptSegment.from_dict(data)
        assert restored.segment_id == seg.segment_id
        assert restored.text == seg.text
        assert restored.speaker_label == "Speaker A"
        assert restored.duration == 15.0

    def test_word_count_empty(self):
        seg = TranscriptSegment.new(
            start_seconds=0.0,
            end_seconds=2.0,
            text="one",
        )
        assert seg.word_count == 1


# ---------------------------------------------------------------------------
# HookCandidate
# ---------------------------------------------------------------------------

class TestHookCandidate:
    def test_new_high_strength(self):
        hook = HookCandidate.new(
            segment_id="ts_abc123",
            start_seconds=5.0,
            end_seconds=8.0,
            hook_text="This is an amazing hook that grabs attention",
            strength=HookStrength.HIGH,
            score=0.9,
            rationale="test hook",
        )
        assert hook.hook_id.startswith("hk_")
        assert hook.strength == HookStrength.HIGH

    def test_new_invalid_score_raises(self):
        try:
            HookCandidate.new(
                segment_id="ts_abc",
                start_seconds=0.0,
                end_seconds=5.0,
                hook_text="Test hook",
                strength=HookStrength.MEDIUM,
                score=1.5,
                rationale="should fail",
            )
            assert False, "deveria ter lancado ValueError"
        except ValueError:
            pass

    def test_to_dict_and_from_dict_roundtrip(self):
        hook = HookCandidate.new(
            segment_id="ts_test",
            start_seconds=3.0,
            end_seconds=7.0,
            hook_text="Best hook ever",
            strength=HookStrength.MEDIUM,
            score=0.55,
            rationale="moderate density",
        )
        data = hook.to_dict()
        restored = HookCandidate.from_dict(data)
        assert restored.hook_id == hook.hook_id
        assert restored.strength == HookStrength.MEDIUM
        assert restored.score == 0.55


# ---------------------------------------------------------------------------
# CutPlan / CutInstruction
# ---------------------------------------------------------------------------

class TestCutInstruction:
    def test_new_keep(self):
        ci = CutInstruction.new(
            start_seconds=0.0,
            end_seconds=10.0,
            cut_type=CutType.KEEP,
            label="opening hook",
        )
        assert ci.cut_id.startswith("ci_")
        assert ci.duration == 10.0

    def test_new_remove(self):
        ci = CutInstruction.new(
            start_seconds=10.0,
            end_seconds=12.0,
            cut_type=CutType.REMOVE,
            label="dead air",
        )
        assert ci.cut_type == CutType.REMOVE

    def test_new_empty_label_raises(self):
        try:
            CutInstruction.new(
                start_seconds=0.0,
                end_seconds=5.0,
                cut_type=CutType.KEEP,
                label="   ",
            )
            assert False, "deveria ter lancado ValueError"
        except ValueError:
            pass

    def test_to_dict_and_from_dict_roundtrip(self):
        ci = CutInstruction.new(
            start_seconds=5.0,
            end_seconds=15.0,
            cut_type=CutType.TRIM,
            label="trimmed section",
            segment_id="ts_test",
        )
        data = ci.to_dict()
        restored = CutInstruction.from_dict(data)
        assert restored.cut_id == ci.cut_id
        assert restored.cut_type == CutType.TRIM
        assert restored.segment_id == "ts_test"


class TestCutPlan:
    def test_new_empty(self):
        plan = CutPlan.new(source_id="vs_test")
        assert plan.plan_id.startswith("cp_")
        assert plan.cuts == []
        assert plan.total_duration_seconds == 0.0

    def test_new_empty_source_raises(self):
        try:
            CutPlan.new(source_id="")
            assert False, "deveria ter lancado ValueError"
        except ValueError:
            pass

    def test_add_and_remove_cuts(self):
        plan = CutPlan.new(source_id="vs_test")
        ci1 = CutInstruction.new(0, 10, CutType.KEEP, "first")
        ci2 = CutInstruction.new(10, 15, CutType.KEEP, "second")
        ci3 = CutInstruction.new(15, 20, CutType.REMOVE, "remove me")

        plan.add_cut(ci1)
        plan.add_cut(ci2)
        plan.add_cut(ci3)

        assert len(plan.cuts) == 3
        assert len(plan.keep_cuts) == 2
        assert len(plan.removed_cuts) == 1
        assert plan.total_duration_seconds == 15.0

        removed = plan.remove_cut(ci1.cut_id)
        assert removed is True
        assert len(plan.keep_cuts) == 1

    def test_remove_nonexistent(self):
        plan = CutPlan.new(source_id="vs_test")
        assert plan.remove_cut("nonexistent") is False

    def test_to_dict_and_from_dict_roundtrip(self):
        plan = CutPlan.new(source_id="vs_src")
        plan.add_cut(CutInstruction.new(0, 10, CutType.KEEP, "hook"))
        plan.add_cut(CutInstruction.new(10, 20, CutType.TRIM, "body"))
        plan.add_cut(CutInstruction.new(20, 25, CutType.REMOVE, "dead"))

        data = plan.to_dict()
        restored = CutPlan.from_dict(data)
        assert restored.plan_id == plan.plan_id
        assert len(restored.cuts) == 3
        assert restored.total_duration_seconds == plan.total_duration_seconds


# ---------------------------------------------------------------------------
# ReelScript / ReelSegment
# ---------------------------------------------------------------------------

class TestReelScript:
    def test_new_valid(self):
        script = ReelScript.new(
            source_id="vs_test",
            plan_id="cp_test",
            format=ReelFormat.SHORT,
            title="My First Reel",
        )
        assert script.script_id.startswith("rs_")
        assert script.format == ReelFormat.SHORT
        assert script.segments == []
        assert script.total_duration_seconds == 0.0

    def test_new_empty_title_raises(self):
        try:
            ReelScript.new(
                source_id="vs_test",
                plan_id="cp_test",
                format=ReelFormat.STANDARD,
                title="   ",
            )
            assert False, "deveria ter lancado ValueError"
        except ValueError:
            pass

    def test_add_segments(self):
        script = ReelScript.new("vs_test", "cp_test", ReelFormat.STANDARD, "Test Reel")
        seg1 = ReelSegment(
            position=1, start_seconds=0.0, end_seconds=5.0,
            narration="Opening", on_screen_text="Welcome!",
        )
        seg2 = ReelSegment(
            position=2, start_seconds=5.0, end_seconds=12.0,
            narration="Main content",
        )
        script.add_segment(seg1)
        script.add_segment(seg2)
        assert script.segment_count == 2
        assert script.total_duration_seconds == 12.0

    def test_to_dict_and_from_dict_roundtrip(self):
        script = ReelScript.new("vs_test", "cp_test", ReelFormat.EXTENDED, "Long Reel")
        seg = ReelSegment(
            position=1, start_seconds=0.0, end_seconds=10.0,
            narration="Content", on_screen_text="Title",
            caption_spec=CaptionOverlaySpec.new("Title", end_seconds=10.0),
        )
        script.add_segment(seg)

        data = script.to_dict()
        restored = ReelScript.from_dict(data)
        assert restored.script_id == script.script_id
        assert restored.format == ReelFormat.EXTENDED
        assert restored.segment_count == 1
        assert restored.segments[0].caption_spec is not None


# ---------------------------------------------------------------------------
# CaptionOverlaySpec
# ---------------------------------------------------------------------------

class TestCaptionOverlaySpec:
    def test_new_defaults(self):
        cap = CaptionOverlaySpec.new("Hello World")
        assert cap.position == CaptionPosition.BOTTOM
        assert cap.style == CaptionStyle.BOLD
        assert cap.font_size_hint == 48
        assert cap.color_hex == "#FFFFFF"
        assert cap.duration == 3.0

    def test_new_invalid_color_raises(self):
        try:
            CaptionOverlaySpec.new("Test", color_hex="red")
            assert False, "deveria ter lancado ValueError"
        except ValueError:
            pass

    def test_new_invalid_duration_raises(self):
        try:
            CaptionOverlaySpec.new("Test", start_seconds=5.0, end_seconds=3.0)
            assert False, "deveria ter lancado ValueError"
        except ValueError:
            pass

    def test_to_dict_and_from_dict_roundtrip(self):
        cap = CaptionOverlaySpec.new(
            "Destaque!",
            position=CaptionPosition.CENTER,
            style=CaptionStyle.HIGHLIGHT,
            font_size_hint=64,
            color_hex="#FFD700",
            start_seconds=2.0,
            end_seconds=6.0,
        )
        data = cap.to_dict()
        restored = CaptionOverlaySpec.from_dict(data)
        assert restored.text == "Destaque!"
        assert restored.position == CaptionPosition.CENTER
        assert restored.style == CaptionStyle.HIGHLIGHT
        assert restored.color_hex == "#FFD700"


# ---------------------------------------------------------------------------
# VideoPackage
# ---------------------------------------------------------------------------

class TestVideoPackage:
    def _make_source(self) -> VideoSource:
        return VideoSource.new(VideoSourceKind.RAW, "test/video.mp4", 60.0)

    def _make_cut_plan(self, source: VideoSource) -> CutPlan:
        plan = CutPlan.new(source.source_id)
        plan.add_cut(CutInstruction.new(0, 10, CutType.KEEP, "hook"))
        plan.add_cut(CutInstruction.new(10, 50, CutType.KEEP, "body"))
        return plan

    def _make_reel_script(self, source: VideoSource, plan: CutPlan) -> ReelScript:
        script = ReelScript.new(source.source_id, plan.plan_id, ReelFormat.STANDARD, "Test")
        script.add_segment(ReelSegment(1, 0, 10, "Opening"))
        script.add_segment(ReelSegment(2, 10, 50, "Body"))
        return script

    def test_new_and_validate_pass(self):
        source = self._make_source()
        plan = self._make_cut_plan(source)
        script = self._make_reel_script(source, plan)
        pkg = VideoPackage.new(source, plan, script)
        assert pkg.status == PackageStatus.DRAFT
        assert pkg.validate() is True
        assert pkg.status == PackageStatus.VALIDATED

    def test_validate_mismatched_source_ids(self):
        source = self._make_source()
        source2 = VideoSource.new(VideoSourceKind.RAW, "other/video.mp4", 30.0)
        plan = self._make_cut_plan(source)  # plan references original source
        script = self._make_reel_script(source, plan)
        pkg = VideoPackage.new(source2, plan, script)
        assert pkg.validate() is False
        assert any("source_id" in e for e in pkg.validation_errors)

    def test_validate_missing_cuts(self):
        source = self._make_source()
        plan = CutPlan.new(source.source_id)  # no cuts
        script = ReelScript.new(source.source_id, plan.plan_id, ReelFormat.SHORT, "Empty")
        pkg = VideoPackage.new(source, plan, script)
        assert pkg.validate() is False

    def test_add_hooks_and_captions(self):
        source = self._make_source()
        plan = self._make_cut_plan(source)
        script = self._make_reel_script(source, plan)
        pkg = VideoPackage.new(source, plan, script)

        hook = HookCandidate.new("ts_test", 0, 10, "great hook", HookStrength.HIGH, 0.9, "strong")
        cap = CaptionOverlaySpec.new("Caption", end_seconds=10.0)

        pkg.add_hook(hook)
        pkg.add_caption_spec(cap)

        assert len(pkg.hook_candidates) == 1
        assert len(pkg.caption_specs) == 1
        assert pkg.strongest_hook is not None
        assert pkg.strongest_hook.score == 0.9

    def test_strongest_hook_empty(self):
        source = self._make_source()
        plan = self._make_cut_plan(source)
        script = self._make_reel_script(source, plan)
        pkg = VideoPackage.new(source, plan, script)
        assert pkg.strongest_hook is None

    def test_to_dict_and_from_dict_roundtrip(self):
        source = self._make_source()
        plan = self._make_cut_plan(source)
        script = self._make_reel_script(source, plan)
        pkg = VideoPackage.new(source, plan, script, notes="roundtrip test")
        pkg.add_hook(HookCandidate.new("ts_1", 0, 5, "hook text", HookStrength.HIGH, 0.95, "great"))
        pkg.validate()

        data = pkg.to_dict()
        restored = VideoPackage.from_dict(data)
        assert restored.package_id == pkg.package_id
        assert restored.notes == "roundtrip test"
        assert restored.status == PackageStatus.VALIDATED
        assert len(restored.hook_candidates) == 1
