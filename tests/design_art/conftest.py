"""Shared fixtures for design_art tests."""

from __future__ import annotations

import pytest

from src.design_art.models import (
    BrandVisualProfile,
    VisualDirection,
    DesignBrief,
    AssetSpec,
    CarouselLayoutSpec,
    CreativeReview,
    DIRECTION_TYPE_COLOR_PALETTE,
    DIRECTION_TYPE_TYPOGRAPHY,
    DIRECTION_TYPE_MOODBOARD,
    ARCHETYPE_MINIMALIST,
    ARCHETYPE_BOLD,
    FORMAT_POST,
    FORMAT_CAROUSEL,
    ASSET_TYPE_IMAGE,
    ASPECT_RATIO_1_1,
    TRANSITION_SWIPE,
    REVIEW_STATUS_APPROVED,
)


@pytest.fixture
def sample_profile() -> BrandVisualProfile:
    return BrandVisualProfile.new(
        name="Test Brand",
        description="A test brand profile",
        brand_id="brand_abc123",
        primary_color="#1A1A2E",
        secondary_color="#E94560",
        accent_color="#0F3460",
        heading_font="Montserrat",
        body_font="Open Sans",
        logo_style="lettermark",
        visual_archetype=ARCHETYPE_BOLD,
        mood_keywords=["energetic", "modern", "bold"],
    )


@pytest.fixture
def sample_direction(sample_profile) -> VisualDirection:
    return VisualDirection.new(
        profile_id=sample_profile.id,
        direction_type=DIRECTION_TYPE_COLOR_PALETTE,
        direction_name="Dark Cyber Palette",
        description="High contrast dark palette with neon accents",
        palette_hex=["#1A1A2E", "#E94560", "#0F3460", "#16213E"],
        rules=["background must be dark", "accent for CTAs only"],
    )


@pytest.fixture
def sample_brief(sample_profile, sample_direction) -> DesignBrief:
    return DesignBrief.new(
        title="Summer Launch Post",
        profile_id=sample_profile.id,
        direction_ids=[sample_direction.id],
        objective="Announce summer package",
        target_format=FORMAT_POST,
        dimensions="1080x1080",
        constraints=["use brand palette only", "no serif fonts"],
        copy_text="Discover paradise this summer 🌴",
    )


@pytest.fixture
def sample_asset(sample_brief) -> AssetSpec:
    return AssetSpec.new(
        brief_id=sample_brief.id,
        asset_type=ASSET_TYPE_IMAGE,
        asset_name="hero_background",
        description="Main background image placeholder",
        width=1080,
        height=1080,
    )


@pytest.fixture
def sample_carousel(sample_brief) -> CarouselLayoutSpec:
    return CarouselLayoutSpec.new(
        brief_id=sample_brief.id,
        slide_count=3,
        slide_order=["aspec_a", "aspec_b", "aspec_c"],
        aspect_ratio=ASPECT_RATIO_1_1,
        cover_slide_id="aspec_a",
    )


@pytest.fixture
def sample_review(sample_brief) -> CreativeReview:
    return CreativeReview.new(
        brief_id=sample_brief.id,
        score=85,
        status=REVIEW_STATUS_APPROVED,
        reviewer_notes=["Good contrast", "Clean layout"],
        suggestions=["Consider lighter accent on slide 2"],
    )
