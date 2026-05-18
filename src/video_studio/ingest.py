"""VideoIngestor — reads file metadata without ffprobe."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from src.video_studio.errors import VideoStudioError

SUPPORTED_FORMATS = {".mp4", ".mov", ".avi"}


class VideoIngestError(VideoStudioError):
    """Raised when a video file cannot be ingested."""
    pass


@dataclass
class IngestResult:
    path: Path
    format: str
    size_bytes: int
    duration_estimate_seconds: float  # always 0.0 without ffprobe — caller can override

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "format": self.format,
            "size_bytes": self.size_bytes,
            "duration_estimate_seconds": self.duration_estimate_seconds,
        }


class VideoIngestor:
    """Reads file metadata using only stdlib — no ffprobe required."""

    def ingest(self, path: Path) -> IngestResult:
        if not path.exists():
            raise VideoIngestError(f"File not found: {path}")
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_FORMATS:
            raise VideoIngestError(
                f"Unsupported format '{suffix}'. Supported: {SUPPORTED_FORMATS}"
            )
        size_bytes = os.path.getsize(path)
        return IngestResult(
            path=path,
            format=suffix.lstrip("."),
            size_bytes=size_bytes,
            duration_estimate_seconds=0.0,
        )
