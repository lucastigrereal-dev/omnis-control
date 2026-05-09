"""Delivery Templates and Brand Kits models."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class BrandKit:
    kit_id: str
    account_handle: str       # normalised handle (no @)
    display_name: str
    primary_color: str        # hex e.g. "#FF5733"
    secondary_color: str
    tone: str                 # e.g. "inspiracional", "informal", "profissional"
    bio: str
    website: Optional[str] = None
    hashtags: list[str] = field(default_factory=list)
    logo_path: Optional[str] = None   # local path only — NUNCA URL publica
    contact_email: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, account_handle: str, display_name: str, **kwargs) -> "BrandKit":
        return cls(
            kit_id=f"bk_{uuid.uuid4().hex[:8]}",
            account_handle=account_handle.lstrip("@").lower(),
            display_name=display_name,
            **kwargs,
        )

    def to_dict(self) -> dict:
        return {
            "kit_id": self.kit_id,
            "account_handle": self.account_handle,
            "display_name": self.display_name,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "tone": self.tone,
            "bio": self.bio,
            "website": self.website,
            "hashtags": self.hashtags,
            "logo_path": self.logo_path,
            "contact_email": self.contact_email,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BrandKit":
        return cls(**data)


@dataclass
class DeliveryTemplate:
    template_id: str
    name: str
    account_handle: str
    delivery_format: str       # hotel_collab | restaurante_collab | press_kit | custom
    caption_style: str         # formal | casual | inspiracional
    default_hashtag_count: int
    include_metrics: bool
    include_checklist: bool
    custom_notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, name: str, account_handle: str, delivery_format: str, **kwargs) -> "DeliveryTemplate":
        return cls(
            template_id=f"tmpl_{uuid.uuid4().hex[:8]}",
            name=name,
            account_handle=account_handle.lstrip("@").lower(),
            delivery_format=delivery_format,
            **kwargs,
        )

    def to_dict(self) -> dict:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "account_handle": self.account_handle,
            "delivery_format": self.delivery_format,
            "caption_style": self.caption_style,
            "default_hashtag_count": self.default_hashtag_count,
            "include_metrics": self.include_metrics,
            "include_checklist": self.include_checklist,
            "custom_notes": self.custom_notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DeliveryTemplate":
        return cls(**data)
