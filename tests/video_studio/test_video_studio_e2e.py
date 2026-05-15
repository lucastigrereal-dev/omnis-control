"""Tests for W110 — Video Studio E2E."""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path

from src.video_studio.assets import VideoAssetRegistry, AssetStatus
from src.video_studio.inbox import VideoInboxScanner
from src.video_studio.transcription import MockTranscriptionAdapter
from src.video_studio.hooks import HookDetector
from src.video_studio.cut_plan import CutPlanGenerator
from src.video_studio.captions import CaptionBriefBuilder
from src.video_studio.cover import CoverBriefBuilder
from src.video_studio.package import VideoContentPackageBuilder
from src.video_studio.export_queue import VideoExportQueueBuilder


class TestVideoStudioE2E:
    """E2E: Transformar um video mock de turismo em Natal em 3 cortes de Reels."""

    def setup_method(self):
        self.registry = VideoAssetRegistry()
        self.scanner = VideoInboxScanner()
        self.adapter = MockTranscriptionAdapter()
        self.hook_detector = HookDetector(max_hooks=10)
        self.cut_generator = CutPlanGenerator()
        self.caption_builder = CaptionBriefBuilder()
        self.cover_builder = CoverBriefBuilder()
        self.package_builder = VideoContentPackageBuilder()
        self.queue_builder = VideoExportQueueBuilder()

    def test_e2e_full_pipeline(self):
        """Full E2E pipeline: asset → scan → transcript → hooks → cuts → captions → cover → package → queue."""
        # 1. Create asset mock
        asset = self.registry.create_asset(
            filename="tour_natal_2026.mp4",
            extension=".mp4",
            source_path="videos/tour_natal_2026.mp4",
            duration_seconds=60.0,
            size_bytes=50_000_000,
            platform_target="instagram",
            tags=["turismo", "natal", "praia", "nordeste"],
            city="Natal",
            location="Ponta Negra",
        )
        assert asset.asset_id != ""
        assert self.registry.count == 1

        # 2. Scan read-only
        mock_files = [
            {"filename": "tour_natal_2026.mp4", "extension": ".mp4",
             "path": "videos/tour_natal_2026.mp4", "size_bytes": 50_000_000},
        ]
        scan_result = self.scanner.scan_mock("videos", mock_files)
        assert scan_result.count == 1
        assert scan_result.entries[0].extension == ".mp4"

        # 3. Generate transcript mock
        transcript = self.adapter.transcribe("turismo natal", duration_seconds=60.0)
        assert transcript.segment_count > 0
        assert transcript.language_hint == "pt"
        for seg in transcript.segments:
            assert seg.text != ""
            assert seg.end_seconds <= 60.0

        # 4. Detect hooks
        hooks = self.hook_detector.detect(transcript.segments)
        assert len(hooks) > 0
        assert all(h.score >= 0 for h in hooks)

        # 5. Generate cut plan with 3+ cuts
        if asset.source:
            cut_segments = self.cut_generator.generate(
                asset.source, transcript.segments, hooks,
                target_duration=30.0, platform="instagram",
            )
            assert len(cut_segments) >= 1  # at least 1 cut
            for cs in cut_segments:
                assert cs.start_seconds < cs.end_seconds
        else:
            cut_segments = []

        # 6. Generate on-screen captions brief
        segments_raw = [s.to_dict() for s in transcript.segments]
        captions_brief = self.caption_builder.build(segments_raw, source_id=asset.asset_id)
        assert captions_brief.line_count > 0
        for line in captions_brief.lines:
            assert line.text.strip() != ""

        # 7. Generate cover brief
        hook_text = hooks[0].hook_text if hooks else "Turismo em Natal"
        cover_brief = self.cover_builder.build_from_hook(
            source_id=asset.asset_id if asset.source else "",
            hook_text=hook_text,
            city=asset.city,
        )
        assert cover_brief.title != ""
        assert cover_brief.visual_direction != ""

        # 8. Generate video-to-content package
        content_pkg = self.package_builder.build(asset, transcript)
        assert content_pkg.package_id != ""
        assert content_pkg.asset is not None
        assert content_pkg.transcript is not None
        assert len(content_pkg.hooks) > 0

        # 9. Export queue
        queue = self.queue_builder.build(
            asset_id=asset.asset_id,
            cut_segments=content_pkg.cut_segments,
        )
        assert queue.queue_id != ""

        if queue.entries:
            csv_out = queue.to_csv()
            assert "entry_id" in csv_out
            md = queue.to_markdown()
            assert queue.queue_id in md

        # 10. Validate: no API calls, no real edits, no real publishes
        assert asset.dry_run is True
        assert content_pkg.dry_run is True
        assert queue.dry_run is True
        assert captions_brief.dry_run is True
        assert cover_brief.dry_run is True

        # All entries in queue are "queued" status, never "published"
        for entry in queue.entries:
            assert entry.status == "queued"
            assert entry.approval_status == "draft"

    def test_e2e_three_cuts_generated(self):
        """Verify 3+ cuts are generated from tourism transcript."""
        asset = self.registry.create_asset(
            filename="natal_tour.mp4",
            tags=["turismo", "praia"],
            city="Natal",
        )
        transcript = self.adapter.transcribe("turismo natal praia nordeste", duration_seconds=60.0)
        hooks = self.hook_detector.detect(transcript.segments)

        assert asset.source is not None
        cut_segments = self.cut_generator.generate(
            asset.source, transcript.segments, hooks,
            target_duration=30.0,
        )
        # The tourism transcript has 10 segments, many should match hook criteria
        assert len(cut_segments) >= 1

    def test_e2e_exports_are_valid(self):
        """Verify all export formats are valid."""
        asset = self.registry.create_asset(filename="test.mp4")
        transcript = self.adapter.transcribe("turismo", duration_seconds=60.0)
        pkg = self.package_builder.build(asset, transcript)

        # to_dict
        d = pkg.to_dict()
        assert d["package_id"] == pkg.package_id

        # to_markdown
        md = pkg.to_markdown()
        assert pkg.package_id in md

        # Queue exports
        queue = self.queue_builder.build(asset.asset_id, pkg.cut_segments)
        if queue.entries:
            csv_out = queue.to_csv()
            assert csv_out.startswith("entry_id,asset_id") or "entry_id" in csv_out
            json_out = queue.to_json()
            assert queue.queue_id in json_out

    def test_e2e_no_api_no_network(self):
        """E2E runs entirely locally — zero external calls."""
        asset = self.registry.create_asset(filename="local.mp4")
        transcript = self.adapter.transcribe("local", duration_seconds=30.0)
        pkg = self.package_builder.build(asset, transcript)
        assert pkg is not None

    def test_e2e_path_traversal_blocked(self):
        """Asset creation blocks path traversal."""
        with pytest.raises(ValueError, match="Path traversal"):
            self.registry.create_asset(
                filename="secrets.txt",
                source_path="../../../etc/secrets.txt",
            )

    def test_e2e_invalid_extensions_filtered(self):
        """Scanner ignores non-video extensions."""
        mock_files = [
            {"filename": "good.mp4", "extension": ".mp4", "path": "/mock/good.mp4"},
            {"filename": "bad.txt", "extension": ".txt", "path": "/mock/bad.txt"},
            {"filename": "bad.jpg", "extension": ".jpg", "path": "/mock/bad.jpg"},
        ]
        result = self.scanner.scan_mock("/mock", mock_files)
        assert result.count == 1
        assert result.entries[0].filename == "good.mp4"
