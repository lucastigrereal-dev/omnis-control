"""Delivery Package models — Pydantic v2.

NUNCA armazena tokens, secrets ou valores reais de credenciais.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PackageType(str, Enum):
    CAROUSEL = "carousel_package"
    SINGLE_POST = "single_post_package"
    REELS_SCRIPT = "reels_script_package"
    CAMPAIGN = "campaign_package"
    BRIEFING = "briefing_package"


class PackageStatus(str, Enum):
    DRAFT = "draft"
    PARTIAL = "partial"
    READY = "ready"
    BLOCKED = "blocked"
    EXPORTED = "exported"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DeliveryPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_id: str
    package_type: PackageType
    title: str = ""
    account_handle: str = ""
    source_queue_id: Optional[str] = None
    source_caption_id: Optional[str] = None
    source_brief_id: Optional[str] = None
    asset_ids: list[str] = Field(default_factory=list)
    output_dir: str = ""
    files: list[str] = Field(default_factory=list)
    manifest_path: str = ""
    status: PackageStatus = PackageStatus.DRAFT
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    seo_keywords: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    cta: str = ""
    created_at: str = Field(default_factory=_now_iso)

    def is_ready(self) -> bool:
        return self.status == PackageStatus.READY and len(self.blockers) == 0

    def safe_summary(self) -> str:
        lines = [
            f"Package: {self.package_id}",
            f"Type: {self.package_type.value}",
            f"Title: {self.title}",
            f"Account: {self.account_handle}",
            f"Status: {self.status.value}",
            f"Files: {len(self.files)}",
        ]
        if self.blockers:
            lines.append(f"Blockers ({len(self.blockers)}):")
            for b in self.blockers:
                lines.append(f"  - {b}")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"  - {w}")
        if self.next_actions:
            lines.append("Next actions:")
            for a in self.next_actions:
                lines.append(f"  - {a}")
        return "\n".join(lines)
