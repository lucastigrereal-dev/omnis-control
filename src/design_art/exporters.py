"""P6 Design Art Engine — local exporters (markdown).

Dry-run only. No upload, no API, no network, no image generation.
"""

from __future__ import annotations

import io
from typing import Optional

from src.design_art.models import (
    BrandVisualProfile,
    VisualDirection,
    DesignBrief,
    AssetSpec,
    CarouselLayoutSpec,
    CreativeReview,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _md_bullet(label: str, value: str) -> str:
    return f"- **{label}:** {value}\n"


def _md_bullet_list(label: str, values: list[str]) -> str:
    if not values:
        return ""
    items = ", ".join(values)
    return f"- **{label}:** {items}\n"


# ---------------------------------------------------------------------------
# Brand Visual Profile → Markdown
# ---------------------------------------------------------------------------


def export_profile_markdown(profile: BrandVisualProfile) -> str:
    """Render a BrandVisualProfile as markdown."""
    buf = io.StringIO()
    buf.write(f"# Brand Visual Profile: {profile.name}\n\n")
    buf.write(f"**ID:** `{profile.id}`\n")
    buf.write(f"**Brand:** `{profile.brand_id}`\n")
    buf.write(f"**Description:** {profile.description}\n\n")

    buf.write("## Colors\n\n")
    buf.write(f"- **Primary:** `{profile.primary_color}`\n")
    buf.write(f"- **Secondary:** `{profile.secondary_color}`\n")
    buf.write(f"- **Accent:** `{profile.accent_color}`\n\n")

    buf.write("## Typography\n\n")
    buf.write(f"- **Heading:** {profile.heading_font}\n")
    buf.write(f"- **Body:** {profile.body_font}\n\n")

    buf.write("## Style\n\n")
    buf.write(f"- **Logo:** {profile.logo_style}\n")
    buf.write(f"- **Archetype:** {profile.visual_archetype}\n")
    buf.write(f"- **Mood:** {', '.join(profile.mood_keywords)}\n")

    return buf.getvalue()


# ---------------------------------------------------------------------------
# Visual Direction → Markdown
# ---------------------------------------------------------------------------


def export_direction_markdown(direction: VisualDirection) -> str:
    """Render a VisualDirection as markdown."""
    buf = io.StringIO()
    buf.write(f"# Visual Direction: {direction.direction_name}\n\n")
    buf.write(f"**ID:** `{direction.id}`\n")
    buf.write(f"**Type:** {direction.direction_type}\n")
    buf.write(f"**Profile:** `{direction.profile_id}`\n")
    buf.write(f"**Description:** {direction.description}\n\n")

    if direction.palette_hex:
        buf.write("## Palette\n\n")
        for h in direction.palette_hex:
            buf.write(f"- `{h}`\n")
        buf.write("\n")

    if direction.rules:
        buf.write("## Rules\n\n")
        for r in direction.rules:
            buf.write(f"- {r}\n")
        buf.write("\n")

    if direction.references:
        buf.write("## References\n\n")
        for ref in direction.references:
            buf.write(f"- `{ref}`\n")
        buf.write("\n")

    if direction.example_descriptor:
        buf.write("## Example\n\n")
        buf.write(f"{direction.example_descriptor}\n\n")

    return buf.getvalue()


# ---------------------------------------------------------------------------
# Design Brief → Markdown
# ---------------------------------------------------------------------------


def export_design_brief_markdown(
    brief: DesignBrief,
    profile: Optional[BrandVisualProfile] = None,
    directions: Optional[list[VisualDirection]] = None,
    assets: Optional[list[AssetSpec]] = None,
    carousel: Optional[CarouselLayoutSpec] = None,
    review: Optional[CreativeReview] = None,
) -> str:
    """Render a complete DesignBrief package as markdown.

    Accepts optional related entities for a full spec dump.
    """
    buf = io.StringIO()
    buf.write(f"# Design Brief: {brief.title}\n\n")
    buf.write(f"**ID:** `{brief.id}`\n")
    buf.write(f"**Format:** {brief.target_format}\n")
    buf.write(f"**Dimensions:** {brief.dimensions}\n")
    buf.write(f"**Objective:** {brief.objective}\n\n")

    if brief.constraints:
        buf.write("## Constraints\n\n")
        for c in brief.constraints:
            buf.write(f"- {c}\n")
        buf.write("\n")

    if brief.copy_text:
        buf.write("## Copy / Text\n\n")
        buf.write(f"```\n{brief.copy_text}\n```\n\n")

    if profile is not None:
        buf.write("---\n\n")
        buf.write(export_profile_markdown(profile))

    if directions:
        buf.write("---\n\n")
        buf.write("## Visual Directions\n\n")
        for d in directions:
            buf.write(f"### {d.direction_name} (`{d.id}`)\n\n")
            buf.write(f"- **Type:** {d.direction_type}\n")
            buf.write(f"- **Description:** {d.description}\n")
            if d.palette_hex:
                buf.write(f"- **Palette:** {', '.join(f'`{h}`' for h in d.palette_hex)}\n")
            if d.rules:
                buf.write(f"- **Rules:** {', '.join(d.rules)}\n")
            buf.write("\n")

    if assets:
        buf.write("---\n\n")
        buf.write("## Asset Specifications\n\n")
        buf.write("| # | Name | Type | Dimensions | DPI | Format | Color Mode | Placeholder |\n")
        buf.write("|---|---|---|---|---|---|---|---|\n")
        for a in sorted(assets, key=lambda x: x.layer_order):
            buf.write(
                f"| {a.layer_order} | {a.asset_name} | {a.asset_type} | "
                f"{a.width}x{a.height} | {a.dpi} | {a.file_format} | "
                f"{a.color_mode} | `{a.placeholder_color}` |\n"
            )
        buf.write("\n")

    if carousel is not None:
        buf.write("---\n\n")
        buf.write("## Carousel Layout\n\n")
        buf.write(f"- **ID:** `{carousel.id}`\n")
        buf.write(f"- **Slides:** {carousel.slide_count}\n")
        buf.write(f"- **Aspect Ratio:** {carousel.aspect_ratio}\n")
        buf.write(f"- **Transition:** {carousel.transition}\n")
        if carousel.cover_slide_id:
            buf.write(f"- **Cover Slide:** `{carousel.cover_slide_id}`\n")
        if carousel.slide_order:
            buf.write(f"- **Slide Order:** {' → '.join(f'`{s}`' for s in carousel.slide_order)}\n")
        buf.write("\n")

    if review is not None:
        buf.write("---\n\n")
        buf.write("## Creative Review\n\n")
        buf.write(f"- **Status:** {review.status}\n")
        buf.write(f"- **Score:** {review.score}/100\n")
        if review.issues:
            buf.write("- **Issues:**\n")
            for i in review.issues:
                buf.write(f"  - {i}\n")
        if review.suggestions:
            buf.write("- **Suggestions:**\n")
            for s in review.suggestions:
                buf.write(f"  - {s}\n")
        buf.write("\n")

    return buf.getvalue()
