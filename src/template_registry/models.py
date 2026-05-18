"""Template Registry data models."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class TemplateCategory(str, Enum):
    MARKETING = "marketing"
    VIDEO = "video"
    APP_FACTORY = "app_factory"
    SALES = "sales"
    OPS = "ops"
    DESIGN = "design"
    AUTOMATION = "automation"


class TemplateStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class TemplateEntry:
    template_id: str
    name: str
    category: TemplateCategory
    description: str
    status: TemplateStatus = TemplateStatus.DRAFT
    version: int = 1
    tags: list[str] = field(default_factory=list)

    # Content
    content: dict = field(default_factory=dict)
    source_mission_id: Optional[str] = None
    source_output_path: Optional[str] = None

    # Quality
    score: Optional[float] = None  # 0.0–10.0 quality score
    usage_count: int = 0

    # Files
    files: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    deprecated_at: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["category"] = self.category.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TemplateEntry":
        d = dict(d)
        d["category"] = TemplateCategory(d["category"])
        d["status"] = TemplateStatus(d["status"])
        return cls(**d)

    def bump_version(self) -> None:
        self.version += 1
        self.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
