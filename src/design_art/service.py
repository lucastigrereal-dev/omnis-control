"""P6 Design Art Engine — deterministic Design Art Planner service.

All operations are dry-run by default. Zero LLM. Zero network. Zero database.
Zero image generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.design_art.models import (
    _now_iso,
    _new_id,
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
    FORMAT_POST,
    FORMAT_CAROUSEL,
    FORMAT_STORY,
    ASSET_TYPE_IMAGE,
    ASSET_TYPE_TEXT_OVERLAY,
    ASSET_TYPE_LOGO,
    ASSET_TYPE_BACKGROUND,
    ASSET_TYPE_ICON,
    COLOR_MODE_RGB,
    FILE_FORMAT_PNG,
    FILE_FORMAT_JPG,
    ASPECT_RATIO_1_1,
    ASPECT_RATIO_4_5,
    ASPECT_RATIO_9_16,
    TRANSITION_SWIPE,
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_NEEDS_REVISION,
    REVIEW_STATUS_REJECTED,
    VALID_DESIGN_FORMATS,
    VALID_ASSET_TYPES,
    VALID_ARCHETYPES,
    VALID_DIRECTION_TYPES,
    VALID_ASPECT_RATIOS,
    VALID_TRANSITIONS,
    VALID_REVIEW_STATUSES,
    VALID_COLOR_MODES,
    VALID_FILE_FORMATS,
)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Outcome of design/visual validation."""
    valid: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.valid and len(self.issues) == 0

    @classmethod
    def success(cls, warnings: Optional[list[str]] = None) -> "ValidationResult":
        return cls(valid=True, warnings=warnings or [])

    @classmethod
    def failure(cls, issues: list[str], warnings: Optional[list[str]] = None) -> "ValidationResult":
        return cls(valid=False, issues=issues, warnings=warnings or [])


# ---------------------------------------------------------------------------
# Default layout helper
# ---------------------------------------------------------------------------

def _dimensions_for_format(target_format: str, aspect_ratio: str) -> str:
    """Return default pixel dimensions for a format + aspect ratio."""
    mapping = {
        (FORMAT_POST, ASPECT_RATIO_1_1): "1080x1080",
        (FORMAT_POST, ASPECT_RATIO_4_5): "1080x1350",
        (FORMAT_CAROUSEL, ASPECT_RATIO_1_1): "1080x1080",
        (FORMAT_CAROUSEL, ASPECT_RATIO_4_5): "1080x1350",
        (FORMAT_STORY, ASPECT_RATIO_9_16): "1080x1920",
    }
    return mapping.get((target_format, aspect_ratio), "1080x1080")


# ---------------------------------------------------------------------------
# Design Art Planner
# ---------------------------------------------------------------------------


class DesignArtPlanner:
    """Deterministic design art planner — dry-run by default.

    Models visual profiles, directions, design briefs, asset specs,
    carousel layouts, and creative reviews without generating any
    actual images or calling external APIs.
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._profiles: list[BrandVisualProfile] = []
        self._directions: list[VisualDirection] = []
        self._briefs: list[DesignBrief] = []
        self._assets: list[AssetSpec] = []
        self._carousels: list[CarouselLayoutSpec] = []
        self._reviews: list[CreativeReview] = []

    # -- Define brand visual profile ---------------------------------------

    def define_brand_profile(
        self,
        name: str,
        description: str,
        brand_id: str,
        primary_color: str = "#000000",
        secondary_color: str = "#FFFFFF",
        accent_color: str = "#FF0000",
        heading_font: str = "Inter",
        body_font: str = "Inter",
        logo_style: str = "wordmark",
        visual_archetype: str = ARCHETYPE_MINIMALIST,
        mood_keywords: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> BrandVisualProfile:
        profile = BrandVisualProfile.new(
            name=name,
            description=description,
            brand_id=brand_id,
            primary_color=primary_color,
            secondary_color=secondary_color,
            accent_color=accent_color,
            heading_font=heading_font,
            body_font=body_font,
            logo_style=logo_style,
            visual_archetype=visual_archetype,
            mood_keywords=mood_keywords,
            notes=notes,
        )
        self._profiles.append(profile)
        return profile

    # -- Define visual direction --------------------------------------------

    def define_visual_direction(
        self,
        profile_id: str,
        direction_type: str,
        direction_name: str,
        description: str,
        rules: Optional[list[str]] = None,
        references: Optional[list[str]] = None,
        palette_hex: Optional[list[str]] = None,
        example_descriptor: str = "",
        notes: Optional[str] = None,
    ) -> VisualDirection:
        direction = VisualDirection.new(
            profile_id=profile_id,
            direction_type=direction_type,
            direction_name=direction_name,
            description=description,
            rules=rules,
            references=references,
            palette_hex=palette_hex,
            example_descriptor=example_descriptor,
            notes=notes,
        )
        self._directions.append(direction)
        return direction

    # -- Build design brief -------------------------------------------------

    def build_design_brief(
        self,
        title: str,
        profile_id: str,
        direction_ids: Optional[list[str]] = None,
        objective: str = "",
        target_format: str = FORMAT_POST,
        dimensions: str = "",
        constraints: Optional[list[str]] = None,
        copy_text: Optional[str] = None,
        notes: Optional[str] = None,
        aspect_ratio: str = ASPECT_RATIO_1_1,
    ) -> DesignBrief:
        resolved_dim = dimensions or _dimensions_for_format(target_format, aspect_ratio)
        brief = DesignBrief.new(
            title=title,
            profile_id=profile_id,
            direction_ids=direction_ids,
            objective=objective,
            target_format=target_format,
            dimensions=resolved_dim,
            constraints=constraints,
            copy_text=copy_text,
            notes=notes,
        )
        self._briefs.append(brief)
        return brief

    # -- Generate asset specs -----------------------------------------------

    def generate_asset_specs(
        self,
        brief: DesignBrief,
        asset_count: int = 1,
        slide_index: int = 0,
    ) -> list[AssetSpec]:
        """Generate deterministic placeholder asset specs for a design brief.

        Produces a background image + optional text overlay + optional logo.
        No actual images are generated — only specification dataclasses.
        """
        specs: list[AssetSpec] = []
        for i in range(asset_count):
            spec = AssetSpec.new(
                brief_id=brief.id,
                asset_type=ASSET_TYPE_IMAGE,
                asset_name=f"slide_{slide_index + i + 1}_bg",
                description=f"Background layer for slide {slide_index + i + 1}",
                width=1080,
                height=1080,
                layer_order=0,
                placeholder_color="#F5F5F5",
            )
            specs.append(spec)
            self._assets.append(spec)

            # Always add a text overlay layer
            text_spec = AssetSpec.new(
                brief_id=brief.id,
                asset_type=ASSET_TYPE_TEXT_OVERLAY,
                asset_name=f"slide_{slide_index + i + 1}_text",
                description=f"Text overlay for slide {slide_index + i + 1}",
                layer_order=1,
                file_format=FILE_FORMAT_PNG,
                placeholder_color="#000000",
            )
            specs.append(text_spec)
            self._assets.append(text_spec)

            # Add logo for brand awareness designs
            logo_spec = AssetSpec.new(
                brief_id=brief.id,
                asset_type=ASSET_TYPE_LOGO,
                asset_name=f"slide_{slide_index + i + 1}_logo",
                description=f"Brand logo watermark for slide {slide_index + i + 1}",
                width=200,
                height=80,
                layer_order=2,
                file_format=FILE_FORMAT_PNG,
                placeholder_color="#999999",
            )
            specs.append(logo_spec)
            self._assets.append(logo_spec)

        return specs

    # -- Build carousel layout ----------------------------------------------

    def build_carousel_layout(
        self,
        brief_id: str,
        slide_count: int,
        slide_order: Optional[list[str]] = None,
        transition: str = TRANSITION_SWIPE,
        aspect_ratio: str = ASPECT_RATIO_1_1,
        cover_slide_id: str = "",
        notes: Optional[str] = None,
    ) -> CarouselLayoutSpec:
        layout = CarouselLayoutSpec.new(
            brief_id=brief_id,
            slide_count=slide_count,
            slide_order=slide_order,
            transition=transition,
            aspect_ratio=aspect_ratio,
            cover_slide_id=cover_slide_id,
            notes=notes,
        )
        self._carousels.append(layout)
        return layout

    # -- Review design -------------------------------------------------------

    def review_design(
        self,
        brief_id: str,
        score: int = 0,
        status: str = REVIEW_STATUS_NEEDS_REVISION,
        reviewer_notes: Optional[list[str]] = None,
        issues: Optional[list[str]] = None,
        suggestions: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> CreativeReview:
        review = CreativeReview.new(
            brief_id=brief_id,
            score=score,
            status=status,
            reviewer_notes=reviewer_notes,
            issues=issues,
            suggestions=suggestions,
            notes=notes,
        )
        self._reviews.append(review)
        return review

    # -- Validate visual direction ------------------------------------------

    def validate_visual_direction(
        self,
        profile: BrandVisualProfile,
        directions: list[VisualDirection],
        brief: Optional[DesignBrief] = None,
    ) -> ValidationResult:
        """Validate that visual directions are consistent with the brand profile."""
        issues: list[str] = []
        warnings: list[str] = []

        if not profile.name.strip():
            issues.append("Brand profile name is empty")
        if not profile.brand_id.strip():
            issues.append("Brand profile has no brand_id")
        if not profile.mood_keywords:
            warnings.append("Brand profile has no mood keywords")

        direction_types = {d.direction_type for d in directions}
        if DIRECTION_TYPE_COLOR_PALETTE not in direction_types:
            warnings.append("No color palette direction defined")
        if DIRECTION_TYPE_TYPOGRAPHY not in direction_types:
            warnings.append("No typography direction defined")

        for d in directions:
            if not d.direction_name.strip():
                issues.append(f"Direction {d.id} has empty name")
            if not d.rules:
                warnings.append(f"Direction '{d.direction_name}' has no rules defined")
            if d.direction_type == DIRECTION_TYPE_COLOR_PALETTE and not d.palette_hex:
                warnings.append(f"Color palette direction '{d.direction_name}' has no hex colors")

        if brief is not None:
            if not brief.title.strip():
                issues.append("Design brief title is empty")
            if not brief.direction_ids:
                warnings.append("Design brief has no direction_ids linked")
            if brief.target_format not in VALID_DESIGN_FORMATS:
                issues.append(f"Unknown target_format {brief.target_format!r}")

        if issues:
            return ValidationResult.failure(issues, warnings)
        return ValidationResult.success(warnings)

    # -- Export helpers -----------------------------------------------------

    def get_profile(self, profile_id: str) -> Optional[BrandVisualProfile]:
        for p in self._profiles:
            if p.id == profile_id:
                return p
        return None

    def get_directions(self, direction_ids: list[str]) -> list[VisualDirection]:
        return [d for d in self._directions if d.id in direction_ids]

    def get_assets(self, brief_id: str) -> list[AssetSpec]:
        return [a for a in self._assets if a.brief_id == brief_id]

    def get_carousel(self, brief_id: str) -> Optional[CarouselLayoutSpec]:
        for c in self._carousels:
            if c.brief_id == brief_id:
                return c
        return None

    def get_review(self, brief_id: str) -> Optional[CreativeReview]:
        for r in self._reviews:
            if r.brief_id == brief_id:
                return r
        return None

    # -- Properties ---------------------------------------------------------

    @property
    def profile_count(self) -> int:
        return len(self._profiles)

    @property
    def direction_count(self) -> int:
        return len(self._directions)

    @property
    def brief_count(self) -> int:
        return len(self._briefs)

    @property
    def asset_count(self) -> int:
        return len(self._assets)

    @property
    def carousel_count(self) -> int:
        return len(self._carousels)

    @property
    def review_count(self) -> int:
        return len(self._reviews)

    @property
    def total_entities(self) -> int:
        return (
            self.profile_count
            + self.direction_count
            + self.brief_count
            + self.asset_count
            + self.carousel_count
            + self.review_count
        )
