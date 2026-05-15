"""Tests for W102 — Video Inbox Scanner."""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path

from src.video_studio.inbox import (
    InboxEntry,
    InboxScanResult,
    VideoInboxScanner,
    SUPPORTED_EXTENSIONS,
)


class TestInboxEntry:
    def test_create_entry(self):
        e = InboxEntry(filename="video.mp4", extension=".mp4", path="/tmp/video.mp4")
        assert e.filename == "video.mp4"
        assert e.extension == ".mp4"

    def test_to_dict_roundtrip(self):
        e = InboxEntry(
            filename="test.mp4",
            extension=".mp4",
            path="/tmp/test.mp4",
            size_bytes=100,
        )
        d = e.to_dict()
        restored = InboxEntry.from_dict(d)
        assert restored.filename == "test.mp4"
        assert restored.size_bytes == 100


class TestInboxScanResult:
    def test_create_result(self):
        r = InboxScanResult(scan_id="s1", directory="/tmp")
        assert r.scan_id == "s1"
        assert r.count == 0

    def test_to_dict(self):
        r = InboxScanResult(scan_id="s2", directory="/tmp")
        r.entries.append(InboxEntry(filename="a.mp4", extension=".mp4", path="/tmp/a.mp4"))
        d = r.to_dict()
        assert d["count"] == 1
        assert len(d["entries"]) == 1


class TestVideoInboxScanner:
    def setup_method(self):
        self.scanner = VideoInboxScanner()

    def test_scan_empty_directory(self):
        with tempfile.TemporaryDirectory() as td:
            result = self.scanner.scan_directory(td)
            assert result.count == 0

    def test_scan_nonexistent_directory(self):
        result = self.scanner.scan_directory("/nonexistent/path/12345")
        assert result.count == 0

    def test_scan_real_video_files(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "video1.mp4").write_text("fake mp4")
            (p / "video2.mov").write_text("fake mov")
            (p / "not_a_video.txt").write_text("text")
            (p / "video3.avi").write_text("fake avi")

            result = self.scanner.scan_directory(td)
            assert result.count == 3
            exts = {e.extension for e in result.entries}
            assert ".mp4" in exts
            assert ".mov" in exts
            assert ".avi" in exts

    def test_scan_ignores_invalid_extensions(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "image.jpg").write_text("jpg")
            (p / "doc.pdf").write_text("pdf")
            (p / "script.py").write_text("code")

            result = self.scanner.scan_directory(td)
            assert result.count == 0

    def test_scan_all_supported_extensions(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            for ext in SUPPORTED_EXTENSIONS:
                (p / f"file{ext}").write_text("fake")

            result = self.scanner.scan_directory(td)
            assert result.count == len(SUPPORTED_EXTENSIONS)

    def test_scan_mock(self):
        mock_files = [
            {"filename": "tour.mp4", "extension": ".mp4", "path": "/mock/tour.mp4", "size_bytes": 1000},
            {"filename": "reel.mov", "extension": ".mov", "path": "/mock/reel.mov", "size_bytes": 2000},
            {"filename": "bad.jpg", "extension": ".jpg", "path": "/mock/bad.jpg"},
        ]
        result = self.scanner.scan_mock("/mock", mock_files)
        assert result.count == 2  # jpg filtered out
        assert all(e.extension in SUPPORTED_EXTENSIONS for e in result.entries)

    def test_scan_mock_empty_directory(self):
        result = self.scanner.scan_mock("/empty")
        assert result.count == 0
