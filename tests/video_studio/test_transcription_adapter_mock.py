"""Tests for W103 — Transcription Adapter Mock."""
from __future__ import annotations

import pytest

from src.video_studio.models import TranscriptSegment
from src.video_studio.transcription import (
    VideoTranscript,
    MockTranscriptionAdapter,
)


class TestVideoTranscript:
    def test_create_transcript(self):
        t = VideoTranscript(transcript_id="t1")
        assert t.transcript_id == "t1"
        assert t.segment_count == 0
        assert t.total_duration == 0.0
        assert t.language_hint == "pt"

    def test_add_segments(self):
        t = VideoTranscript(transcript_id="t2")
        t.segments.append(TranscriptSegment.new(
            start_seconds=0.0, end_seconds=5.0, text="Primeiro segmento", confidence=0.95
        ))
        t.segments.append(TranscriptSegment.new(
            start_seconds=5.0, end_seconds=10.0, text="Segundo segmento", confidence=0.90
        ))
        assert t.segment_count == 2
        assert t.total_duration == 10.0

    def test_full_text(self):
        t = VideoTranscript(transcript_id="t3")
        t.segments.append(TranscriptSegment.new(
            start_seconds=0.0, end_seconds=3.0, text="Ola mundo", confidence=1.0
        ))
        t.segments.append(TranscriptSegment.new(
            start_seconds=3.0, end_seconds=6.0, text="Como vai", confidence=1.0
        ))
        assert t.full_text == "Ola mundo Como vai"

    def test_to_dict_roundtrip(self):
        t = VideoTranscript(transcript_id="t4", source_id="vs1")
        t.segments.append(TranscriptSegment.new(
            start_seconds=0.0, end_seconds=5.0, text="Teste", confidence=0.95
        ))
        d = t.to_dict()
        restored = VideoTranscript.from_dict(d)
        assert restored.transcript_id == t.transcript_id
        assert restored.source_id == "vs1"
        assert restored.segment_count == 1

    def test_to_markdown(self):
        t = VideoTranscript(transcript_id="t5")
        t.segments.append(TranscriptSegment.new(
            start_seconds=0.0, end_seconds=5.0, text="Segmento unico", confidence=1.0
        ))
        md = t.to_markdown()
        assert "t5" in md
        assert "Segmento unico" in md
        assert "5.0s" in md


class TestMockTranscriptionAdapter:
    def setup_method(self):
        self.adapter = MockTranscriptionAdapter()

    def test_transcribe_tourism_video(self):
        result = self.adapter.transcribe("turismo natal praia", duration_seconds=60.0)
        assert isinstance(result, VideoTranscript)
        assert result.segment_count > 0
        assert result.language_hint == "pt"
        assert all(isinstance(s, TranscriptSegment) for s in result.segments)

    def test_transcribe_default_video(self):
        result = self.adapter.transcribe("unknown topic", duration_seconds=30.0)
        assert result.segment_count > 0
        # Default transcript is shorter
        assert len(result.segments) <= 6

    def test_transcribe_respects_duration(self):
        result = self.adapter.transcribe("turismo", duration_seconds=10.0)
        for s in result.segments:
            assert s.end_seconds <= 10.0

    def test_transcribe_no_api_call(self):
        result = self.adapter.transcribe("qualquer coisa", duration_seconds=30.0)
        assert result is not None
        # Should complete without network

    def test_transcribe_segments_have_valid_timestamps(self):
        result = self.adapter.transcribe("turismo", duration_seconds=60.0)
        for s in result.segments:
            assert s.start_seconds >= 0
            assert s.end_seconds > s.start_seconds
            assert s.text != ""

    def test_pick_transcript_tourism_hint(self):
        raw = self.adapter._pick_transcript("video de turismo em natal")
        assert len(raw) == 10  # TOURISM_TRANSCRIPT has 10 entries

    def test_pick_transcript_default(self):
        raw = self.adapter._pick_transcript("random video about tech")
        assert len(raw) == 6  # DEFAULT_TRANSCRIPT has 6 entries
