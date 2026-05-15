"""Tests for W108 — Video-to-Content Package."""
from __future__ import annotations

import pytest

from src.video_studio.assets import VideoAsset, VideoAssetRegistry
from src.video_studio.transcription import VideoTranscript, MockTranscriptionAdapter
from src.video_studio.package import VideoContentPackage, VideoContentPackageBuilder


class TestVideoContentPackage:
    def test_create_package(self):
        pkg = VideoContentPackage(package_id="vp1")
        assert pkg.package_id == "vp1"
        assert pkg.cut_count == 0
        assert pkg.hook_count == 0
        assert pkg.dry_run is True

    def test_package_with_asset(self):
        registry = VideoAssetRegistry()
        asset = registry.create_asset(filename="tour.mp4", tags=["turismo"])
        pkg = VideoContentPackage(package_id="vp2", asset=asset)
        assert pkg.asset.filename == "tour.mp4"

    def test_to_dict_roundtrip(self):
        registry = VideoAssetRegistry()
        asset = registry.create_asset(filename="test.mp4")
        adapter = MockTranscriptionAdapter()
        transcript = adapter.transcribe("turismo", duration_seconds=30.0)

        pkg = VideoContentPackage(
            package_id="vp3",
            asset=asset,
            transcript=transcript,
            notes="Test package",
        )
        d = pkg.to_dict()
        restored = VideoContentPackage.from_dict(d)
        assert restored.package_id == "vp3"
        assert restored.asset.filename == "test.mp4"
        assert restored.transcript is not None
        assert restored.notes == "Test package"

    def test_to_markdown(self):
        registry = VideoAssetRegistry()
        asset = registry.create_asset(filename="video.mp4", tags=["turismo"], city="Natal")
        pkg = VideoContentPackage(package_id="vp4", asset=asset)
        md = pkg.to_markdown()
        assert "vp4" in md
        assert "video.mp4" in md

    def test_dry_run_default_true(self):
        pkg = VideoContentPackage(package_id="vp5")
        assert pkg.dry_run is True


class TestVideoContentPackageBuilder:
    def setup_method(self):
        self.builder = VideoContentPackageBuilder()
        self.registry = VideoAssetRegistry()
        self.adapter = MockTranscriptionAdapter()

    def test_build_full_pipeline(self):
        asset = self.registry.create_asset(
            filename="tour_natal.mp4",
            tags=["turismo", "praia"],
            city="Natal",
        )
        transcript = self.adapter.transcribe("turismo", duration_seconds=60.0)
        pkg = self.builder.build(asset, transcript)

        assert pkg.package_id != ""
        assert pkg.asset is not None
        assert pkg.transcript is not None
        assert len(pkg.hooks) > 0
        assert len(pkg.cut_segments) > 0
        assert pkg.captions_brief is not None
        assert pkg.cover_brief is not None

    def test_build_captions_brief_has_lines(self):
        asset = self.registry.create_asset(filename="video.mp4")
        transcript = self.adapter.transcribe("turismo", duration_seconds=60.0)
        pkg = self.builder.build(asset, transcript)
        assert pkg.captions_brief is not None
        assert pkg.captions_brief.line_count > 0

    def test_build_cover_brief_has_title(self):
        asset = self.registry.create_asset(filename="video.mp4")
        transcript = self.adapter.transcribe("turismo", duration_seconds=60.0)
        pkg = self.builder.build(asset, transcript)
        assert pkg.cover_brief is not None
        assert pkg.cover_brief.title != ""

    def test_build_no_api_calls(self):
        asset = self.registry.create_asset(filename="video.mp4")
        transcript = self.adapter.transcribe("turismo", duration_seconds=30.0)
        pkg = self.builder.build(asset, transcript)
        assert pkg.dry_run is True

    def test_build_with_custom_duration(self):
        asset = self.registry.create_asset(filename="video.mp4")
        transcript = self.adapter.transcribe("turismo", duration_seconds=60.0)
        pkg = self.builder.build(asset, transcript, target_duration=15.0)
        for cs in pkg.cut_segments:
            assert cs.duration <= 15.5  # allow slight rounding

    def test_build_reel_package_integration(self):
        asset = self.registry.create_asset(filename="video.mp4")
        transcript = self.adapter.transcribe("turismo", duration_seconds=60.0)
        pkg = self.builder.build(asset, transcript)
        # May have reel_package if there are valid cut segments
        if pkg.cut_segments and asset.source:
            assert pkg.reel_package is not None
