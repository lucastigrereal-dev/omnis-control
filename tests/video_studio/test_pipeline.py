"""Tests for the Video Studio local real MVP pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.video_studio.ingest import VideoIngestor, VideoIngestError
from src.video_studio.audio_extract import AudioExtractor
from src.video_studio.srt_generator import SRTGenerator
from src.video_studio.render_ffmpeg import FFmpegRenderer
from src.video_studio.pipeline import VideoStudioPipeline

FIXTURE_MP4 = Path(__file__).parent / "fixtures" / "sample.mp4"


# ---------------------------------------------------------------------------
# VideoIngestor
# ---------------------------------------------------------------------------

class TestVideoIngestor:
    def test_ingest_raises_on_missing_file(self, tmp_path):
        ingestor = VideoIngestor()
        with pytest.raises(VideoIngestError):
            ingestor.ingest(tmp_path / "nonexistent.mp4")

    def test_ingest_raises_on_unsupported_format(self, tmp_path):
        fake = tmp_path / "video.mkv"
        fake.write_bytes(b"fake")
        ingestor = VideoIngestor()
        with pytest.raises(VideoIngestError):
            ingestor.ingest(fake)

    def test_ingest_returns_result_for_mp4(self):
        ingestor = VideoIngestor()
        result = ingestor.ingest(FIXTURE_MP4)
        assert result.format == "mp4"
        assert result.size_bytes > 0
        assert result.duration_estimate_seconds == 0.0

    def test_ingest_returns_result_for_mov(self, tmp_path):
        f = tmp_path / "clip.mov"
        f.write_bytes(b"fake mov content")
        result = VideoIngestor().ingest(f)
        assert result.format == "mov"


# ---------------------------------------------------------------------------
# SRTGenerator
# ---------------------------------------------------------------------------

class TestSRTGenerator:
    def test_generate_creates_valid_srt(self, tmp_path):
        gen = SRTGenerator()
        cuts = [
            {"start": 0.0, "end": 3.5, "text": "Hello world"},
            {"start": 3.5, "end": 7.0, "text": "Second line"},
        ]
        out = tmp_path / "sub.srt"
        gen.generate(cuts, out)
        content = out.read_text(encoding="utf-8")
        assert "1\n" in content
        assert "--> " in content
        assert "Hello world" in content
        assert "Second line" in content

    def test_srt_timestamp_format(self, tmp_path):
        gen = SRTGenerator()
        cuts = [{"start": 65.5, "end": 70.0, "text": "Late segment"}]
        out = tmp_path / "ts.srt"
        gen.generate(cuts, out)
        content = out.read_text(encoding="utf-8")
        assert "00:01:05,500" in content

    def test_from_transcription_splits_into_segments(self):
        text = " ".join([f"word{i}" for i in range(25)])
        segs = SRTGenerator.from_transcription(text, 30.0)
        assert len(segs) == 3  # 25 words / 10 per chunk = 3 chunks
        assert segs[0]["start"] == 0.0
        assert segs[-1]["end"] == pytest.approx(30.0, abs=0.01)

    def test_from_transcription_empty_returns_empty(self):
        assert SRTGenerator.from_transcription("", 30.0) == []

    def test_from_transcription_zero_duration_returns_empty(self):
        assert SRTGenerator.from_transcription("hello", 0.0) == []


# ---------------------------------------------------------------------------
# FFmpegRenderer
# ---------------------------------------------------------------------------

class TestFFmpegRenderer:
    def test_is_ffmpeg_available_returns_bool(self):
        result = FFmpegRenderer.is_ffmpeg_available()
        assert isinstance(result, bool)

    def test_render_dry_run_writes_manifest_not_mp4(self, tmp_path):
        renderer = FFmpegRenderer()
        out = tmp_path / "cut.mp4"
        result = renderer.render_cut(FIXTURE_MP4, 0.0, 5.0, out, dry_run=True)
        assert result.suffix == ".json"
        assert result.exists()
        data = json.loads(result.read_text(encoding="utf-8"))
        assert data["dry_run"] is True
        assert data["duration"] == 5.0

    def test_render_dry_run_does_not_write_mp4(self, tmp_path):
        renderer = FFmpegRenderer()
        out = tmp_path / "cut.mp4"
        renderer.render_cut(FIXTURE_MP4, 0.0, 5.0, out, dry_run=True)
        assert not out.exists()


# ---------------------------------------------------------------------------
# AudioExtractor
# ---------------------------------------------------------------------------

class TestAudioExtractor:
    def test_dry_run_returns_path_without_calling_ffmpeg(self, tmp_path):
        extractor = AudioExtractor()
        result = extractor.extract(FIXTURE_MP4, tmp_path, dry_run=True)
        assert result.name == "sample.wav"
        # file should NOT exist — dry run never writes
        assert not result.exists()

    def test_dry_run_path_is_in_output_dir(self, tmp_path):
        extractor = AudioExtractor()
        result = extractor.extract(FIXTURE_MP4, tmp_path, dry_run=True)
        assert result.parent == tmp_path


# ---------------------------------------------------------------------------
# VideoStudioPipeline
# ---------------------------------------------------------------------------

class TestVideoStudioPipeline:
    def test_run_dry_run_returns_dict_with_expected_keys(self, tmp_path):
        pipeline = VideoStudioPipeline()
        result = pipeline.run(FIXTURE_MP4, tmp_path, dry_run=True)
        for key in ("video_path", "output_dir", "dry_run", "ingest",
                    "audio_path", "transcription", "cuts", "rendered_path",
                    "ffmpeg_available"):
            assert key in result, f"Missing key: {key}"

    def test_run_dry_run_saves_export_manifest(self, tmp_path):
        pipeline = VideoStudioPipeline()
        pipeline.run(FIXTURE_MP4, tmp_path, dry_run=True)
        manifest_path = tmp_path / "export_manifest.json"
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert data["dry_run"] is True

    def test_run_dry_run_is_true_in_result(self, tmp_path):
        pipeline = VideoStudioPipeline()
        result = pipeline.run(FIXTURE_MP4, tmp_path, dry_run=True)
        assert result["dry_run"] is True

    def test_run_raises_on_missing_video(self, tmp_path):
        from src.video_studio.ingest import VideoIngestError
        pipeline = VideoStudioPipeline()
        with pytest.raises(VideoIngestError):
            pipeline.run(tmp_path / "ghost.mp4", tmp_path, dry_run=True)
