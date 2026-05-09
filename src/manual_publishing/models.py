"""Manual publishing tracker models."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PublishRecord:
    package_id: str
    platform: str
    posted_at: str
    posted_by: str
    url: Optional[str] = None
    notes: Optional[str] = None
    status: str = "posted"

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "platform": self.platform,
            "posted_at": self.posted_at,
            "posted_by": self.posted_by,
            "url": self.url,
            "notes": self.notes,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PublishRecord":
        return cls(
            package_id=d["package_id"],
            platform=d.get("platform", "instagram"),
            posted_at=d.get("posted_at", ""),
            posted_by=d.get("posted_by", ""),
            url=d.get("url"),
            notes=d.get("notes"),
            status=d.get("status", "posted"),
        )
