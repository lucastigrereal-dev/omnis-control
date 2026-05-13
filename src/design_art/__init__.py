"""P6 Design Art Engine Skeleton — deterministic design briefs and asset specs.

Zero LLM. Zero network. Zero database. Zero image generation. Dry-run by default.
"""

from src.design_art.models import (
    # Direction types
    DIRECTION_TYPE_MOODBOARD,
    DIRECTION_TYPE_COLOR_PALETTE,
    DIRECTION_TYPE_TYPOGRAPHY,
    DIRECTION_TYPE_COMPOSITION,
    DIRECTION_TYPE_ICONOGRAPHY,
    DIRECTION_TYPE_PHOTOGRAPHY,
    VALID_DIRECTION_TYPES,
    # Visual archetypes
    ARCHETYPE_MINIMALIST,
    ARCHETYPE_BOLD,
    ARCHETYPE_ELEGANT,
    ARCHETYPE_PLAYFUL,
    ARCHETYPE_RUSTIC,
    ARCHETYPE_EDITORIAL,
    ARCHETYPE_CORPORATE,
    VALID_ARCHETYPES,
    # Design formats
    FORMAT_CAROUSEL,
    FORMAT_REEL,
    FORMAT_STORY,
    FORMAT_POST,
    FORMAT_BANNER,
    FORMAT_THUMBNAIL,
    VALID_DESIGN_FORMATS,
    # Asset types
    ASSET_TYPE_IMAGE,
    ASSET_TYPE_VIDEO,
    ASSET_TYPE_TEXT_OVERLAY,
    ASSET_TYPE_LOGO,
    ASSET_TYPE_BACKGROUND,
    ASSET_TYPE_ICON,
    ASSET_TYPE_CAPTION_BAR,
    VALID_ASSET_TYPES,
    # Color modes
    COLOR_MODE_RGB,
    COLOR_MODE_CMYK,
    VALID_COLOR_MODES,
    # File formats
    FILE_FORMAT_PNG,
    FILE_FORMAT_JPG,
    FILE_FORMAT_SVG,
    FILE_FORMAT_MP4,
    FILE_FORMAT_WEBP,
    VALID_FILE_FORMATS,
    # Review statuses
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_REJECTED,
    REVIEW_STATUS_NEEDS_REVISION,
    VALID_REVIEW_STATUSES,
    # Aspect ratios
    ASPECT_RATIO_1_1,
    ASPECT_RATIO_4_5,
    ASPECT_RATIO_16_9,
    ASPECT_RATIO_9_16,
    VALID_ASPECT_RATIOS,
    # Transitions
    TRANSITION_SWIPE,
    TRANSITION_FADE,
    TRANSITION_DISSOLVE,
    TRANSITION_NONE,
    VALID_TRANSITIONS,
    # Models
    BrandVisualProfile,
    VisualDirection,
    DesignBrief,
    AssetSpec,
    CarouselLayoutSpec,
    CreativeReview,
)
from src.design_art.service import (
    DesignArtPlanner,
    ValidationResult,
)
from src.design_art.exporters import (
    export_profile_markdown,
    export_direction_markdown,
    export_design_brief_markdown,
)
from src.design_art.errors import (
    DesignArtError,
    InvalidProfileError,
    InvalidDirectionError,
    InvalidBriefError,
    InvalidAssetSpecError,
    InvalidCarouselLayoutError,
    InvalidReviewError,
    ValidationError,
    ExportError,
)

__all__ = [
    # Constants — direction types
    "DIRECTION_TYPE_MOODBOARD",
    "DIRECTION_TYPE_COLOR_PALETTE",
    "DIRECTION_TYPE_TYPOGRAPHY",
    "DIRECTION_TYPE_COMPOSITION",
    "DIRECTION_TYPE_ICONOGRAPHY",
    "DIRECTION_TYPE_PHOTOGRAPHY",
    "VALID_DIRECTION_TYPES",
    # Constants — visual archetypes
    "ARCHETYPE_MINIMALIST",
    "ARCHETYPE_BOLD",
    "ARCHETYPE_ELEGANT",
    "ARCHETYPE_PLAYFUL",
    "ARCHETYPE_RUSTIC",
    "ARCHETYPE_EDITORIAL",
    "ARCHETYPE_CORPORATE",
    "VALID_ARCHETYPES",
    # Constants — design formats
    "FORMAT_CAROUSEL",
    "FORMAT_REEL",
    "FORMAT_STORY",
    "FORMAT_POST",
    "FORMAT_BANNER",
    "FORMAT_THUMBNAIL",
    "VALID_DESIGN_FORMATS",
    # Constants — asset types
    "ASSET_TYPE_IMAGE",
    "ASSET_TYPE_VIDEO",
    "ASSET_TYPE_TEXT_OVERLAY",
    "ASSET_TYPE_LOGO",
    "ASSET_TYPE_BACKGROUND",
    "ASSET_TYPE_ICON",
    "ASSET_TYPE_CAPTION_BAR",
    "VALID_ASSET_TYPES",
    # Constants — color modes
    "COLOR_MODE_RGB",
    "COLOR_MODE_CMYK",
    "VALID_COLOR_MODES",
    # Constants — file formats
    "FILE_FORMAT_PNG",
    "FILE_FORMAT_JPG",
    "FILE_FORMAT_SVG",
    "FILE_FORMAT_MP4",
    "FILE_FORMAT_WEBP",
    "VALID_FILE_FORMATS",
    # Constants — review statuses
    "REVIEW_STATUS_APPROVED",
    "REVIEW_STATUS_REJECTED",
    "REVIEW_STATUS_NEEDS_REVISION",
    "VALID_REVIEW_STATUSES",
    # Constants — aspect ratios
    "ASPECT_RATIO_1_1",
    "ASPECT_RATIO_4_5",
    "ASPECT_RATIO_16_9",
    "ASPECT_RATIO_9_16",
    "VALID_ASPECT_RATIOS",
    # Constants — transitions
    "TRANSITION_SWIPE",
    "TRANSITION_FADE",
    "TRANSITION_DISSOLVE",
    "TRANSITION_NONE",
    "VALID_TRANSITIONS",
    # Models
    "BrandVisualProfile",
    "VisualDirection",
    "DesignBrief",
    "AssetSpec",
    "CarouselLayoutSpec",
    "CreativeReview",
    # Service
    "DesignArtPlanner",
    "ValidationResult",
    # Exporters
    "export_profile_markdown",
    "export_direction_markdown",
    "export_design_brief_markdown",
    # Errors
    "DesignArtError",
    "InvalidProfileError",
    "InvalidDirectionError",
    "InvalidBriefError",
    "InvalidAssetSpecError",
    "InvalidCarouselLayoutError",
    "InvalidReviewError",
    "ValidationError",
    "ExportError",
]
