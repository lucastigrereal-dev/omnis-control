"""Tests for W106 — On-Screen Captions Brief."""
from __future__ import annotations

import pytest

from src.video_studio.models import CaptionOverlaySpec
from src.video_studio.captions import (
    CaptionLine,
    OnScreenCaptionBrief,
    CaptionBriefBuilder,
)


class TestCaptionLine:
    def test_create_line(self):
        cl = CaptionLine(text="Ola", start_seconds=0.0, end_seconds=3.0)
        assert cl.text == "Ola"
        assert cl.start_seconds == 0.0
        assert cl.end_seconds == 3.0
        assert cl.duration == 3.0

    def test_create_line_with_emphasis(self):
        cl = CaptionLine(
            text="PALAVRA CHAVE",
            start_seconds=5.0,
            end_seconds=8.0,
            emphasis="bold",
            style_hint="bottom-white",
        )
        assert cl.emphasis == "bold"
        assert cl.style_hint == "bottom-white"

    def test_to_dict_roundtrip(self):
        cl = CaptionLine(
            text="Test caption",
            start_seconds=1.0,
            end_seconds=4.0,
            emphasis="highlight",
            style_hint="center-yellow",
        )
        d = cl.to_dict()
        restored = CaptionLine.from_dict(d)
        assert restored.text == "Test caption"
        assert restored.start_seconds == 1.0
        assert restored.emphasis == "highlight"


class TestOnScreenCaptionBrief:
    def test_create_brief(self):
        brief = OnScreenCaptionBrief(brief_id="b1")
        assert brief.brief_id == "b1"
        assert brief.line_count == 0

    def test_add_lines(self):
        brief = OnScreenCaptionBrief(brief_id="b2")
        brief.lines.append(CaptionLine(text="L1", start_seconds=0.0, end_seconds=3.0))
        brief.lines.append(CaptionLine(text="L2", start_seconds=3.0, end_seconds=6.0))
        assert brief.line_count == 2

    def test_to_dict_roundtrip(self):
        brief = OnScreenCaptionBrief(brief_id="b3", source_id="vs1")
        brief.lines.append(CaptionLine(text="Line 1", start_seconds=0.0, end_seconds=3.0))
        brief.total_duration = 3.0
        d = brief.to_dict()
        restored = OnScreenCaptionBrief.from_dict(d)
        assert restored.brief_id == "b3"
        assert restored.source_id == "vs1"
        assert restored.line_count == 1
        assert restored.total_duration == 3.0

    def test_to_markdown(self):
        brief = OnScreenCaptionBrief(brief_id="b4")
        brief.lines.append(CaptionLine(
            text="Caption text", start_seconds=0.0, end_seconds=5.0,
            emphasis="bold", style_hint="bottom-white",
        ))
        md = brief.to_markdown()
        assert "b4" in md
        assert "Caption text" in md

    def test_to_caption_overlay_specs(self):
        brief = OnScreenCaptionBrief(brief_id="b5")
        brief.lines.append(CaptionLine(
            text="Texto na tela", start_seconds=0.0, end_seconds=3.0,
            emphasis="bold", style_hint="bottom-white",
        ))
        brief.lines.append(CaptionLine(
            text="Outro texto", start_seconds=3.0, end_seconds=6.0,
            emphasis="highlight", style_hint="center-yellow",
        ))
        specs = brief.to_caption_overlay_specs()
        assert len(specs) == 2
        assert all(isinstance(s, CaptionOverlaySpec) for s in specs)

    def test_dry_run_default_true(self):
        brief = OnScreenCaptionBrief(brief_id="b6")
        assert brief.dry_run is True


class TestCaptionBriefBuilder:
    def setup_method(self):
        self.builder = CaptionBriefBuilder()

    def test_build_from_segments(self):
        segments = [
            {"text": "Primeira legenda", "start_seconds": 0.0, "end_seconds": 3.0},
            {"text": "Segunda legenda", "start_seconds": 3.0, "end_seconds": 6.0},
        ]
        brief = self.builder.build(segments, source_id="vs1")
        assert brief.line_count == 2
        assert brief.source_id == "vs1"
        assert brief.total_duration >= 0

    def test_build_filters_empty_text(self):
        segments = [
            {"text": "   ", "start_seconds": 0.0, "end_seconds": 3.0},
            {"text": "Valida", "start_seconds": 3.0, "end_seconds": 6.0},
        ]
        brief = self.builder.build(segments)
        assert brief.line_count == 1

    def test_build_short_text_gets_bold(self):
        segments = [
            {"text": "Curto", "start_seconds": 0.0, "end_seconds": 3.0},
        ]
        brief = self.builder.build(segments)
        assert brief.lines[0].emphasis == "bold"

    def test_build_long_text_no_emphasis(self):
        segments = [
            {"text": "Este e um texto bem mais longo que cinco palavras", "start_seconds": 0.0, "end_seconds": 5.0},
        ]
        brief = self.builder.build(segments)
        assert brief.lines[0].emphasis == ""
