"""Asset Inbox models — read-only scan results. Never modifies files."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Allowed file extensions and their media types
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".webp": "image",
    ".mp4": "video",
    ".mov": "video",
    ".m4v": "video",
}

# Status values for AssetInboxItem
STATUS_CANDIDATE = "candidate"
STATUS_IGNORED = "ignored"
STATUS_TOO_LARGE = "too_large"
STATUS_MISSING = "missing_on_disk"
STATUS_BLOCKED = "blocked"

# Default limits
DEFAULT_SCAN_LIMIT = 500
DEFAULT_MAX_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB

DEFAULT_EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "exports",
}


@dataclass
class AssetInboxItem:
    path: str
    file_name: str
    extension: str
    size_bytes: int
    media_type: str          # image | video | unknown
    fingerprint: str         # sha256 hex or "" if unavailable
    exists_on_disk: bool
    status: str              # candidate | ignored | too_large | missing_on_disk | blocked
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "file_name": self.file_name,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "media_type": self.media_type,
            "fingerprint": self.fingerprint,
            "exists_on_disk": self.exists_on_disk,
            "status": self.status,
            "warnings": self.warnings,
        }


@dataclass
class AssetInboxScanResult:
    scan_id: str
    root_path: str
    total_seen: int
    total_supported: int
    total_ignored: int
    total_too_large: int
    total_size_bytes: int
    items: list[AssetInboxItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, root_path: str) -> "AssetInboxScanResult":
        return cls(
            scan_id=f"scan_{uuid.uuid4().hex[:8]}",
            root_path=root_path,
            total_seen=0,
            total_supported=0,
            total_ignored=0,
            total_too_large=0,
            total_size_bytes=0,
        )

    def to_dict(self) -> dict:
        return {
            "scan_id": self.scan_id,
            "root_path": self.root_path,
            "total_seen": self.total_seen,
            "total_supported": self.total_supported,
            "total_ignored": self.total_ignored,
            "total_too_large": self.total_too_large,
            "total_size_bytes": self.total_size_bytes,
            "items": [i.to_dict() for i in self.items],
            "warnings": self.warnings,
            "blockers": self.blockers,
            "created_at": self.created_at,
            "next_actions": ["B8B Safe Import Registry"],
        }
