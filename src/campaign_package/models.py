"""Campaign package models."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    ZIPPED = "zipped"


@dataclass
class CampaignPost:
    post_number: int
    title: str
    package_id: Optional[str] = None
    account_handle: str = ""
    scheduled_date: str = ""
    status: str = "draft"

    def to_dict(self) -> dict:
        return {
            "post_number": self.post_number,
            "title": self.title,
            "package_id": self.package_id,
            "account_handle": self.account_handle,
            "scheduled_date": self.scheduled_date,
            "status": self.status,
        }


@dataclass
class Campaign:
    campaign_id: str
    name: str
    post_count: int
    status: CampaignStatus
    account_handle: str
    created_at: str
    output_dir: str
    zip_path: Optional[str] = None
    posts: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "post_count": self.post_count,
            "status": self.status.value,
            "account_handle": self.account_handle,
            "created_at": self.created_at,
            "output_dir": self.output_dir,
            "zip_path": self.zip_path,
            "posts": [p.to_dict() for p in self.posts],
            "warnings": self.warnings,
        }
