"""Creative Production Bridge — placeholder connector for content creation."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CreativeFormat(str, Enum):
    CAROUSEL = "carousel"
    REEL = "reel"
    STORY = "story"
    SINGLE_IMAGE = "single_image"


class CreativeStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    FAILED = "failed"


@dataclass
class CreativeAsset:
    asset_id: str
    content_id: str
    format: CreativeFormat = CreativeFormat.SINGLE_IMAGE
    media_urls: list[str] = field(default_factory=list)
    thumbnail_url: str = ""
    duration_seconds: float = 0.0
    status: CreativeStatus = CreativeStatus.PENDING
    notes: str = ""

    def mark_ready(self) -> None:
        self.status = CreativeStatus.READY

    def mark_failed(self, reason: str = "") -> None:
        self.status = CreativeStatus.FAILED
        if reason:
            self.notes = reason

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "content_id": self.content_id,
            "format": self.format.value,
            "media_urls": self.media_urls,
            "thumbnail_url": self.thumbnail_url,
            "duration_seconds": self.duration_seconds,
            "status": self.status.value,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CreativeAsset":
        return cls(
            asset_id=d["asset_id"],
            content_id=d.get("content_id", ""),
            format=CreativeFormat(d.get("format", "single_image")),
            media_urls=d.get("media_urls", []),
            thumbnail_url=d.get("thumbnail_url", ""),
            duration_seconds=d.get("duration_seconds", 0.0),
            status=CreativeStatus(d.get("status", "pending")),
            notes=d.get("notes", ""),
        )


@dataclass
class CreativeBridge:
    """Bridge between content pipeline and creative production (carrossel/reel/story).

    Dry-run only — returns placeholder assets. No API calls, no file writes.
    """

    assets: dict[str, CreativeAsset] = field(default_factory=dict)

    def request_asset(
        self,
        content_id: str,
        format: CreativeFormat = CreativeFormat.SINGLE_IMAGE,
    ) -> CreativeAsset:
        import uuid
        asset = CreativeAsset(
            asset_id=str(uuid.uuid4())[:8],
            content_id=content_id,
            format=format,
            media_urls=[f"placeholder://{content_id}/image_{i}" for i in range(1, 4)],
            thumbnail_url=f"placeholder://{content_id}/thumb",
            status=CreativeStatus.READY,
            notes="Dry-run — placeholder asset",
        )
        self.assets[content_id] = asset
        return asset

    def get_asset(self, content_id: str) -> CreativeAsset | None:
        return self.assets.get(content_id)

    def is_ready(self, content_id: str) -> bool:
        asset = self.assets.get(content_id)
        return asset is not None and asset.status == CreativeStatus.READY

    def to_dict(self) -> dict:
        return {
            "assets": {k: v.to_dict() for k, v in self.assets.items()},
        }
