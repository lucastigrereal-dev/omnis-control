"""Publer/Metricool Export — export contract for external scheduling platforms."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class PublerPlatform(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"


@dataclass
class PublerExportItem:
    item_id: str
    caption: str
    account_handle: str
    platform: PublerPlatform = PublerPlatform.INSTAGRAM
    media_url: str = ""
    hashtags: list[str] = field(default_factory=list)
    schedule_iso: str = ""
    link_in_bio: str = ""
    first_comment: str = ""

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "caption": self.caption,
            "account_handle": self.account_handle,
            "platform": self.platform.value,
            "media_url": self.media_url,
            "hashtags": self.hashtags,
            "schedule_iso": self.schedule_iso,
            "link_in_bio": self.link_in_bio,
            "first_comment": self.first_comment,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PublerExportItem":
        return cls(
            item_id=d["item_id"],
            caption=d.get("caption", ""),
            account_handle=d.get("account_handle", ""),
            platform=PublerPlatform(d.get("platform", "instagram")),
            media_url=d.get("media_url", ""),
            hashtags=d.get("hashtags", []),
            schedule_iso=d.get("schedule_iso", ""),
            link_in_bio=d.get("link_in_bio", ""),
            first_comment=d.get("first_comment", ""),
        )


@dataclass
class PublerExportBatch:
    batch_id: str
    label: str = ""
    items: list[PublerExportItem] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    def add(self, item: PublerExportItem) -> None:
        self.items.append(item)

    def to_csv_rows(self) -> list[dict]:
        return [i.to_dict() for i in self.items]

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "label": self.label,
            "item_count": len(self.items),
            "created_at": self.created_at,
            "dry_run": self.dry_run,
            "items": [i.to_dict() for i in self.items],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PublerExportBatch":
        batch = cls(
            batch_id=d["batch_id"],
            label=d.get("label", ""),
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )
        for i in d.get("items", []):
            batch.add(PublerExportItem.from_dict(i))
        return batch


@dataclass
class PublerExporter:
    """Deterministic Publer/Metricool export — dry-run only, no API calls."""

    dry_run: bool = True
    batches: dict[str, PublerExportBatch] = field(default_factory=dict)

    def create_batch(self, label: str = "") -> PublerExportBatch:
        import uuid
        batch = PublerExportBatch(
            batch_id=str(uuid.uuid4())[:8],
            label=label,
            dry_run=self.dry_run,
        )
        self.batches[batch.batch_id] = batch
        return batch

    def build_item(
        self,
        caption: str,
        account_handle: str,
        media_url: str = "",
        hashtags: list[str] | None = None,
        schedule_iso: str = "",
    ) -> PublerExportItem:
        import uuid
        return PublerExportItem(
            item_id=str(uuid.uuid4())[:8],
            caption=caption,
            account_handle=account_handle,
            media_url=media_url,
            hashtags=hashtags or [],
            schedule_iso=schedule_iso,
        )

    def export_batch(self, batch_id: str) -> str | None:
        """Export a batch as CSV-formatted string (dry-run — never writes to disk)."""
        batch = self.batches.get(batch_id)
        if batch is None or not batch.items:
            return None
        headers = ["item_id", "caption", "account_handle", "platform", "media_url", "hashtags", "schedule_iso"]
        rows = []
        for item in batch.items:
            d = item.to_dict()
            d["hashtags"] = " ".join(item.hashtags)
            rows.append(",".join(str(d.get(h, "")) for h in headers))
        header_line = ",".join(headers)
        return header_line + "\n" + "\n".join(rows)

    def to_dict(self) -> dict:
        return {
            "dry_run": self.dry_run,
            "batches": {k: v.to_dict() for k, v in self.batches.items()},
        }
