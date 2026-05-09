"""Delivery Templates and Brand Kits service — JSONL persistence."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.delivery_templates.models import BrandKit, DeliveryTemplate

BRAND_KITS_LOG = Path("data/brand_kits.jsonl")
TEMPLATES_LOG = Path("data/delivery_templates.jsonl")

VALID_FORMATS = {"hotel_collab", "restaurante_collab", "press_kit", "custom"}
VALID_STYLES = {"formal", "casual", "inspiracional"}


class BrandKitNotFoundError(ValueError):
    pass


class TemplateNotFoundError(ValueError):
    pass


class ValidationError(ValueError):
    pass


def _load_jsonl(path: Path, cls) -> list:
    if not path.exists():
        return []
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                items.append(cls.from_dict(json.loads(line)))
            except Exception:
                continue
    return items


def _save_jsonl(path: Path, items: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")


# ── Brand Kits ──────────────────────────────────────────────────────────────

def set_brand_kit(
    account_handle: str,
    display_name: str,
    primary_color: str,
    secondary_color: str,
    tone: str,
    bio: str,
    website: Optional[str] = None,
    hashtags: Optional[list[str]] = None,
    logo_path: Optional[str] = None,
    contact_email: Optional[str] = None,
    log_path: Path = None,
) -> BrandKit:
    if log_path is None:
        log_path = BRAND_KITS_LOG

    handle = account_handle.lstrip("@").lower()
    kits = _load_jsonl(log_path, BrandKit)

    existing = next((k for k in kits if k.account_handle == handle), None)
    if existing:
        existing.display_name = display_name
        existing.primary_color = primary_color
        existing.secondary_color = secondary_color
        existing.tone = tone
        existing.bio = bio
        existing.website = website
        existing.hashtags = hashtags or []
        existing.logo_path = logo_path
        existing.contact_email = contact_email
        existing.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _save_jsonl(log_path, kits)
        return existing

    kit = BrandKit.new(
        account_handle=handle,
        display_name=display_name,
        primary_color=primary_color,
        secondary_color=secondary_color,
        tone=tone,
        bio=bio,
        website=website,
        hashtags=hashtags or [],
        logo_path=logo_path,
        contact_email=contact_email,
    )
    kits.append(kit)
    _save_jsonl(log_path, kits)
    return kit


def get_brand_kit(account_handle: str, log_path: Path = None) -> BrandKit:
    if log_path is None:
        log_path = BRAND_KITS_LOG
    handle = account_handle.lstrip("@").lower()
    kits = _load_jsonl(log_path, BrandKit)
    found = next((k for k in kits if k.account_handle == handle), None)
    if not found:
        raise BrandKitNotFoundError(f"Brand kit for '@{handle}' not found")
    return found


def list_brand_kits(log_path: Path = None) -> list[BrandKit]:
    if log_path is None:
        log_path = BRAND_KITS_LOG
    return _load_jsonl(log_path, BrandKit)


# ── Delivery Templates ───────────────────────────────────────────────────────

def create_template(
    name: str,
    account_handle: str,
    delivery_format: str = "custom",
    caption_style: str = "casual",
    default_hashtag_count: int = 5,
    include_metrics: bool = True,
    include_checklist: bool = True,
    custom_notes: Optional[str] = None,
    log_path: Path = None,
) -> DeliveryTemplate:
    if log_path is None:
        log_path = TEMPLATES_LOG
    if delivery_format not in VALID_FORMATS:
        raise ValidationError(f"delivery_format deve ser um de: {', '.join(sorted(VALID_FORMATS))}")
    if caption_style not in VALID_STYLES:
        raise ValidationError(f"caption_style deve ser um de: {', '.join(sorted(VALID_STYLES))}")
    if default_hashtag_count < 0 or default_hashtag_count > 30:
        raise ValidationError("default_hashtag_count deve estar entre 0 e 30")

    tmpl = DeliveryTemplate.new(
        name=name,
        account_handle=account_handle,
        delivery_format=delivery_format,
        caption_style=caption_style,
        default_hashtag_count=default_hashtag_count,
        include_metrics=include_metrics,
        include_checklist=include_checklist,
        custom_notes=custom_notes,
    )
    templates = _load_jsonl(log_path, DeliveryTemplate)
    templates.append(tmpl)
    _save_jsonl(log_path, templates)
    return tmpl


def list_templates(account_handle: Optional[str] = None, log_path: Path = None) -> list[DeliveryTemplate]:
    if log_path is None:
        log_path = TEMPLATES_LOG
    templates = _load_jsonl(log_path, DeliveryTemplate)
    if account_handle:
        handle = account_handle.lstrip("@").lower()
        templates = [t for t in templates if t.account_handle == handle]
    return templates


def get_template(template_id: str, log_path: Path = None) -> DeliveryTemplate:
    if log_path is None:
        log_path = TEMPLATES_LOG
    templates = _load_jsonl(log_path, DeliveryTemplate)
    for t in templates:
        if t.template_id == template_id or t.template_id.startswith(template_id):
            return t
    raise TemplateNotFoundError(f"Template '{template_id}' not found")
