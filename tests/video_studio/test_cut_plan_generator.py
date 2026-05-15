"""Tests for W105 — Cut Plan Generator."""
from __future__ import annotations

import pytest

from src.video_studio.models import (
    VideoSource,
    VideoSourceKind,
    TranscriptSegment,
    HookCandidate,
    HookStrength,
    CutType,
)
from src.video_studio.cut_plan import CutSegment, CutPlanGenerator


class TestCutSegment:
    def test_create_segment(self):
        cs = CutSegment(
            cut_id="c1",
            start_seconds=0.0,
            end_seconds=30.0,
            hook="Hook test",
            title="Test Cut",
            reason="High score",
        )
        assert cs.cut_id == "c1"
        assert cs.start_seconds == 0.0
        assert cs.end_seconds == 30.0
        assert cs.duration == 30.0
        assert cs.hook == "Hook test"

    def test_start_before_end(self):
        cs = CutSegment(cut_id="c2", start_seconds=5.0, end_seconds=25.0)
        assert cs.start_seconds < cs.end_seconds
        assert cs.duration == 20.0

    def test_to_dict_roundtrip(self):
        cs = CutSegment(
            cut_id="c3",
            start_seconds=0.0,
            end_seconds=15.0,
            hook="hook",
            title="title",
            reason="reason",
            platform="instagram",
        )
        d = cs.to_dict()
        restored = CutSegment.from_dict(d)
        assert restored.cut_id == cs.cut_id
        assert restored.start_seconds == cs.start_seconds
        assert restored.duration == cs.duration
        assert restored.platform == "instagram"


class TestCutPlanGenerator:
    def setup_method(self):
        self.generator = CutPlanGenerator()

    def _make_source(self) -> VideoSource:
        return VideoSource.new(
            kind=VideoSourceKind.RAW,
            uri_hint="test.mp4",
            duration_seconds=120.0,
        )

    def _make_segments(self) -> list[TranscriptSegment]:
        segments = []
        texts = [
            "Voce ja imaginou acordar nessa vista?",
            "Aqui em Natal tudo e mais bonito.",
            "Gastronomia incrivel e precos justos.",
            "O segredo que ninguem te conta sobre viajar.",
            "Mais de 3 milhoes de turistas por ano.",
        ]
        for i, t in enumerate(texts):
            segments.append(TranscriptSegment.new(
                start_seconds=i * 10.0,
                end_seconds=(i + 1) * 10.0,
                text=t,
                confidence=0.95,
            ))
        return segments

    def _make_hooks(self, segments: list[TranscriptSegment]) -> list[HookCandidate]:
        hooks = []
        for i, seg in enumerate(segments):
            if i % 2 == 0:  # every other segment is a hook
                hooks.append(HookCandidate.new(
                    segment_id=seg.segment_id,
                    start_seconds=seg.start_seconds,
                    end_seconds=seg.end_seconds,
                    hook_text=seg.text,
                    strength=HookStrength.HIGH if i == 0 else HookStrength.MEDIUM,
                    score=0.8 if i == 0 else 0.5,
                    rationale="test rationale",
                ))
        return hooks

    def test_generate_produces_cuts(self):
        source = self._make_source()
        segments = self._make_segments()
        hooks = self._make_hooks(segments)
        cuts = self.generator.generate(source, segments, hooks)
        assert len(cuts) > 0
        assert all(isinstance(c, CutSegment) for c in cuts)

    def test_generate_cuts_respect_timestamps(self):
        source = self._make_source()
        segments = self._make_segments()
        hooks = self._make_hooks(segments)
        cuts = self.generator.generate(source, segments, hooks)
        for c in cuts:
            assert c.start_seconds >= 0
            assert c.end_seconds > c.start_seconds

    def test_generate_no_segments_returns_empty(self):
        source = self._make_source()
        cuts = self.generator.generate(source, [], [])
        assert cuts == []

    def test_generate_cuts_are_sequential(self):
        source = self._make_source()
        segments = self._make_segments()
        hooks = self._make_hooks(segments)
        cuts = self.generator.generate(source, segments, hooks)
        for i in range(1, len(cuts)):
            assert cuts[i].start_seconds >= cuts[i - 1].start_seconds

    def test_generate_max_5_cuts(self):
        source = self._make_source()
        segments = self._make_segments()
        hooks = self._make_hooks(segments)
        # Add more hooks
        for i in range(5, 15):
            seg = TranscriptSegment.new(
                start_seconds=i * 10, end_seconds=(i + 1) * 10,
                text=f"Segmento {i}", confidence=0.9,
            )
            segments.append(seg)
            hooks.append(HookCandidate.new(
                segment_id=seg.segment_id,
                start_seconds=seg.start_seconds,
                end_seconds=seg.end_seconds,
                hook_text=seg.text,
                strength=HookStrength.LOW,
                score=0.3,
                rationale="extra",
            ))
        cuts = self.generator.generate(source, segments, hooks)
        assert len(cuts) <= 5

    def test_to_cut_plan(self):
        source = self._make_source()
        segments = self._make_segments()
        hooks = self._make_hooks(segments)
        cuts = self.generator.generate(source, segments, hooks)
        plan = self.generator.to_cut_plan(source, cuts)
        assert plan.source_id == source.source_id
        assert len(plan.cuts) == len(cuts)

    def test_export_markdown(self):
        cuts = [
            CutSegment(cut_id="c1", start_seconds=0.0, end_seconds=15.0, hook="Hook 1", title="T1", platform="instagram"),
            CutSegment(cut_id="c2", start_seconds=20.0, end_seconds=45.0, hook="Hook 2", title="T2", platform="instagram"),
        ]
        md = self.generator.export_markdown(cuts)
        assert "Cut Plan" in md
        assert "Hook 1" in md
        assert "Hook 2" in md
