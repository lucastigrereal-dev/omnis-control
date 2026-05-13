"""Tests for P6 Design Art Engine service — DesignArtPlanner."""

from __future__ import annotations

import pytest

from src.design_art.service import (
    DesignArtPlanner,
    ValidationResult,
    _dimensions_for_format,
)
from src.design_art.models import (
    DIRECTION_TYPE_COLOR_PALETTE,
    DIRECTION_TYPE_TYPOGRAPHY,
    DIRECTION_TYPE_MOODBOARD,
    ARCHETYPE_BOLD,
    ARCHETYPE_MINIMALIST,
    FORMAT_POST,
    FORMAT_CAROUSEL,
    FORMAT_STORY,
    ASSET_TYPE_IMAGE,
    ASSET_TYPE_TEXT_OVERLAY,
    ASSET_TYPE_LOGO,
    ASPECT_RATIO_1_1,
    ASPECT_RATIO_4_5,
    ASPECT_RATIO_9_16,
    TRANSITION_SWIPE,
    TRANSITION_FADE,
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_REJECTED,
    REVIEW_STATUS_NEEDS_REVISION,
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


def _setup_planner() -> DesignArtPlanner:
    return DesignArtPlanner(dry_run=True)


# ---------------------------------------------------------------------------
# _dimensions_for_format helper
# ---------------------------------------------------------------------------


class TestDimensionsForFormat:
    def test_post_1_1(self):
        assert _dimensions_for_format(FORMAT_POST, ASPECT_RATIO_1_1) == "1080x1080"

    def test_post_4_5(self):
        assert _dimensions_for_format(FORMAT_POST, ASPECT_RATIO_4_5) == "1080x1350"

    def test_carousel_1_1(self):
        assert _dimensions_for_format(FORMAT_CAROUSEL, ASPECT_RATIO_1_1) == "1080x1080"

    def test_carousel_4_5(self):
        assert _dimensions_for_format(FORMAT_CAROUSEL, ASPECT_RATIO_4_5) == "1080x1350"

    def test_story_9_16(self):
        assert _dimensions_for_format(FORMAT_STORY, ASPECT_RATIO_9_16) == "1080x1920"

    def test_unknown_falls_back(self):
        assert _dimensions_for_format("unknown", ASPECT_RATIO_1_1) == "1080x1080"


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


class TestValidationResult:
    def test_success(self):
        r = ValidationResult.success()
        assert r.ok is True
        assert r.valid is True
        assert r.issues == []

    def test_success_with_warnings(self):
        r = ValidationResult.success(["low contrast"])
        assert r.ok is True
        assert r.warnings == ["low contrast"]

    def test_failure(self):
        r = ValidationResult.failure(["no palette"])
        assert r.ok is False
        assert r.valid is False
        assert r.issues == ["no palette"]

    def test_failure_with_warnings(self):
        r = ValidationResult.failure(["no brief"], ["missing mood"])
        assert r.ok is False
        assert r.warnings == ["missing mood"]

    def test_ok_false_when_valid_but_has_issues(self):
        r = ValidationResult(valid=True, issues=["something"])
        assert r.ok is False


# ---------------------------------------------------------------------------
# DesignArtPlanner — define_brand_profile
# ---------------------------------------------------------------------------


class TestDefineBrandProfile:
    def test_define_adds_entity(self):
        planner = _setup_planner()
        profile = planner.define_brand_profile("Test", "Desc", "brand_x")
        assert profile.name == "Test"
        assert profile.id.startswith("bvprof_")
        assert planner.profile_count == 1

    def test_multiple_profiles_accumulate(self):
        planner = _setup_planner()
        planner.define_brand_profile("A", "DA", "b1")
        planner.define_brand_profile("B", "DB", "b2")
        assert planner.profile_count == 2

    def test_full_params(self):
        planner = _setup_planner()
        profile = planner.define_brand_profile(
            name="Full Brand",
            description="Complete profile",
            brand_id="brand_full",
            primary_color="#FF0000",
            secondary_color="#00FF00",
            accent_color="#0000FF",
            heading_font="Montserrat",
            body_font="Lato",
            logo_style="icon_only",
            visual_archetype=ARCHETYPE_BOLD,
            mood_keywords=["bold", "modern"],
        )
        assert profile.primary_color == "#FF0000"
        assert profile.accent_color == "#0000FF"
        assert profile.heading_font == "Montserrat"
        assert profile.visual_archetype == ARCHETYPE_BOLD


# ---------------------------------------------------------------------------
# DesignArtPlanner — define_visual_direction
# ---------------------------------------------------------------------------


class TestDefineVisualDirection:
    def test_define_adds_entity(self):
        planner = _setup_planner()
        direction = planner.define_visual_direction(
            "bvprof_abc", DIRECTION_TYPE_COLOR_PALETTE, "Dark Mode", "Dark palette"
        )
        assert direction.direction_name == "Dark Mode"
        assert direction.id.startswith("vdir_")
        assert planner.direction_count == 1

    def test_direction_with_palette_and_rules(self):
        planner = _setup_planner()
        direction = planner.define_visual_direction(
            "bvprof_xyz",
            DIRECTION_TYPE_COLOR_PALETTE,
            "Ocean Palette",
            "Blues and teals",
            rules=["use blue as dominant", "teal for accents"],
            palette_hex=["#0077B6", "#00B4D8", "#90E0EF"],
        )
        assert direction.palette_hex == ["#0077B6", "#00B4D8", "#90E0EF"]
        assert len(direction.rules) == 2


# ---------------------------------------------------------------------------
# DesignArtPlanner — build_design_brief
# ---------------------------------------------------------------------------


class TestBuildDesignBrief:
    def test_build_adds_entity(self):
        planner = _setup_planner()
        brief = planner.build_design_brief("Test Brief", "bvprof_abc")
        assert brief.title == "Test Brief"
        assert brief.id.startswith("dbrf_")
        assert planner.brief_count == 1

    def test_auto_resolves_dimensions(self):
        planner = _setup_planner()
        brief = planner.build_design_brief(
            "Carousel", "bvprof_abc",
            target_format=FORMAT_CAROUSEL,
            aspect_ratio=ASPECT_RATIO_4_5,
        )
        assert brief.dimensions == "1080x1350"

    def test_explicit_dimensions_override(self):
        planner = _setup_planner()
        brief = planner.build_design_brief(
            "Custom", "bvprof_abc",
            dimensions="1200x1200",
        )
        assert brief.dimensions == "1200x1200"

    def test_full_params(self):
        planner = _setup_planner()
        brief = planner.build_design_brief(
            title="Summer Campaign",
            profile_id="bvprof_x",
            direction_ids=["vdir_a"],
            objective="Sell summer packages",
            target_format=FORMAT_CAROUSEL,
            constraints=["no dark colors"],
            copy_text="Book your summer trip!",
            aspect_ratio=ASPECT_RATIO_1_1,
        )
        assert brief.objective == "Sell summer packages"
        assert brief.copy_text == "Book your summer trip!"
        assert "no dark colors" in brief.constraints


# ---------------------------------------------------------------------------
# DesignArtPlanner — generate_asset_specs
# ---------------------------------------------------------------------------


class TestGenerateAssetSpecs:
    def test_generates_assets_for_single_slide(self):
        planner = _setup_planner()
        brief = planner.build_design_brief("Test", "bvprof_abc")
        specs = planner.generate_asset_specs(brief, asset_count=1, slide_index=0)
        # 1 bg + 1 text + 1 logo = 3 per slide
        assert len(specs) == 3
        assert planner.asset_count == 3

    def test_generates_assets_for_multiple_slides(self):
        planner = _setup_planner()
        brief = planner.build_design_brief("Multi", "bvprof_abc")
        specs = planner.generate_asset_specs(brief, asset_count=3, slide_index=0)
        assert len(specs) == 9
        assert planner.asset_count == 9

    def test_first_asset_is_background(self):
        planner = _setup_planner()
        brief = planner.build_design_brief("Test", "bvprof_abc")
        specs = planner.generate_asset_specs(brief, asset_count=1)
        assert specs[0].asset_type == ASSET_TYPE_IMAGE
        assert specs[0].layer_order == 0

    def test_second_asset_is_text_overlay(self):
        planner = _setup_planner()
        brief = planner.build_design_brief("Test", "bvprof_abc")
        specs = planner.generate_asset_specs(brief, asset_count=1)
        assert specs[1].asset_type == ASSET_TYPE_TEXT_OVERLAY
        assert specs[1].layer_order == 1

    def test_third_asset_is_logo(self):
        planner = _setup_planner()
        brief = planner.build_design_brief("Test", "bvprof_abc")
        specs = planner.generate_asset_specs(brief, asset_count=1)
        assert specs[2].asset_type == ASSET_TYPE_LOGO
        assert specs[2].layer_order == 2

    def test_all_assets_link_to_brief(self):
        planner = _setup_planner()
        brief = planner.build_design_brief("Test", "bvprof_abc")
        specs = planner.generate_asset_specs(brief, asset_count=2)
        for s in specs:
            assert s.brief_id == brief.id

    def test_slide_naming_with_offset(self):
        planner = _setup_planner()
        brief = planner.build_design_brief("Test", "bvprof_abc")
        specs = planner.generate_asset_specs(brief, asset_count=1, slide_index=2)
        assert specs[0].asset_name == "slide_3_bg"


# ---------------------------------------------------------------------------
# DesignArtPlanner — build_carousel_layout
# ---------------------------------------------------------------------------


class TestBuildCarouselLayout:
    def test_build_adds_entity(self):
        planner = _setup_planner()
        layout = planner.build_carousel_layout("dbrf_abc", slide_count=5)
        assert layout.slide_count == 5
        assert layout.id.startswith("clyt_")
        assert planner.carousel_count == 1

    def test_full_params(self):
        planner = _setup_planner()
        layout = planner.build_carousel_layout(
            "dbrf_abc",
            slide_count=4,
            slide_order=["a", "b", "c", "d"],
            transition=TRANSITION_FADE,
            aspect_ratio=ASPECT_RATIO_4_5,
            cover_slide_id="a",
        )
        assert layout.transition == TRANSITION_FADE
        assert layout.aspect_ratio == ASPECT_RATIO_4_5
        assert layout.cover_slide_id == "a"
        assert layout.slide_order == ["a", "b", "c", "d"]


# ---------------------------------------------------------------------------
# DesignArtPlanner — review_design
# ---------------------------------------------------------------------------


class TestReviewDesign:
    def test_review_adds_entity(self):
        planner = _setup_planner()
        review = planner.review_design("dbrf_abc", score=75)
        assert review.score == 75
        assert review.id.startswith("crvw_")
        assert planner.review_count == 1

    def test_approved_review(self):
        planner = _setup_planner()
        review = planner.review_design(
            "dbrf_abc",
            score=90,
            status=REVIEW_STATUS_APPROVED,
            reviewer_notes=["Excellent!"],
            suggestions=["Minor: increase contrast"],
        )
        assert review.status == REVIEW_STATUS_APPROVED
        assert review.is_approved is True

    def test_rejected_review(self):
        planner = _setup_planner()
        review = planner.review_design(
            "dbrf_abc",
            score=30,
            status=REVIEW_STATUS_REJECTED,
            issues=["Off-brand colors", "Illegible font"],
        )
        assert review.status == REVIEW_STATUS_REJECTED
        assert review.has_issues is True
        assert len(review.issues) == 2


# ---------------------------------------------------------------------------
# DesignArtPlanner — validate_visual_direction
# ---------------------------------------------------------------------------


class TestValidateVisualDirection:
    def test_valid_profile_and_directions(self):
        planner = _setup_planner()
        profile = planner.define_brand_profile(
            "Valid Brand", "Test", "brand_xyz",
            mood_keywords=["modern"],
        )
        d1 = planner.define_visual_direction(
            profile.id, DIRECTION_TYPE_COLOR_PALETTE, "Palette", "Colors",
            palette_hex=["#000", "#FFF"],
        )
        d2 = planner.define_visual_direction(
            profile.id, DIRECTION_TYPE_TYPOGRAPHY, "Fonts", "Font rules",
            rules=["use sans-serif"],
        )
        result = planner.validate_visual_direction(profile, [d1, d2])
        assert result.ok is True

    def test_empty_profile_name(self):
        planner = _setup_planner()
        profile = planner.define_brand_profile("", "", "")
        result = planner.validate_visual_direction(profile, [])
        assert result.ok is False

    def test_no_mood_keywords_warns(self):
        planner = _setup_planner()
        profile = planner.define_brand_profile("Brand", "Desc", "b_x")
        d = planner.define_visual_direction(
            profile.id, DIRECTION_TYPE_COLOR_PALETTE, "P", "D",
            palette_hex=["#000"],
        )
        result = planner.validate_visual_direction(profile, [d])
        assert result.ok is True
        assert any("mood keywords" in w for w in result.warnings)

    def test_missing_color_palette_warns(self):
        planner = _setup_planner()
        profile = planner.define_brand_profile("Brand", "Test", "b1", mood_keywords=["modern"])
        d = planner.define_visual_direction(
            profile.id, DIRECTION_TYPE_TYPOGRAPHY, "Fonts", "F", rules=["sans"]
        )
        result = planner.validate_visual_direction(profile, [d])
        assert any("color palette" in w.lower() for w in result.warnings)

    def test_missing_typography_warns(self):
        planner = _setup_planner()
        profile = planner.define_brand_profile("Brand", "Test", "b1", mood_keywords=["modern"])
        d = planner.define_visual_direction(
            profile.id, DIRECTION_TYPE_COLOR_PALETTE, "Colors", "C", palette_hex=["#000"]
        )
        result = planner.validate_visual_direction(profile, [d])
        assert any("typography" in w.lower() for w in result.warnings)

    def test_direction_no_rules_warns(self):
        planner = _setup_planner()
        profile = planner.define_brand_profile("Brand", "Test", "b1", mood_keywords=["modern"])
        d = planner.define_visual_direction(
            profile.id, DIRECTION_TYPE_COLOR_PALETTE, "P", "D", palette_hex=["#000"]
        )
        result = planner.validate_visual_direction(profile, [d])
        assert any("no rules" in w.lower() for w in result.warnings)

    def test_color_palette_no_hex_warns(self):
        planner = _setup_planner()
        profile = planner.define_brand_profile("Brand", "Test", "b1", mood_keywords=["modern"])
        d = planner.define_visual_direction(
            profile.id, DIRECTION_TYPE_COLOR_PALETTE, "P", "D"
        )
        result = planner.validate_visual_direction(profile, [d])
        assert any("no hex colors" in w.lower() for w in result.warnings)

    def test_with_brief_validation(self):
        planner = _setup_planner()
        profile = planner.define_brand_profile("Brand", "Test", "b1", mood_keywords=["modern"])
        d = planner.define_visual_direction(
            profile.id, DIRECTION_TYPE_COLOR_PALETTE, "P", "D", palette_hex=["#000"]
        )
        brief = planner.build_design_brief("Valid Brief", profile.id, direction_ids=[d.id])
        result = planner.validate_visual_direction(profile, [d], brief)
        assert result.ok is True

    def test_brief_no_direction_ids_warns(self):
        planner = _setup_planner()
        profile = planner.define_brand_profile("Brand", "Test", "b1", mood_keywords=["modern"])
        d = planner.define_visual_direction(
            profile.id, DIRECTION_TYPE_COLOR_PALETTE, "P", "D", palette_hex=["#000"]
        )
        brief = planner.build_design_brief("Brief", profile.id)
        result = planner.validate_visual_direction(profile, [d], brief)
        assert any("direction_ids" in w.lower() for w in result.warnings)

    def test_empty_direction_name_is_issue(self):
        planner = _setup_planner()
        profile = planner.define_brand_profile("Brand", "Test", "b1", mood_keywords=["modern"])
        d = planner.define_visual_direction(
            profile.id, DIRECTION_TYPE_COLOR_PALETTE, "", "Desc"
        )
        result = planner.validate_visual_direction(profile, [d])
        assert result.ok is False
        assert any("empty name" in issue for issue in result.issues)


# ---------------------------------------------------------------------------
# DesignArtPlanner — lookup helpers
# ---------------------------------------------------------------------------


class TestLookupHelpers:
    def test_get_profile_found(self):
        planner = _setup_planner()
        p = planner.define_brand_profile("P", "D", "b1")
        assert planner.get_profile(p.id) is p

    def test_get_profile_not_found(self):
        planner = _setup_planner()
        assert planner.get_profile("nonexistent") is None

    def test_get_directions_filters_by_ids(self):
        planner = _setup_planner()
        d1 = planner.define_visual_direction("p1", DIRECTION_TYPE_COLOR_PALETTE, "A", "D")
        d2 = planner.define_visual_direction("p1", DIRECTION_TYPE_TYPOGRAPHY, "B", "D")
        result = planner.get_directions([d1.id])
        assert len(result) == 1
        assert result[0].id == d1.id

    def test_get_directions_empty(self):
        planner = _setup_planner()
        assert planner.get_directions(["none"]) == []

    def test_get_assets_by_brief(self):
        planner = _setup_planner()
        brief = planner.build_design_brief("T", "p1")
        planner.generate_asset_specs(brief, asset_count=1)
        result = planner.get_assets(brief.id)
        assert len(result) == 3

    def test_get_carousel_found(self):
        planner = _setup_planner()
        layout = planner.build_carousel_layout("dbrf_x", 3)
        assert planner.get_carousel("dbrf_x") is layout

    def test_get_carousel_not_found(self):
        planner = _setup_planner()
        assert planner.get_carousel("none") is None

    def test_get_review_found(self):
        planner = _setup_planner()
        review = planner.review_design("dbrf_x", score=80)
        assert planner.get_review("dbrf_x") is review

    def test_get_review_not_found(self):
        planner = _setup_planner()
        assert planner.get_review("none") is None


# ---------------------------------------------------------------------------
# DesignArtPlanner — dry_run flag & properties
# ---------------------------------------------------------------------------


class TestDryRunAndProperties:
    def test_default_dry_run(self):
        planner = DesignArtPlanner()
        assert planner.dry_run is True

    def test_explicit_dry_run_true(self):
        planner = DesignArtPlanner(dry_run=True)
        assert planner.define_brand_profile("X", "Y", "z") is not None

    def test_non_dry_run_also_works(self):
        planner = DesignArtPlanner(dry_run=False)
        assert planner.define_brand_profile("X", "Y", "z") is not None

    def test_total_entities(self):
        planner = _setup_planner()
        planner.define_brand_profile("A", "D", "b1")
        planner.define_visual_direction("p", DIRECTION_TYPE_COLOR_PALETTE, "C", "D")
        planner.build_design_brief("B", "p")
        assert planner.total_entities == 3
