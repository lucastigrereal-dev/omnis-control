"""Tests for P6 Design Art Engine exporters."""

from __future__ import annotations

import pytest

from src.design_art.exporters import (
    export_profile_markdown,
    export_direction_markdown,
    export_design_brief_markdown,
)
from src.design_art.models import (
    BrandVisualProfile,
    VisualDirection,
    DesignBrief,
    AssetSpec,
    CarouselLayoutSpec,
    CreativeReview,
    DIRECTION_TYPE_COLOR_PALETTE,
    DIRECTION_TYPE_TYPOGRAPHY,
    ARCHETYPE_BOLD,
    FORMAT_CAROUSEL,
    FORMAT_POST,
    ASSET_TYPE_IMAGE,
    ASSET_TYPE_TEXT_OVERLAY,
    ASSET_TYPE_LOGO,
    ASPECT_RATIO_1_1,
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_REJECTED,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile() -> BrandVisualProfile:
    return BrandVisualProfile.new(
        name="Test Brand",
        description="A test brand profile",
        brand_id="brand_abc",
        primary_color="#1A1A2E",
        secondary_color="#E94560",
        accent_color="#0F3460",
        heading_font="Montserrat",
        body_font="Open Sans",
        visual_archetype=ARCHETYPE_BOLD,
        mood_keywords=["energetic", "bold"],
    )


def _make_direction() -> VisualDirection:
    return VisualDirection.new(
        profile_id="bvprof_abc",
        direction_type=DIRECTION_TYPE_COLOR_PALETTE,
        direction_name="Dark Palette",
        description="High contrast dark palette",
        palette_hex=["#1A1A2E", "#E94560", "#0F3460"],
        rules=["background must be dark"],
        references=["ref_dark_mode_guide"],
        example_descriptor="Like Spotify dark mode",
    )


def _make_brief() -> DesignBrief:
    return DesignBrief.new(
        title="Summer Launch",
        profile_id="bvprof_abc",
        direction_ids=["vdir_a"],
        objective="Announce summer sale",
        target_format=FORMAT_POST,
        dimensions="1080x1080",
        constraints=["brand palette only"],
        copy_text="Discover paradise!",
    )


def _make_assets(brief_id: str) -> list[AssetSpec]:
    return [
        AssetSpec.new(brief_id, ASSET_TYPE_IMAGE, "bg", "Background", layer_order=0),
        AssetSpec.new(brief_id, ASSET_TYPE_TEXT_OVERLAY, "text", "Text overlay", layer_order=1),
        AssetSpec.new(brief_id, ASSET_TYPE_LOGO, "logo", "Logo", layer_order=2),
    ]


def _make_carousel(brief_id: str) -> CarouselLayoutSpec:
    return CarouselLayoutSpec.new(
        brief_id=brief_id,
        slide_count=3,
        slide_order=["a", "b", "c"],
        cover_slide_id="a",
    )


def _make_review(brief_id: str) -> CreativeReview:
    return CreativeReview.new(
        brief_id=brief_id,
        score=85,
        status=REVIEW_STATUS_APPROVED,
        issues=[],
        suggestions=["try bolder CTA"],
    )


# ---------------------------------------------------------------------------
# export_profile_markdown
# ---------------------------------------------------------------------------


class TestExportProfileMarkdown:
    def test_returns_string(self):
        profile = _make_profile()
        result = export_profile_markdown(profile)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_profile_name(self):
        profile = _make_profile()
        result = export_profile_markdown(profile)
        assert "Test Brand" in result

    def test_contains_colors(self):
        profile = _make_profile()
        result = export_profile_markdown(profile)
        assert "#1A1A2E" in result
        assert "#E94560" in result

    def test_contains_fonts(self):
        profile = _make_profile()
        result = export_profile_markdown(profile)
        assert "Montserrat" in result
        assert "Open Sans" in result

    def test_contains_archetype(self):
        profile = _make_profile()
        result = export_profile_markdown(profile)
        assert ARCHETYPE_BOLD in result

    def test_contains_markdown_header(self):
        profile = _make_profile()
        result = export_profile_markdown(profile)
        assert result.startswith("# Brand Visual Profile:")


# ---------------------------------------------------------------------------
# export_direction_markdown
# ---------------------------------------------------------------------------


class TestExportDirectionMarkdown:
    def test_returns_string(self):
        direction = _make_direction()
        result = export_direction_markdown(direction)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_direction_name(self):
        direction = _make_direction()
        result = export_direction_markdown(direction)
        assert "Dark Palette" in result

    def test_contains_palette_hex(self):
        direction = _make_direction()
        result = export_direction_markdown(direction)
        assert "#1A1A2E" in result
        assert "#E94560" in result

    def test_contains_rules(self):
        direction = _make_direction()
        result = export_direction_markdown(direction)
        assert "background must be dark" in result

    def test_contains_references(self):
        direction = _make_direction()
        result = export_direction_markdown(direction)
        assert "ref_dark_mode_guide" in result

    def test_contains_example_descriptor(self):
        direction = _make_direction()
        result = export_direction_markdown(direction)
        assert "Spotify dark mode" in result

    def test_no_example_section_when_empty(self):
        direction = VisualDirection.new(
            "p1", DIRECTION_TYPE_TYPOGRAPHY, "T", "Desc",
        )
        result = export_direction_markdown(direction)
        assert "Example" not in result


# ---------------------------------------------------------------------------
# export_design_brief_markdown
# ---------------------------------------------------------------------------


class TestExportDesignBriefMarkdown:
    def test_basic_brief(self):
        brief = _make_brief()
        result = export_design_brief_markdown(brief)
        assert isinstance(result, str)
        assert "Summer Launch" in result
        assert brief.id in result

    def test_brief_with_profile(self):
        brief = _make_brief()
        profile = _make_profile()
        result = export_design_brief_markdown(brief, profile=profile)
        assert "Test Brand" in result
        assert "#1A1A2E" in result

    def test_brief_with_directions(self):
        brief = _make_brief()
        direction = _make_direction()
        result = export_design_brief_markdown(brief, directions=[direction])
        assert "Dark Palette" in result
        assert "## Visual Directions" in result

    def test_brief_with_assets(self):
        brief = _make_brief()
        assets = _make_assets(brief.id)
        result = export_design_brief_markdown(brief, assets=assets)
        assert "## Asset Specifications" in result
        assert "bg" in result
        assert "text" in result
        assert "logo" in result

    def test_brief_with_carousel(self):
        brief = _make_brief()
        carousel = _make_carousel(brief.id)
        result = export_design_brief_markdown(brief, carousel=carousel)
        assert "## Carousel Layout" in result
        assert "3" in result

    def test_brief_with_review(self):
        brief = _make_brief()
        review = _make_review(brief.id)
        result = export_design_brief_markdown(brief, review=review)
        assert "## Creative Review" in result
        assert "approved" in result
        assert "85" in result

    def test_brief_with_rejected_review(self):
        brief = _make_brief()
        review = CreativeReview.new(
            brief.id, score=30, status=REVIEW_STATUS_REJECTED,
            issues=["off-brand colors"],
            suggestions=["use palette"],
        )
        result = export_design_brief_markdown(brief, review=review)
        assert "rejected" in result
        assert "off-brand colors" in result

    def test_full_package(self):
        brief = _make_brief()
        profile = _make_profile()
        direction = _make_direction()
        assets = _make_assets(brief.id)
        carousel = _make_carousel(brief.id)
        review = _make_review(brief.id)
        result = export_design_brief_markdown(
            brief, profile=profile, directions=[direction],
            assets=assets, carousel=carousel, review=review,
        )
        assert isinstance(result, str)
        assert len(result) > 500

    def test_brief_constraints_in_output(self):
        brief = _make_brief()
        result = export_design_brief_markdown(brief)
        assert "brand palette only" in result

    def test_brief_copy_text_in_output(self):
        brief = _make_brief()
        result = export_design_brief_markdown(brief)
        assert "Discover paradise!" in result

    def test_returns_markdown_header(self):
        brief = _make_brief()
        result = export_design_brief_markdown(brief)
        assert result.startswith("# Design Brief:")
