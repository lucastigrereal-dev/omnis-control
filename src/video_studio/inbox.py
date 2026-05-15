"""W102 — Video Inbox Scanner (read-only)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol


SUPPORTED_EXTENSIONS = frozenset({".mp4", ".mov", ".m4v", ".avi", ".webm"})


@dataclass
class InboxEntry:
    filename: str
    extension: str
    path: str
    size_bytes: int = 0
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "extension": self.extension,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "detected_at": self.detected_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "InboxEntry":
        return cls(
            filename=d["filename"],
            extension=d.get("extension", ""),
            path=d.get("path", ""),
            size_bytes=d.get("size_bytes", 0),
            detected_at=d.get("detected_at", ""),
        )


@dataclass
class InboxScanResult:
    scan_id: str
    directory: str
    entries: list[InboxEntry] = field(default_factory=list)
    scanned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def count(self) -> int:
        return len(self.entries)

    def to_dict(self) -> dict:
        return {
            "scan_id": self.scan_id,
            "directory": self.directory,
            "entries": [e.to_dict() for e in self.entries],
            "count": self.count,
            "scanned_at": self.scanned_at,
        }


class VideoInboxScanner:
    """Read-only scanner for video inbox directories."""

    def __init__(self) -> None:
        pass

    def scan_directory(self, directory: str) -> InboxScanResult:
        import uuid

        p = Path(directory)
        if not p.exists() or not p.is_dir():
            return InboxScanResult(
                scan_id=str(uuid.uuid4())[:8],
                directory=directory,
                entries=[],
            )

        entries: list[InboxEntry] = []
        for f in p.iterdir():
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            try:
                size = f.stat().st_size
            except OSError:
                size = 0
            entries.append(InboxEntry(
                filename=f.name,
                extension=ext,
                path=str(f.resolve()),
                size_bytes=size,
            ))

        entries.sort(key=lambda e: e.filename)

        return InboxScanResult(
            scan_id=str(uuid.uuid4())[:8],
            directory=str(p.resolve()),
            entries=entries,
        )

    def scan_mock(self, directory: str, mock_files: list[dict] | None = None) -> InboxScanResult:
        """Scan using mock data (no real filesystem access required)."""
        import uuid

        entries: list[InboxEntry] = []
        if mock_files:
            for mf in mock_files:
                ext = mf.get("extension", ".mp4")
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                entries.append(InboxEntry(
                    filename=mf.get("filename", "unknown.mp4"),
                    extension=ext,
                    path=mf.get("path", f"{directory}/{mf.get('filename', 'unknown.mp4')}"),
                    size_bytes=mf.get("size_bytes", 0),
                ))
            entries.sort(key=lambda e: e.filename)

        return InboxScanResult(
            scan_id=str(uuid.uuid4())[:8],
            directory=directory,
            entries=entries,
        )
