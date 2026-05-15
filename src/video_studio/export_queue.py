"""W109 — Video Export Queue."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import csv
import io

from src.video_studio.cut_plan import CutSegment


@dataclass
class ExportEntry:
    entry_id: str
    asset_id: str = ""
    cut_id: str = ""
    platform: str = "instagram"
    title: str = ""
    caption: str = ""
    status: str = "queued"
    approval_status: str = "draft"
    export_path: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "asset_id": self.asset_id,
            "cut_id": self.cut_id,
            "platform": self.platform,
            "title": self.title,
            "caption": self.caption,
            "status": self.status,
            "approval_status": self.approval_status,
            "export_path": self.export_path,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ExportEntry":
        return cls(
            entry_id=d["entry_id"],
            asset_id=d.get("asset_id", ""),
            cut_id=d.get("cut_id", ""),
            platform=d.get("platform", "instagram"),
            title=d.get("title", ""),
            caption=d.get("caption", ""),
            status=d.get("status", "queued"),
            approval_status=d.get("approval_status", "draft"),
            export_path=d.get("export_path", ""),
            created_at=d.get("created_at", ""),
        )


@dataclass
class VideoExportQueue:
    queue_id: str
    entries: list[ExportEntry] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def add_entry(self, entry: ExportEntry) -> None:
        self.entries.append(entry)

    def to_dict(self) -> dict:
        return {
            "queue_id": self.queue_id,
            "entries": [e.to_dict() for e in self.entries],
            "entry_count": self.entry_count,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "VideoExportQueue":
        q = cls(
            queue_id=d["queue_id"],
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )
        for e in d.get("entries", []):
            q.entries.append(ExportEntry.from_dict(e))
        return q

    def to_csv(self) -> str:
        output = io.StringIO()
        fieldnames = [
            "entry_id", "asset_id", "cut_id", "platform", "title",
            "caption", "status", "approval_status", "export_path",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for e in self.entries:
            writer.writerow({
                "entry_id": e.entry_id,
                "asset_id": e.asset_id,
                "cut_id": e.cut_id,
                "platform": e.platform,
                "title": e.title,
                "caption": e.caption,
                "status": e.status,
                "approval_status": e.approval_status,
                "export_path": e.export_path,
            })
        return output.getvalue()

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        lines = [
            f"# Video Export Queue: {self.queue_id}",
            f"**Entries:** {self.entry_count} | **Created:** {self.created_at}",
            "",
            "| # | Asset | Cut | Platform | Title | Status | Approval |",
            "|---|---|---|---|---|---|---|",
        ]
        for i, e in enumerate(self.entries, 1):
            lines.append(
                f"| {i} | {e.asset_id} | {e.cut_id} | {e.platform} | "
                f"{e.title[:30]} | {e.status} | {e.approval_status} |"
            )
        return "\n".join(lines)


class VideoExportQueueBuilder:
    """Builds export queue entries from cut segments."""

    def build(
        self,
        asset_id: str,
        cut_segments: list[CutSegment],
    ) -> VideoExportQueue:
        import uuid

        queue = VideoExportQueue(queue_id=str(uuid.uuid4())[:8])

        for cs in cut_segments:
            entry = ExportEntry(
                entry_id=str(uuid.uuid4())[:8],
                asset_id=asset_id,
                cut_id=cs.cut_id,
                platform=cs.platform,
                title=cs.title,
                caption=cs.hook,
                export_path=f"export/{cs.cut_id}/{cs.platform}/",
            )
            queue.add_entry(entry)

        return queue
