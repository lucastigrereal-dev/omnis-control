"""W101 — Video Asset Registry extending VideoSource."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from src.video_studio.models import VideoSource, VideoSourceKind


class AssetStatus(str, Enum):
    PENDING = "pending"
    SCANNED = "scanned"
    TRANSCRIBED = "transcribed"
    PROCESSED = "processed"
    ARCHIVED = "archived"


@dataclass
class VideoAsset:
    """Extended video asset wrapping VideoSource with registry fields."""

    asset_id: str
    source: VideoSource | None = None
    filename: str = ""
    extension: str = ""
    source_path: str = ""
    size_bytes: int = 0
    platform_target: str = "instagram"
    status: AssetStatus = AssetStatus.PENDING
    tags: list[str] = field(default_factory=list)
    city: str = ""
    location: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    @property
    def duration_seconds(self) -> float:
        return self.source.duration_seconds if self.source else 0.0

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "source": self.source.to_dict() if self.source else None,
            "filename": self.filename,
            "extension": self.extension,
            "source_path": self.source_path,
            "size_bytes": self.size_bytes,
            "platform_target": self.platform_target,
            "status": self.status.value,
            "tags": self.tags,
            "city": self.city,
            "location": self.location,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "VideoAsset":
        status = d.get("status", "pending")
        if isinstance(status, str):
            status = AssetStatus(status)
        source = d.get("source")
        return cls(
            asset_id=d["asset_id"],
            source=VideoSource.from_dict(source) if source else None,
            filename=d.get("filename", ""),
            extension=d.get("extension", ""),
            source_path=d.get("source_path", ""),
            size_bytes=d.get("size_bytes", 0),
            platform_target=d.get("platform_target", "instagram"),
            status=status,
            tags=d.get("tags", []),
            city=d.get("city", ""),
            location=d.get("location", ""),
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )

    def to_markdown(self) -> str:
        lines = [
            f"# Video Asset: {self.filename or self.asset_id}",
            f"**ID:** {self.asset_id} | **Status:** {self.status.value}",
            f"**Platform:** {self.platform_target} | **Size:** {self.size_bytes} bytes",
        ]
        if self.city:
            lines.append(f"**Location:** {self.city}{' — ' + self.location if self.location else ''}")
        if self.tags:
            lines.append(f"**Tags:** {', '.join(self.tags)}")
        if self.duration_seconds:
            lines.append(f"**Duration:** {self.duration_seconds}s")
        return "\n".join(lines)


class VideoAssetRegistry:
    """Registry of video assets — no file I/O, no real video processing."""

    def __init__(self) -> None:
        self._assets: dict[str, VideoAsset] = {}

    def register(self, asset: VideoAsset) -> VideoAsset:
        self._assets[asset.asset_id] = asset
        return asset

    def create_asset(
        self,
        filename: str,
        extension: str = ".mp4",
        source_path: str = "",
        duration_seconds: float = 60.0,
        size_bytes: int = 0,
        platform_target: str = "instagram",
        tags: list[str] | None = None,
        city: str = "",
        location: str = "",
    ) -> VideoAsset:
        import uuid

        source = VideoSource.new(
            kind=VideoSourceKind.IMPORTED,
            uri_hint=source_path or f"mock://{filename}",
            duration_seconds=duration_seconds,
        )

        path = source_path or f"videos/{filename}"
        if ".." in path or path.startswith("/"):
            raise ValueError("Path traversal blocked")

        asset = VideoAsset(
            asset_id=str(uuid.uuid4())[:8],
            source=source,
            filename=filename,
            extension=extension if extension.startswith(".") else f".{extension}",
            source_path=path,
            size_bytes=size_bytes,
            platform_target=platform_target,
            tags=tags or [],
            city=city,
            location=location,
        )
        self._assets[asset.asset_id] = asset
        return asset

    def get(self, asset_id: str) -> VideoAsset | None:
        return self._assets.get(asset_id)

    def list_all(self) -> list[VideoAsset]:
        return list(self._assets.values())

    def list_by_status(self, status: AssetStatus) -> list[VideoAsset]:
        return [a for a in self._assets.values() if a.status == status]

    def list_by_platform(self, platform: str) -> list[VideoAsset]:
        return [a for a in self._assets.values() if a.platform_target == platform]

    def list_by_tag(self, tag: str) -> list[VideoAsset]:
        return [a for a in self._assets.values() if tag in a.tags]

    def list_by_city(self, city: str) -> list[VideoAsset]:
        return [a for a in self._assets.values() if a.city.lower() == city.lower()]

    def update_status(self, asset_id: str, status: AssetStatus) -> bool:
        asset = self._assets.get(asset_id)
        if asset is None:
            return False
        asset.status = status
        return True

    def to_dict(self) -> dict:
        return {
            "assets": [a.to_dict() for a in self._assets.values()],
            "count": len(self._assets),
        }

    def to_jsonl(self) -> str:
        import json
        return "\n".join(json.dumps(a.to_dict(), ensure_ascii=False) for a in self._assets.values())

    @property
    def count(self) -> int:
        return len(self._assets)
