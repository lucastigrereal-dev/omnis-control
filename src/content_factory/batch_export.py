"""W097 — Content Batch Export model."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from src.content_factory.brief import ContentBrief
from src.content_factory.seogram import SEOgramCaption
from src.content_factory.carousel import CarouselPackage
from src.content_factory.reels import ReelScriptPackage
from src.content_factory.stories import StoriesPackage


class ExportFormat(str, Enum):
    JSONL = "jsonl"
    CSV = "csv"
    MARKDOWN = "markdown"


@dataclass
class ExportBatch:
    batch_id: str
    brand: str = ""
    items: list[dict] = field(default_factory=list)
    export_format: str = "jsonl"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    @property
    def item_count(self) -> int:
        return len(self.items)

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "brand": self.brand,
            "item_count": self.item_count,
            "export_format": self.export_format,
            "items": self.items,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ExportBatch":
        return cls(
            batch_id=d["batch_id"],
            brand=d.get("brand", ""),
            items=d.get("items", []),
            export_format=d.get("export_format", "jsonl"),
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )

    def to_jsonl(self) -> str:
        import json
        return "\n".join(json.dumps(item, ensure_ascii=False) for item in self.items)

    def to_csv(self) -> str:
        if not self.items:
            return ""
        headers = list(self.items[0].keys())
        lines = [",".join(headers)]
        for item in self.items:
            row = [str(item.get(h, "")).replace(",", "\\,") for h in headers]
            lines.append(",".join(row))
        return "\n".join(lines)

    def to_markdown(self) -> str:
        lines = [
            f"# Export Batch: {self.batch_id}",
            f"**Brand:** {self.brand} | **Items:** {self.item_count} | **Format:** {self.export_format}",
            f"**Created:** {self.created_at}",
            "",
        ]
        if self.items:
            headers = list(self.items[0].keys())
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("|" + "|".join("---" for _ in headers) + "|")
            for item in self.items:
                row = [str(item.get(h, "")) for h in headers]
                lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)

    def export(self) -> str | None:
        """Return serialized batch in the target format (no file I/O)."""
        if not self.items:
            return None
        if self.export_format == ExportFormat.CSV.value:
            return self.to_csv()
        if self.export_format == ExportFormat.MARKDOWN.value:
            return self.to_markdown()
        return self.to_jsonl()


class BatchExporter:
    """Deterministic batch exporter. Collects packages and exports in target format."""

    def collect_from_brief(
        self,
        batch_id: str,
        briefs: list[ContentBrief],
        export_format: str = "jsonl",
    ) -> ExportBatch:
        import uuid

        batch = ExportBatch(
            batch_id=batch_id,
            brand=briefs[0].brand if briefs else "",
            export_format=export_format,
        )

        for brief in briefs:
            meta = {
                "type": "content_brief",
                "id": brief.brief_id,
                "title": brief.title,
                "brand": brief.brand,
                "format": brief.format,
                "pillar": brief.pillar,
                "objective": brief.objective,
                "keywords": ",".join(brief.keywords),
                "cta": brief.cta,
                "created_at": brief.created_at,
            }
            batch.items.append(meta)

        return batch

    def collect_from_captions(
        self,
        batch_id: str,
        captions: list[SEOgramCaption],
        export_format: str = "jsonl",
    ) -> ExportBatch:
        brand = captions[0].keywords_used[0] if captions and captions[0].keywords_used else ""

        batch = ExportBatch(
            batch_id=batch_id,
            brand=brand,
            export_format=export_format,
        )

        for cap in captions:
            meta = {
                "type": "seogram_caption",
                "id": cap.caption_id,
                "hook": cap.hook,
                "cta": cap.cta,
                "hashtags": " ".join(cap.hashtags),
                "approval_status": cap.approval_status,
                "created_at": cap.created_at,
            }
            batch.items.append(meta)

        return batch

    def collect_from_carousels(
        self,
        batch_id: str,
        packages: list[CarouselPackage],
        export_format: str = "jsonl",
    ) -> ExportBatch:
        brand = packages[0].title if packages else ""

        batch = ExportBatch(
            batch_id=batch_id,
            brand=brand,
            export_format=export_format,
        )

        for pkg in packages:
            meta = {
                "type": "carousel_package",
                "id": pkg.package_id,
                "title": pkg.title,
                "slide_count": str(pkg.slide_count),
                "cta": pkg.cta_final,
                "created_at": pkg.created_at,
            }
            batch.items.append(meta)

        return batch

    def collect_from_reels(
        self,
        batch_id: str,
        packages: list[ReelScriptPackage],
        export_format: str = "jsonl",
    ) -> ExportBatch:
        brand = packages[0].title if packages else ""

        batch = ExportBatch(
            batch_id=batch_id,
            brand=brand,
            export_format=export_format,
        )

        for pkg in packages:
            meta = {
                "type": "reel_script",
                "id": pkg.package_id,
                "title": pkg.title,
                "hook": pkg.hook,
                "scene_count": str(pkg.scene_count),
                "target_duration": str(pkg.target_duration_seconds),
                "cta": pkg.cta,
                "created_at": pkg.created_at,
            }
            batch.items.append(meta)

        return batch

    def collect_from_stories(
        self,
        batch_id: str,
        packages: list[StoriesPackage],
        export_format: str = "jsonl",
    ) -> ExportBatch:
        brand = packages[0].title if packages else ""

        batch = ExportBatch(
            batch_id=batch_id,
            brand=brand,
            export_format=export_format,
        )

        for pkg in packages:
            meta = {
                "type": "stories_package",
                "id": pkg.package_id,
                "title": pkg.title,
                "frame_count": str(pkg.frame_count),
                "swipe_up_link": pkg.swipe_up_link,
                "created_at": pkg.created_at,
            }
            batch.items.append(meta)

        return batch
