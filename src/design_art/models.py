"""P6 Design Art Engine — deterministic dataclass models.

Zero LLM. Zero network. Zero database. Zero image generation. Stdlib only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Direction type constants
# ---------------------------------------------------------------------------

DIRECTION_TYPE_MOODBOARD = "moodboard"
DIRECTION_TYPE_COLOR_PALETTE = "color_palette"
DIRECTION_TYPE_TYPOGRAPHY = "typography"
DIRECTION_TYPE_COMPOSITION = "composition"
DIRECTION_TYPE_ICONOGRAPHY = "iconography"
DIRECTION_TYPE_PHOTOGRAPHY = "photography"

VALID_DIRECTION_TYPES = frozenset({
    DIRECTION_TYPE_MOODBOARD,
    DIRECTION_TYPE_COLOR_PALETTE,
    DIRECTION_TYPE_TYPOGRAPHY,
    DIRECTION_TYPE_COMPOSITION,
    DIRECTION_TYPE_ICONOGRAPHY,
    DIRECTION_TYPE_PHOTOGRAPHY,
})

# ---------------------------------------------------------------------------
# Visual archetype constants
# ---------------------------------------------------------------------------

ARCHETYPE_MINIMALIST = "minimalist"
ARCHETYPE_BOLD = "bold"
ARCHETYPE_ELEGANT = "elegant"
ARCHETYPE_PLAYFUL = "playful"
ARCHETYPE_RUSTIC = "rustic"
ARCHETYPE_EDITORIAL = "editorial"
ARCHETYPE_CORPORATE = "corporate"

VALID_ARCHETYPES = frozenset({
    ARCHETYPE_MINIMALIST,
    ARCHETYPE_BOLD,
    ARCHETYPE_ELEGANT,
    ARCHETYPE_PLAYFUL,
    ARCHETYPE_RUSTIC,
    ARCHETYPE_EDITORIAL,
    ARCHETYPE_CORPORATE,
})

# ---------------------------------------------------------------------------
# Design format constants
# ---------------------------------------------------------------------------

FORMAT_CAROUSEL = "carousel"
FORMAT_REEL = "reel"
FORMAT_STORY = "story"
FORMAT_POST = "post"
FORMAT_BANNER = "banner"
FORMAT_THUMBNAIL = "thumbnail"

VALID_DESIGN_FORMATS = frozenset({
    FORMAT_CAROUSEL,
    FORMAT_REEL,
    FORMAT_STORY,
    FORMAT_POST,
    FORMAT_BANNER,
    FORMAT_THUMBNAIL,
})

# ---------------------------------------------------------------------------
# Asset type constants
# ---------------------------------------------------------------------------

ASSET_TYPE_IMAGE = "image"
ASSET_TYPE_VIDEO = "video"
ASSET_TYPE_TEXT_OVERLAY = "text_overlay"
ASSET_TYPE_LOGO = "logo"
ASSET_TYPE_BACKGROUND = "background"
ASSET_TYPE_ICON = "icon"
ASSET_TYPE_CAPTION_BAR = "caption_bar"

VALID_ASSET_TYPES = frozenset({
    ASSET_TYPE_IMAGE,
    ASSET_TYPE_VIDEO,
    ASSET_TYPE_TEXT_OVERLAY,
    ASSET_TYPE_LOGO,
    ASSET_TYPE_BACKGROUND,
    ASSET_TYPE_ICON,
    ASSET_TYPE_CAPTION_BAR,
})

# ---------------------------------------------------------------------------
# Color mode constants
# ---------------------------------------------------------------------------

COLOR_MODE_RGB = "rgb"
COLOR_MODE_CMYK = "cmyk"

VALID_COLOR_MODES = frozenset({
    COLOR_MODE_RGB,
    COLOR_MODE_CMYK,
})

# ---------------------------------------------------------------------------
# File format constants
# ---------------------------------------------------------------------------

FILE_FORMAT_PNG = "png"
FILE_FORMAT_JPG = "jpg"
FILE_FORMAT_SVG = "svg"
FILE_FORMAT_MP4 = "mp4"
FILE_FORMAT_WEBP = "webp"

VALID_FILE_FORMATS = frozenset({
    FILE_FORMAT_PNG,
    FILE_FORMAT_JPG,
    FILE_FORMAT_SVG,
    FILE_FORMAT_MP4,
    FILE_FORMAT_WEBP,
})

# ---------------------------------------------------------------------------
# Review status constants
# ---------------------------------------------------------------------------

REVIEW_STATUS_APPROVED = "approved"
REVIEW_STATUS_REJECTED = "rejected"
REVIEW_STATUS_NEEDS_REVISION = "needs_revision"

VALID_REVIEW_STATUSES = frozenset({
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_REJECTED,
    REVIEW_STATUS_NEEDS_REVISION,
})

# ---------------------------------------------------------------------------
# Aspect ratio constants
# ---------------------------------------------------------------------------

ASPECT_RATIO_1_1 = "1:1"
ASPECT_RATIO_4_5 = "4:5"
ASPECT_RATIO_16_9 = "16:9"
ASPECT_RATIO_9_16 = "9:16"

VALID_ASPECT_RATIOS = frozenset({
    ASPECT_RATIO_1_1,
    ASPECT_RATIO_4_5,
    ASPECT_RATIO_16_9,
    ASPECT_RATIO_9_16,
})

# ---------------------------------------------------------------------------
# Transition type constants
# ---------------------------------------------------------------------------

TRANSITION_SWIPE = "swipe"
TRANSITION_FADE = "fade"
TRANSITION_DISSOLVE = "dissolve"
TRANSITION_NONE = "none"

VALID_TRANSITIONS = frozenset({
    TRANSITION_SWIPE,
    TRANSITION_FADE,
    TRANSITION_DISSOLVE,
    TRANSITION_NONE,
})

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass
class BrandVisualProfile:
    """Core visual identity profile for a brand or Instagram page."""
    id: str
    name: str
    description: str
    brand_id: str
    primary_color: str
    secondary_color: str
    accent_color: str
    heading_font: str
    body_font: str
    logo_style: str
    visual_archetype: str
    mood_keywords: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
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
    ) -> "BrandVisualProfile":
        if visual_archetype not in VALID_ARCHETYPES:
            raise ValueError(
                f"Invalid visual_archetype {visual_archetype!r}. "
                f"Must be one of {sorted(VALID_ARCHETYPES)}"
            )
        return cls(
            id=_new_id("bvprof_"),
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
            mood_keywords=mood_keywords or [],
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "brand_id": self.brand_id,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "accent_color": self.accent_color,
            "heading_font": self.heading_font,
            "body_font": self.body_font,
            "logo_style": self.logo_style,
            "visual_archetype": self.visual_archetype,
            "mood_keywords": list(self.mood_keywords),
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BrandVisualProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class VisualDirection:
    """A specific visual direction rule set — palette, composition, typography rules."""
    id: str
    profile_id: str
    direction_type: str
    direction_name: str
    description: str
    rules: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    palette_hex: list[str] = field(default_factory=list)
    example_descriptor: str = ""
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        profile_id: str,
        direction_type: str,
        direction_name: str,
        description: str,
        rules: Optional[list[str]] = None,
        references: Optional[list[str]] = None,
        palette_hex: Optional[list[str]] = None,
        example_descriptor: str = "",
        notes: Optional[str] = None,
    ) -> "VisualDirection":
        if direction_type not in VALID_DIRECTION_TYPES:
            raise ValueError(
                f"Invalid direction_type {direction_type!r}. "
                f"Must be one of {sorted(VALID_DIRECTION_TYPES)}"
            )
        return cls(
            id=_new_id("vdir_"),
            profile_id=profile_id,
            direction_type=direction_type,
            direction_name=direction_name,
            description=description,
            rules=rules or [],
            references=references or [],
            palette_hex=palette_hex or [],
            example_descriptor=example_descriptor,
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "direction_type": self.direction_type,
            "direction_name": self.direction_name,
            "description": self.description,
            "rules": list(self.rules),
            "references": list(self.references),
            "palette_hex": list(self.palette_hex),
            "example_descriptor": self.example_descriptor,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VisualDirection":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DesignBrief:
    """Complete design briefing — profile, directions, constraints, target format."""
    id: str
    title: str
    profile_id: str
    direction_ids: list[str] = field(default_factory=list)
    objective: str = ""
    target_format: str = FORMAT_POST
    dimensions: str = "1080x1080"
    constraints: list[str] = field(default_factory=list)
    copy_text: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        title: str,
        profile_id: str,
        direction_ids: Optional[list[str]] = None,
        objective: str = "",
        target_format: str = FORMAT_POST,
        dimensions: str = "1080x1080",
        constraints: Optional[list[str]] = None,
        copy_text: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "DesignBrief":
        if target_format not in VALID_DESIGN_FORMATS:
            raise ValueError(
                f"Invalid target_format {target_format!r}. "
                f"Must be one of {sorted(VALID_DESIGN_FORMATS)}"
            )
        return cls(
            id=_new_id("dbrf_"),
            title=title,
            profile_id=profile_id,
            direction_ids=direction_ids or [],
            objective=objective,
            target_format=target_format,
            dimensions=dimensions,
            constraints=constraints or [],
            copy_text=copy_text,
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "profile_id": self.profile_id,
            "direction_ids": list(self.direction_ids),
            "objective": self.objective,
            "target_format": self.target_format,
            "dimensions": self.dimensions,
            "constraints": list(self.constraints),
            "copy_text": self.copy_text,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DesignBrief":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AssetSpec:
    """Specification for a single design asset — placeholder only, no image generation."""
    id: str
    brief_id: str
    asset_type: str
    asset_name: str
    description: str
    width: int = 1080
    height: int = 1080
    dpi: int = 72
    color_mode: str = COLOR_MODE_RGB
    file_format: str = FILE_FORMAT_PNG
    placeholder_color: str = "#CCCCCC"
    layer_order: int = 0
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        brief_id: str,
        asset_type: str,
        asset_name: str,
        description: str,
        width: int = 1080,
        height: int = 1080,
        dpi: int = 72,
        color_mode: str = COLOR_MODE_RGB,
        file_format: str = FILE_FORMAT_PNG,
        placeholder_color: str = "#CCCCCC",
        layer_order: int = 0,
        notes: Optional[str] = None,
    ) -> "AssetSpec":
        if asset_type not in VALID_ASSET_TYPES:
            raise ValueError(
                f"Invalid asset_type {asset_type!r}. "
                f"Must be one of {sorted(VALID_ASSET_TYPES)}"
            )
        if color_mode not in VALID_COLOR_MODES:
            raise ValueError(
                f"Invalid color_mode {color_mode!r}. "
                f"Must be one of {sorted(VALID_COLOR_MODES)}"
            )
        if file_format not in VALID_FILE_FORMATS:
            raise ValueError(
                f"Invalid file_format {file_format!r}. "
                f"Must be one of {sorted(VALID_FILE_FORMATS)}"
            )
        if width <= 0 or height <= 0:
            raise ValueError(
                f"Dimensions must be positive (got {width}x{height})"
            )
        if dpi <= 0:
            raise ValueError(f"DPI must be positive (got {dpi})")
        return cls(
            id=_new_id("aspec_"),
            brief_id=brief_id,
            asset_type=asset_type,
            asset_name=asset_name,
            description=description,
            width=width,
            height=height,
            dpi=dpi,
            color_mode=color_mode,
            file_format=file_format,
            placeholder_color=placeholder_color,
            layer_order=layer_order,
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "brief_id": self.brief_id,
            "asset_type": self.asset_type,
            "asset_name": self.asset_name,
            "description": self.description,
            "width": self.width,
            "height": self.height,
            "dpi": self.dpi,
            "color_mode": self.color_mode,
            "file_format": self.file_format,
            "placeholder_color": self.placeholder_color,
            "layer_order": self.layer_order,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AssetSpec":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CarouselLayoutSpec:
    """Layout specification for an Instagram carousel — slide ordering and transitions."""
    id: str
    brief_id: str
    slide_count: int
    slide_order: list[str] = field(default_factory=list)
    transition: str = TRANSITION_SWIPE
    aspect_ratio: str = ASPECT_RATIO_1_1
    cover_slide_id: str = ""
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        brief_id: str,
        slide_count: int,
        slide_order: Optional[list[str]] = None,
        transition: str = TRANSITION_SWIPE,
        aspect_ratio: str = ASPECT_RATIO_1_1,
        cover_slide_id: str = "",
        notes: Optional[str] = None,
    ) -> "CarouselLayoutSpec":
        if transition not in VALID_TRANSITIONS:
            raise ValueError(
                f"Invalid transition {transition!r}. "
                f"Must be one of {sorted(VALID_TRANSITIONS)}"
            )
        if aspect_ratio not in VALID_ASPECT_RATIOS:
            raise ValueError(
                f"Invalid aspect_ratio {aspect_ratio!r}. "
                f"Must be one of {sorted(VALID_ASPECT_RATIOS)}"
            )
        if slide_count <= 0:
            raise ValueError(f"slide_count must be positive (got {slide_count})")
        return cls(
            id=_new_id("clyt_"),
            brief_id=brief_id,
            slide_count=slide_count,
            slide_order=slide_order or [],
            transition=transition,
            aspect_ratio=aspect_ratio,
            cover_slide_id=cover_slide_id,
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "brief_id": self.brief_id,
            "slide_count": self.slide_count,
            "slide_order": list(self.slide_order),
            "transition": self.transition,
            "aspect_ratio": self.aspect_ratio,
            "cover_slide_id": self.cover_slide_id,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CarouselLayoutSpec":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CreativeReview:
    """Review evaluation for a design brief — score, status, issues, suggestions."""
    id: str
    brief_id: str
    score: int = 0
    status: str = REVIEW_STATUS_NEEDS_REVISION
    reviewer_notes: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        brief_id: str,
        score: int = 0,
        status: str = REVIEW_STATUS_NEEDS_REVISION,
        reviewer_notes: Optional[list[str]] = None,
        issues: Optional[list[str]] = None,
        suggestions: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> "CreativeReview":
        if status not in VALID_REVIEW_STATUSES:
            raise ValueError(
                f"Invalid status {status!r}. "
                f"Must be one of {sorted(VALID_REVIEW_STATUSES)}"
            )
        if score < 0 or score > 100:
            raise ValueError(
                f"Score must be between 0 and 100 (got {score})"
            )
        return cls(
            id=_new_id("crvw_"),
            brief_id=brief_id,
            score=score,
            status=status,
            reviewer_notes=reviewer_notes or [],
            issues=issues or [],
            suggestions=suggestions or [],
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "brief_id": self.brief_id,
            "score": self.score,
            "status": self.status,
            "reviewer_notes": list(self.reviewer_notes),
            "issues": list(self.issues),
            "suggestions": list(self.suggestions),
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CreativeReview":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @property
    def is_approved(self) -> bool:
        return self.status == REVIEW_STATUS_APPROVED

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0
