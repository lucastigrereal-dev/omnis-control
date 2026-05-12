"""P5 Marketing Supreme Skeleton — deterministic campaign planning.

Zero LLM. Zero network. Zero database. Dry-run by default.
"""

from src.marketing.models import (
    # Objective types
    OBJECTIVE_TYPE_AWARENESS,
    OBJECTIVE_TYPE_ENGAGEMENT,
    OBJECTIVE_TYPE_CONVERSION,
    OBJECTIVE_TYPE_RETENTION,
    VALID_OBJECTIVE_TYPES,
    # Priorities
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_HIGH,
    PRIORITY_CRITICAL,
    VALID_PRIORITIES,
    # Pillar types
    PILLAR_TYPE_EDUCATIONAL,
    PILLAR_TYPE_ENTERTAINING,
    PILLAR_TYPE_INSPIRATIONAL,
    PILLAR_TYPE_PROMOTIONAL,
    VALID_PILLAR_TYPES,
    # Content formats
    CONTENT_FORMAT_CAROUSEL,
    CONTENT_FORMAT_REEL,
    CONTENT_FORMAT_MULTI_COPY,
    CONTENT_FORMAT_STORY,
    CONTENT_FORMAT_POST,
    VALID_CONTENT_FORMATS,
    # Platforms
    PLATFORM_INSTAGRAM,
    PLATFORM_FACEBOOK,
    PLATFORM_TIKTOK,
    PLATFORM_YOUTUBE,
    VALID_PLATFORMS,
    # Frequencies
    FREQUENCY_DAILY,
    FREQUENCY_WEEKLY,
    FREQUENCY_BIWEEKLY,
    FREQUENCY_MONTHLY,
    VALID_FREQUENCIES,
    # Tones
    TONE_PROFESSIONAL,
    TONE_CASUAL,
    TONE_HUMOROUS,
    TONE_INSPIRATIONAL,
    TONE_URGENT,
    VALID_TONES,
    # CTAs
    CTA_LINK_BIO,
    CTA_DM,
    CTA_COMMENT,
    CTA_SHARE,
    CTA_SAVE,
    CTA_VISIT,
    CTA_BOOK,
    VALID_CTAS,
    # Models
    MarketingObjective,
    AudienceProfile,
    ContentPillar,
    ContentItem,
    CampaignBrief,
    ContentPlan,
    CampaignPackage,
)
from src.marketing.service import (
    MarketingPlanner,
    ValidationResult,
)
from src.marketing.exporters import (
    export_campaign_package_markdown,
    export_content_calendar_csv,
    export_content_calendar_json,
)
from src.marketing.errors import (
    MarketingError,
    InvalidObjectiveError,
    InvalidAudienceError,
    InvalidPillarError,
    InvalidCampaignError,
    ContentPlanError,
    ValidationError,
    ExportError,
)

__all__ = [
    # Constants — objective types
    "OBJECTIVE_TYPE_AWARENESS",
    "OBJECTIVE_TYPE_ENGAGEMENT",
    "OBJECTIVE_TYPE_CONVERSION",
    "OBJECTIVE_TYPE_RETENTION",
    "VALID_OBJECTIVE_TYPES",
    # Constants — priorities
    "PRIORITY_LOW",
    "PRIORITY_MEDIUM",
    "PRIORITY_HIGH",
    "PRIORITY_CRITICAL",
    "VALID_PRIORITIES",
    # Constants — pillar types
    "PILLAR_TYPE_EDUCATIONAL",
    "PILLAR_TYPE_ENTERTAINING",
    "PILLAR_TYPE_INSPIRATIONAL",
    "PILLAR_TYPE_PROMOTIONAL",
    "VALID_PILLAR_TYPES",
    # Constants — content formats
    "CONTENT_FORMAT_CAROUSEL",
    "CONTENT_FORMAT_REEL",
    "CONTENT_FORMAT_MULTI_COPY",
    "CONTENT_FORMAT_STORY",
    "CONTENT_FORMAT_POST",
    "VALID_CONTENT_FORMATS",
    # Constants — platforms
    "PLATFORM_INSTAGRAM",
    "PLATFORM_FACEBOOK",
    "PLATFORM_TIKTOK",
    "PLATFORM_YOUTUBE",
    "VALID_PLATFORMS",
    # Constants — frequencies
    "FREQUENCY_DAILY",
    "FREQUENCY_WEEKLY",
    "FREQUENCY_BIWEEKLY",
    "FREQUENCY_MONTHLY",
    "VALID_FREQUENCIES",
    # Constants — tones
    "TONE_PROFESSIONAL",
    "TONE_CASUAL",
    "TONE_HUMOROUS",
    "TONE_INSPIRATIONAL",
    "TONE_URGENT",
    "VALID_TONES",
    # Constants — CTAs
    "CTA_LINK_BIO",
    "CTA_DM",
    "CTA_COMMENT",
    "CTA_SHARE",
    "CTA_SAVE",
    "CTA_VISIT",
    "CTA_BOOK",
    "VALID_CTAS",
    # Models
    "MarketingObjective",
    "AudienceProfile",
    "ContentPillar",
    "ContentItem",
    "CampaignBrief",
    "ContentPlan",
    "CampaignPackage",
    # Service
    "MarketingPlanner",
    "ValidationResult",
    # Exporters
    "export_campaign_package_markdown",
    "export_content_calendar_csv",
    "export_content_calendar_json",
    # Errors
    "MarketingError",
    "InvalidObjectiveError",
    "InvalidAudienceError",
    "InvalidPillarError",
    "InvalidCampaignError",
    "ContentPlanError",
    "ValidationError",
    "ExportError",
]
