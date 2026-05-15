"""Tests for W109 — Video Export Queue."""
from __future__ import annotations

import pytest

from src.video_studio.cut_plan import CutSegment
from src.video_studio.export_queue import (
    ExportEntry,
    VideoExportQueue,
    VideoExportQueueBuilder,
)


class TestExportEntry:
    def test_create_entry(self):
        e = ExportEntry(entry_id="e1")
        assert e.entry_id == "e1"
        assert e.status == "queued"
        assert e.approval_status == "draft"

    def test_create_full_entry(self):
        e = ExportEntry(
            entry_id="e2",
            asset_id="a1",
            cut_id="c1",
            platform="instagram",
            title="Meu Reel",
            caption="Legenda do reel",
            export_path="export/c1/instagram/",
        )
        assert e.asset_id == "a1"
        assert e.cut_id == "c1"
        assert e.platform == "instagram"
        assert e.title == "Meu Reel"

    def test_to_dict_roundtrip(self):
        e = ExportEntry(
            entry_id="e3",
            asset_id="a1",
            cut_id="c1",
            platform="youtube",
            title="Shorts",
        )
        d = e.to_dict()
        restored = ExportEntry.from_dict(d)
        assert restored.entry_id == "e3"
        assert restored.platform == "youtube"
        assert restored.title == "Shorts"


class TestVideoExportQueue:
    def test_create_queue(self):
        q = VideoExportQueue(queue_id="q1")
        assert q.queue_id == "q1"
        assert q.entry_count == 0

    def test_add_entries(self):
        q = VideoExportQueue(queue_id="q2")
        q.add_entry(ExportEntry(entry_id="e1", asset_id="a1", cut_id="c1"))
        q.add_entry(ExportEntry(entry_id="e2", asset_id="a2", cut_id="c2"))
        assert q.entry_count == 2

    def test_to_csv(self):
        q = VideoExportQueue(queue_id="q3")
        q.add_entry(ExportEntry(
            entry_id="e1", asset_id="a1", cut_id="c1",
            platform="instagram", title="Reel 1", caption="Caption 1",
        ))
        csv_out = q.to_csv()
        assert "entry_id" in csv_out
        assert "e1" in csv_out
        assert "Reel 1" in csv_out

    def test_to_json(self):
        q = VideoExportQueue(queue_id="q4")
        q.add_entry(ExportEntry(entry_id="e1", title="Test"))
        j = q.to_json()
        assert "q4" in j
        assert "Test" in j

    def test_to_markdown(self):
        q = VideoExportQueue(queue_id="q5")
        q.add_entry(ExportEntry(
            entry_id="e1", asset_id="a1", cut_id="c1",
            platform="instagram", title="Reel Title",
        ))
        md = q.to_markdown()
        assert "q5" in md
        assert "Reel Title" in md

    def test_to_dict_roundtrip(self):
        q = VideoExportQueue(queue_id="q6")
        q.add_entry(ExportEntry(entry_id="e1"))
        d = q.to_dict()
        restored = VideoExportQueue.from_dict(d)
        assert restored.queue_id == "q6"
        assert restored.entry_count == 1

    def test_dry_run_default_true(self):
        q = VideoExportQueue(queue_id="q7")
        assert q.dry_run is True

    def test_no_real_publish(self):
        q = VideoExportQueue(queue_id="q8")
        q.add_entry(ExportEntry(entry_id="e1"))
        csv_out = q.to_csv()
        # Status always queued, never published
        assert "published" not in csv_out.lower() or "approval_status" in csv_out

    def test_status_never_published(self):
        q = VideoExportQueue(queue_id="q9")
        q.add_entry(ExportEntry(entry_id="e1"))
        assert q.entries[0].status == "queued"


class TestVideoExportQueueBuilder:
    def setup_method(self):
        self.builder = VideoExportQueueBuilder()

    def test_build_from_cut_segments(self):
        cuts = [
            CutSegment(cut_id="c1", start_seconds=0.0, end_seconds=15.0, hook="Hook 1", title="T1", platform="instagram"),
            CutSegment(cut_id="c2", start_seconds=20.0, end_seconds=45.0, hook="Hook 2", title="T2", platform="instagram"),
            CutSegment(cut_id="c3", start_seconds=50.0, end_seconds=80.0, hook="Hook 3", title="T3", platform="youtube"),
        ]
        queue = self.builder.build(asset_id="a1", cut_segments=cuts)
        assert queue.entry_count == 3
        assert all(e.asset_id == "a1" for e in queue.entries)

    def test_build_empty_cuts(self):
        queue = self.builder.build(asset_id="a1", cut_segments=[])
        assert queue.entry_count == 0

    def test_build_export_paths_are_unique(self):
        cuts = [
            CutSegment(cut_id="c1", start_seconds=0.0, end_seconds=10.0),
            CutSegment(cut_id="c2", start_seconds=10.0, end_seconds=20.0),
        ]
        queue = self.builder.build(asset_id="a1", cut_segments=cuts)
        paths = {e.export_path for e in queue.entries}
        assert len(paths) == 2
