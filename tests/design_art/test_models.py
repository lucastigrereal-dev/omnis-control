"""Tests for P6 Design Art Engine models and constants."""

from __future__ import annotations

import pytest

from src.design_art.models import (
    BrandVisualProfile,
    VisualDirection,
    DesignBrief,
    AssetSpec,
    CarouselLayoutSpec,
    CreativeReview,
    DIRECTION_TYPE_MOODBOARD,
    DIRECTION_TYPE_COLOR_PALETTE,
    DIRECTION_TYPE_TYPOGRAPHY,
    DIRECTION_TYPE_COMPOSITION,
    DIRECTION_TYPE_ICONOGRAPHY,
    DIRECTION_TYPE_PHOTOGRAPHY,
    VALID_DIRECTION_TYPES,
    ARCHETYPE_MINIMALIST,
    ARCHETYPE_BOLD,
    ARCHETYPE_ELEGANT,
    ARCHETYPE_PLAYFUL,
    ARCHETYPE_RUSTIC,
    ARCHETYPE_EDITORIAL,
    ARCHETYPE_CORPORATE,
    VALID_ARCHETYPES,
    FORMAT_CAROUSEL,
    FORMAT_REEL,
    FORMAT_STORY,
    FORMAT_POST,
    FORMAT_BANNER,
    FORMAT_THUMBNAIL,
    VALID_DESIGN_FORMATS,
    ASSET_TYPE_IMAGE,
    ASSET_TYPE_VIDEO,
    ASSET_TYPE_TEXT_OVERLAY,
    ASSET_TYPE_LOGO,
    ASSET_TYPE_BACKGROUND,
    ASSET_TYPE_ICON,
    ASSET_TYPE_CAPTION_BAR,
    VALID_ASSET_TYPES,
    COLOR_MODE_RGB,
    COLOR_MODE_CMYK,
    VALID_COLOR_MODES,
    FILE_FORMAT_PNG,
    FILE_FORMAT_JPG,
    FILE_FORMAT_SVG,
    FILE_FORMAT_MP4,
    FILE_FORMAT_WEBP,
    VALID_FILE_FORMATS,
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_REJECTED,
    REVIEW_STATUS_NEEDS_REVISION,
    VALID_REVIEW_STATUSES,
    ASPECT_RATIO_1_1,
    ASPECT_RATIO_4_5,
    ASPECT_RATIO_16_9,
    ASPECT_RATIO_9_16,
    VALID_ASPECT_RATIOS,
    TRANSITION_SWIPE,
    TRANSITION_FADE,
    TRANSITION_DISSOLVE,
    TRANSITION_NONE,
    VALID_TRANSITIONS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(**kw) -> BrandVisualProfile:
    return BrandVisualProfile.new(
        name=kw.pop("name", "Test Brand"),
        description=kw.pop("description", "A test brand profile"),
        brand_id=kw.pop("brand_id", "brand_abc123"),
        **kw,
    )


def _make_direction(**kw) -> VisualDirection:
    return VisualDirection.new(
        profile_id=kw.pop("profile_id", "bvprof_abc"),
        direction_type=kw.pop("direction_type", DIRECTION_TYPE_COLOR_PALETTE),
        direction_name=kw.pop("direction_name", "Test Palette"),
        description=kw.pop("description", "Test palette description"),
        **kw,
    )


def _make_brief(**kw) -> DesignBrief:
    return DesignBrief.new(
        title=kw.pop("title", "Test Brief"),
        profile_id=kw.pop("profile_id", "bvprof_abc"),
        **kw,
    )


def _make_asset(**kw) -> AssetSpec:
    return AssetSpec.new(
        brief_id=kw.pop("brief_id", "dbrf_abc"),
        asset_type=kw.pop("asset_type", ASSET_TYPE_IMAGE),
        asset_name=kw.pop("asset_name", "test_asset"),
        description=kw.pop("description", "Test asset"),
        **kw,
    )


def _make_carousel(**kw) -> CarouselLayoutSpec:
    return CarouselLayoutSpec.new(
        brief_id=kw.pop("brief_id", "dbrf_abc"),
        slide_count=kw.pop("slide_count", 3),
        **kw,
    )


def _make_review(**kw) -> CreativeReview:
    return CreativeReview.new(
        brief_id=kw.pop("brief_id", "dbrf_abc"),
        **kw,
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_valid_direction_types_count(self):
        assert len(VALID_DIRECTION_TYPES) == 6

    def test_valid_archetypes_count(self):
        assert len(VALID_ARCHETYPES) == 7

    def test_valid_design_formats_count(self):
        assert len(VALID_DESIGN_FORMATS) == 6

    def test_valid_asset_types_count(self):
        assert len(VALID_ASSET_TYPES) == 7

    def test_valid_color_modes_count(self):
        assert len(VALID_COLOR_MODES) == 2

    def test_valid_file_formats_count(self):
        assert len(VALID_FILE_FORMATS) == 5

    def test_valid_review_statuses_count(self):
        assert len(VALID_REVIEW_STATUSES) == 3

    def test_valid_aspect_ratios_count(self):
        assert len(VALID_ASPECT_RATIOS) == 4

    def test_valid_transitions_count(self):
        assert len(VALID_TRANSITIONS) == 4

    def test_direction_types_are_distinct(self):
        vals = {
            DIRECTION_TYPE_MOODBOARD, DIRECTION_TYPE_COLOR_PALETTE,
            DIRECTION_TYPE_TYPOGRAPHY, DIRECTION_TYPE_COMPOSITION,
            DIRECTION_TYPE_ICONOGRAPHY, DIRECTION_TYPE_PHOTOGRAPHY,
        }
        assert len(vals) == 6

    def test_archetypes_are_distinct(self):
        vals = {
            ARCHETYPE_MINIMALIST, ARCHETYPE_BOLD, ARCHETYPE_ELEGANT,
            ARCHETYPE_PLAYFUL, ARCHETYPE_RUSTIC, ARCHETYPE_EDITORIAL,
            ARCHETYPE_CORPORATE,
        }
        assert len(vals) == 7


# ---------------------------------------------------------------------------
# BrandVisualProfile
# ---------------------------------------------------------------------------


class TestBrandVisualProfile:
    def test_new_creates_with_id_prefix(self):
        profile = _make_profile()
        assert profile.id.startswith("bvprof_")

    def test_new_defaults_archetype(self):
        profile = _make_profile()
        assert profile.visual_archetype == ARCHETYPE_MINIMALIST

    def test_new_defaults_colors(self):
        profile = _make_profile()
        assert profile.primary_color == "#000000"
        assert profile.secondary_color == "#FFFFFF"
        assert profile.accent_color == "#FF0000"

    def test_new_defaults_fonts(self):
        profile = _make_profile()
        assert profile.heading_font == "Inter"
        assert profile.body_font == "Inter"

    def test_new_rejects_invalid_archetype(self):
        with pytest.raises(ValueError, match="Invalid visual_archetype"):
            _make_profile(visual_archetype="baroque")

    def test_new_defaults_mood_keywords_empty(self):
        profile = _make_profile()
        assert profile.mood_keywords == []

    def test_round_trip_dict(self):
        profile = _make_profile(
            name="Bold Brand",
            brand_id="brand_xyz",
            primary_color="#FF5733",
            visual_archetype=ARCHETYPE_BOLD,
            mood_keywords=["vibrant", "loud"],
        )
        d = profile.to_dict()
        restored = BrandVisualProfile.from_dict(d)
        assert restored.id == profile.id
        assert restored.name == profile.name
        assert restored.primary_color == "#FF5733"
        assert restored.visual_archetype == ARCHETYPE_BOLD
        assert restored.mood_keywords == ["vibrant", "loud"]

    @pytest.mark.parametrize("val", sorted(VALID_ARCHETYPES))
    def test_all_valid_archetypes(self, val):
        profile = _make_profile(visual_archetype=val)
        assert profile.visual_archetype == val

    def test_default_notes_is_none(self):
        profile = _make_profile()
        assert profile.notes is None


# ---------------------------------------------------------------------------
# VisualDirection
# ---------------------------------------------------------------------------


class TestVisualDirection:
    def test_new_creates_with_id_prefix(self):
        direction = _make_direction()
        assert direction.id.startswith("vdir_")

    def test_new_defaults_empty_lists(self):
        direction = _make_direction()
        assert direction.rules == []
        assert direction.references == []
        assert direction.palette_hex == []

    def test_new_rejects_invalid_direction_type(self):
        with pytest.raises(ValueError, match="Invalid direction_type"):
            _make_direction(direction_type="cartoon")

    def test_round_trip_dict(self):
        direction = _make_direction(
            direction_type=DIRECTION_TYPE_TYPOGRAPHY,
            direction_name="Serif Authority",
            description="Uses serif fonts for trust signals",
            rules=["heading: serif", "body: sans-serif"],
            palette_hex=["#333333", "#FFFFFF"],
            example_descriptor="Like New York Times masthead",
        )
        d = direction.to_dict()
        restored = VisualDirection.from_dict(d)
        assert restored.id == direction.id
        assert restored.direction_name == "Serif Authority"
        assert restored.direction_type == DIRECTION_TYPE_TYPOGRAPHY
        assert restored.rules == ["heading: serif", "body: sans-serif"]
        assert restored.example_descriptor == "Like New York Times masthead"

    @pytest.mark.parametrize("val", sorted(VALID_DIRECTION_TYPES))
    def test_all_valid_direction_types(self, val):
        direction = _make_direction(direction_type=val)
        assert direction.direction_type == val

    def test_default_example_descriptor_empty(self):
        direction = _make_direction()
        assert direction.example_descriptor == ""


# ---------------------------------------------------------------------------
# DesignBrief
# ---------------------------------------------------------------------------


class TestDesignBrief:
    def test_new_creates_with_id_prefix(self):
        brief = _make_brief()
        assert brief.id.startswith("dbrf_")

    def test_new_defaults(self):
        brief = _make_brief()
        assert brief.target_format == FORMAT_POST
        assert brief.dimensions == "1080x1080"
        assert brief.direction_ids == []
        assert brief.constraints == []

    def test_new_rejects_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid target_format"):
            _make_brief(target_format="billboard")

    def test_round_trip_dict(self):
        brief = _make_brief(
            title="Carousel Campaign",
            direction_ids=["vdir_a", "vdir_b"],
            objective="Sell packages",
            target_format=FORMAT_CAROUSEL,
            dimensions="1080x1350",
            constraints=["no animations"],
            copy_text="Book now!",
        )
        d = brief.to_dict()
        restored = DesignBrief.from_dict(d)
        assert restored.id == brief.id
        assert restored.title == "Carousel Campaign"
        assert restored.target_format == FORMAT_CAROUSEL
        assert restored.direction_ids == ["vdir_a", "vdir_b"]

    def test_default_copy_text_is_none(self):
        brief = _make_brief()
        assert brief.copy_text is None

    @pytest.mark.parametrize("val", sorted(VALID_DESIGN_FORMATS))
    def test_all_valid_design_formats(self, val):
        brief = _make_brief(target_format=val)
        assert brief.target_format == val


# ---------------------------------------------------------------------------
# AssetSpec
# ---------------------------------------------------------------------------


class TestAssetSpec:
    def test_new_creates_with_id_prefix(self):
        asset = _make_asset()
        assert asset.id.startswith("aspec_")

    def test_new_defaults(self):
        asset = _make_asset()
        assert asset.width == 1080
        assert asset.height == 1080
        assert asset.dpi == 72
        assert asset.color_mode == COLOR_MODE_RGB
        assert asset.file_format == FILE_FORMAT_PNG
        assert asset.placeholder_color == "#CCCCCC"
        assert asset.layer_order == 0

    def test_new_rejects_invalid_asset_type(self):
        with pytest.raises(ValueError, match="Invalid asset_type"):
            _make_asset(asset_type="3d_model")

    def test_new_rejects_invalid_color_mode(self):
        with pytest.raises(ValueError, match="Invalid color_mode"):
            _make_asset(color_mode="lab")

    def test_new_rejects_invalid_file_format(self):
        with pytest.raises(ValueError, match="Invalid file_format"):
            _make_asset(file_format="psd")

    def test_new_rejects_negative_width(self):
        with pytest.raises(ValueError, match="Dimensions must be positive"):
            _make_asset(width=0)

    def test_new_rejects_negative_height(self):
        with pytest.raises(ValueError, match="Dimensions must be positive"):
            _make_asset(height=-5)

    def test_new_rejects_negative_dpi(self):
        with pytest.raises(ValueError, match="DPI must be positive"):
            _make_asset(dpi=0)

    def test_round_trip_dict(self):
        asset = _make_asset(
            asset_type=ASSET_TYPE_VIDEO,
            asset_name="intro_animation",
            description="Opening animation",
            width=1920,
            height=1080,
            dpi=300,
            color_mode=COLOR_MODE_CMYK,
            file_format=FILE_FORMAT_MP4,
            placeholder_color="#000000",
            layer_order=0,
        )
        d = asset.to_dict()
        restored = AssetSpec.from_dict(d)
        assert restored.id == asset.id
        assert restored.asset_name == "intro_animation"
        assert restored.width == 1920
        assert restored.dpi == 300
        assert restored.color_mode == COLOR_MODE_CMYK
        assert restored.file_format == FILE_FORMAT_MP4

    @pytest.mark.parametrize("val", sorted(VALID_ASSET_TYPES))
    def test_all_valid_asset_types(self, val):
        asset = _make_asset(asset_type=val)
        assert asset.asset_type == val


# ---------------------------------------------------------------------------
# CarouselLayoutSpec
# ---------------------------------------------------------------------------


class TestCarouselLayoutSpec:
    def test_new_creates_with_id_prefix(self):
        layout = _make_carousel()
        assert layout.id.startswith("clyt_")

    def test_new_defaults(self):
        layout = _make_carousel()
        assert layout.transition == TRANSITION_SWIPE
        assert layout.aspect_ratio == ASPECT_RATIO_1_1
        assert layout.slide_order == []
        assert layout.cover_slide_id == ""

    def test_new_rejects_invalid_transition(self):
        with pytest.raises(ValueError, match="Invalid transition"):
            _make_carousel(transition="explode")

    def test_new_rejects_invalid_aspect_ratio(self):
        with pytest.raises(ValueError, match="Invalid aspect_ratio"):
            _make_carousel(aspect_ratio="21:9")

    def test_new_rejects_zero_slide_count(self):
        with pytest.raises(ValueError, match="slide_count must be positive"):
            _make_carousel(slide_count=0)

    def test_new_rejects_negative_slide_count(self):
        with pytest.raises(ValueError, match="slide_count must be positive"):
            _make_carousel(slide_count=-1)

    def test_round_trip_dict(self):
        layout = _make_carousel(
            slide_count=5,
            slide_order=["a", "b", "c", "d", "e"],
            transition=TRANSITION_FADE,
            aspect_ratio=ASPECT_RATIO_4_5,
            cover_slide_id="a",
        )
        d = layout.to_dict()
        restored = CarouselLayoutSpec.from_dict(d)
        assert restored.id == layout.id
        assert restored.slide_count == 5
        assert restored.transition == TRANSITION_FADE
        assert restored.aspect_ratio == ASPECT_RATIO_4_5

    @pytest.mark.parametrize("val", sorted(VALID_TRANSITIONS))
    def test_all_valid_transitions(self, val):
        layout = _make_carousel(transition=val)
        assert layout.transition == val


# ---------------------------------------------------------------------------
# CreativeReview
# ---------------------------------------------------------------------------


class TestCreativeReview:
    def test_new_creates_with_id_prefix(self):
        review = _make_review()
        assert review.id.startswith("crvw_")

    def test_new_defaults(self):
        review = _make_review()
        assert review.score == 0
        assert review.status == REVIEW_STATUS_NEEDS_REVISION
        assert review.reviewer_notes == []
        assert review.issues == []
        assert review.suggestions == []

    def test_new_rejects_invalid_status(self):
        with pytest.raises(ValueError, match="Invalid status"):
            _make_review(status="pending")

    def test_new_rejects_negative_score(self):
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            _make_review(score=-1)

    def test_new_rejects_score_above_100(self):
        with pytest.raises(ValueError, match="Score must be between 0 and 100"):
            _make_review(score=101)

    def test_score_at_boundaries(self):
        assert _make_review(score=0).score == 0
        assert _make_review(score=100).score == 100

    def test_is_approved_true(self):
        review = _make_review(status=REVIEW_STATUS_APPROVED)
        assert review.is_approved is True

    def test_is_approved_false_for_needs_revision(self):
        review = _make_review(status=REVIEW_STATUS_NEEDS_REVISION)
        assert review.is_approved is False

    def test_is_approved_false_for_rejected(self):
        review = _make_review(status=REVIEW_STATUS_REJECTED)
        assert review.is_approved is False

    def test_has_issues_false_by_default(self):
        review = _make_review()
        assert review.has_issues is False

    def test_has_issues_true(self):
        review = _make_review(issues=["low contrast"])
        assert review.has_issues is True

    def test_round_trip_dict(self):
        review = _make_review(
            score=92,
            status=REVIEW_STATUS_APPROVED,
            reviewer_notes=["Excellent composition"],
            issues=[],
            suggestions=["Try bolder CTA"],
        )
        d = review.to_dict()
        restored = CreativeReview.from_dict(d)
        assert restored.id == review.id
        assert restored.score == 92
        assert restored.status == REVIEW_STATUS_APPROVED

    @pytest.mark.parametrize("val", sorted(VALID_REVIEW_STATUSES))
    def test_all_valid_review_statuses(self, val):
        review = _make_review(status=val)
        assert review.status == val
