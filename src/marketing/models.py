"""P5 Marketing Supreme — deterministic dataclass models.

Zero LLM. Zero network. Zero database. Stdlib only.
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
# Objective type constants
# ---------------------------------------------------------------------------

OBJECTIVE_TYPE_AWARENESS = "awareness"
OBJECTIVE_TYPE_ENGAGEMENT = "engagement"
OBJECTIVE_TYPE_CONVERSION = "conversion"
OBJECTIVE_TYPE_RETENTION = "retention"

VALID_OBJECTIVE_TYPES = frozenset({
    OBJECTIVE_TYPE_AWARENESS,
    OBJECTIVE_TYPE_ENGAGEMENT,
    OBJECTIVE_TYPE_CONVERSION,
    OBJECTIVE_TYPE_RETENTION,
})

# ---------------------------------------------------------------------------
# Priority constants
# ---------------------------------------------------------------------------

PRIORITY_LOW = "low"
PRIORITY_MEDIUM = "medium"
PRIORITY_HIGH = "high"
PRIORITY_CRITICAL = "critical"

VALID_PRIORITIES = frozenset({
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_HIGH,
    PRIORITY_CRITICAL,
})

# ---------------------------------------------------------------------------
# Pillar type constants
# ---------------------------------------------------------------------------

PILLAR_TYPE_EDUCATIONAL = "educational"
PILLAR_TYPE_ENTERTAINING = "entertaining"
PILLAR_TYPE_INSPIRATIONAL = "inspirational"
PILLAR_TYPE_PROMOTIONAL = "promotional"

VALID_PILLAR_TYPES = frozenset({
    PILLAR_TYPE_EDUCATIONAL,
    PILLAR_TYPE_ENTERTAINING,
    PILLAR_TYPE_INSPIRATIONAL,
    PILLAR_TYPE_PROMOTIONAL,
})

# ---------------------------------------------------------------------------
# Content format constants
# ---------------------------------------------------------------------------

CONTENT_FORMAT_CAROUSEL = "carousel"
CONTENT_FORMAT_REEL = "reel"
CONTENT_FORMAT_MULTI_COPY = "multi_copy"
CONTENT_FORMAT_STORY = "story"
CONTENT_FORMAT_POST = "post"

VALID_CONTENT_FORMATS = frozenset({
    CONTENT_FORMAT_CAROUSEL,
    CONTENT_FORMAT_REEL,
    CONTENT_FORMAT_MULTI_COPY,
    CONTENT_FORMAT_STORY,
    CONTENT_FORMAT_POST,
})

# ---------------------------------------------------------------------------
# Platform constants
# ---------------------------------------------------------------------------

PLATFORM_INSTAGRAM = "instagram"
PLATFORM_FACEBOOK = "facebook"
PLATFORM_TIKTOK = "tiktok"
PLATFORM_YOUTUBE = "youtube"

VALID_PLATFORMS = frozenset({
    PLATFORM_INSTAGRAM,
    PLATFORM_FACEBOOK,
    PLATFORM_TIKTOK,
    PLATFORM_YOUTUBE,
})

# ---------------------------------------------------------------------------
# Frequency constants
# ---------------------------------------------------------------------------

FREQUENCY_DAILY = "daily"
FREQUENCY_WEEKLY = "weekly"
FREQUENCY_BIWEEKLY = "biweekly"
FREQUENCY_MONTHLY = "monthly"

VALID_FREQUENCIES = frozenset({
    FREQUENCY_DAILY,
    FREQUENCY_WEEKLY,
    FREQUENCY_BIWEEKLY,
    FREQUENCY_MONTHLY,
})

# ---------------------------------------------------------------------------
# Tone constants
# ---------------------------------------------------------------------------

TONE_PROFESSIONAL = "professional"
TONE_CASUAL = "casual"
TONE_HUMOROUS = "humorous"
TONE_INSPIRATIONAL = "inspirational"
TONE_URGENT = "urgent"

VALID_TONES = frozenset({
    TONE_PROFESSIONAL,
    TONE_CASUAL,
    TONE_HUMOROUS,
    TONE_INSPIRATIONAL,
    TONE_URGENT,
})

# ---------------------------------------------------------------------------
# CTA type constants
# ---------------------------------------------------------------------------

CTA_LINK_BIO = "link_bio"
CTA_DM = "dm"
CTA_COMMENT = "comment"
CTA_SHARE = "share"
CTA_SAVE = "save"
CTA_VISIT = "visit"
CTA_BOOK = "book"

VALID_CTAS = frozenset({
    CTA_LINK_BIO,
    CTA_DM,
    CTA_COMMENT,
    CTA_SHARE,
    CTA_SAVE,
    CTA_VISIT,
    CTA_BOOK,
})

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass
class MarketingObjective:
    """A measurable marketing goal tied to a business outcome."""
    id: str
    name: str
    description: str
    objective_type: str
    priority: str
    target_metric: str
    target_value: float
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        name: str,
        description: str,
        objective_type: str,
        priority: str = PRIORITY_MEDIUM,
        target_metric: str = "",
        target_value: float = 0.0,
        notes: Optional[str] = None,
    ) -> "MarketingObjective":
        if objective_type not in VALID_OBJECTIVE_TYPES:
            raise ValueError(
                f"Invalid objective_type {objective_type!r}. "
                f"Must be one of {sorted(VALID_OBJECTIVE_TYPES)}"
            )
        if priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority {priority!r}. "
                f"Must be one of {sorted(VALID_PRIORITIES)}"
            )
        return cls(
            id=_new_id("mktobj_"),
            name=name,
            description=description,
            objective_type=objective_type,
            priority=priority,
            target_metric=target_metric,
            target_value=target_value,
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "objective_type": self.objective_type,
            "priority": self.priority,
            "target_metric": self.target_metric,
            "target_value": self.target_value,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MarketingObjective":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AudienceProfile:
    """Target audience definition with demographics, interests, and pain points."""
    id: str
    name: str
    description: str
    demographics: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    pain_points: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        name: str,
        description: str,
        demographics: Optional[list[str]] = None,
        interests: Optional[list[str]] = None,
        pain_points: Optional[list[str]] = None,
        platforms: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> "AudienceProfile":
        if platforms:
            invalid = set(platforms) - VALID_PLATFORMS
            if invalid:
                raise ValueError(
                    f"Invalid platforms {sorted(invalid)!r}. "
                    f"Must be subset of {sorted(VALID_PLATFORMS)}"
                )
        return cls(
            id=_new_id("aud_"),
            name=name,
            description=description,
            demographics=demographics or [],
            interests=interests or [],
            pain_points=pain_points or [],
            platforms=platforms or [],
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "demographics": list(self.demographics),
            "interests": list(self.interests),
            "pain_points": list(self.pain_points),
            "platforms": list(self.platforms),
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AudienceProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @property
    def persona_slug(self) -> str:
        return self.name.lower().replace(" ", "_")


@dataclass
class ContentPillar:
    """A thematic pillar for content production with topics, formats and cadence."""
    id: str
    name: str
    description: str
    pillar_type: str
    topics: list[str] = field(default_factory=list)
    content_formats: list[str] = field(default_factory=list)
    frequency: str = FREQUENCY_WEEKLY
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        name: str,
        description: str,
        pillar_type: str,
        topics: Optional[list[str]] = None,
        content_formats: Optional[list[str]] = None,
        frequency: str = FREQUENCY_WEEKLY,
        notes: Optional[str] = None,
    ) -> "ContentPillar":
        if pillar_type not in VALID_PILLAR_TYPES:
            raise ValueError(
                f"Invalid pillar_type {pillar_type!r}. "
                f"Must be one of {sorted(VALID_PILLAR_TYPES)}"
            )
        if frequency not in VALID_FREQUENCIES:
            raise ValueError(
                f"Invalid frequency {frequency!r}. "
                f"Must be one of {sorted(VALID_FREQUENCIES)}"
            )
        if content_formats:
            invalid = set(content_formats) - VALID_CONTENT_FORMATS
            if invalid:
                raise ValueError(
                    f"Invalid content_formats {sorted(invalid)!r}. "
                    f"Must be subset of {sorted(VALID_CONTENT_FORMATS)}"
                )
        return cls(
            id=_new_id("pil_"),
            name=name,
            description=description,
            pillar_type=pillar_type,
            topics=topics or [],
            content_formats=content_formats or [],
            frequency=frequency,
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "pillar_type": self.pillar_type,
            "topics": list(self.topics),
            "content_formats": list(self.content_formats),
            "frequency": self.frequency,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContentPillar":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ContentItem:
    """A single content delivery slot in a content plan."""
    date: str
    pillar_id: str
    topic: str
    content_format: str
    platform: str
    hook: str = ""
    cta: str = CTA_LINK_BIO
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "pillar_id": self.pillar_id,
            "topic": self.topic,
            "content_format": self.content_format,
            "platform": self.platform,
            "hook": self.hook,
            "cta": self.cta,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContentItem":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CampaignBrief:
    """Complete campaign blueprint tying objective, audience, pillars and messaging."""
    id: str
    name: str
    objective_id: str
    audience_id: str
    pillar_ids: list[str] = field(default_factory=list)
    start_date: str = ""
    end_date: str = ""
    budget: float = 0.0
    key_message: str = ""
    call_to_action: str = CTA_LINK_BIO
    tone: str = TONE_PROFESSIONAL
    constraints: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        name: str,
        objective_id: str,
        audience_id: str,
        pillar_ids: Optional[list[str]] = None,
        start_date: str = "",
        end_date: str = "",
        budget: float = 0.0,
        key_message: str = "",
        call_to_action: str = CTA_LINK_BIO,
        tone: str = TONE_PROFESSIONAL,
        constraints: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> "CampaignBrief":
        if call_to_action not in VALID_CTAS:
            raise ValueError(
                f"Invalid call_to_action {call_to_action!r}. "
                f"Must be one of {sorted(VALID_CTAS)}"
            )
        if tone not in VALID_TONES:
            raise ValueError(
                f"Invalid tone {tone!r}. "
                f"Must be one of {sorted(VALID_TONES)}"
            )
        return cls(
            id=_new_id("cmp_"),
            name=name,
            objective_id=objective_id,
            audience_id=audience_id,
            pillar_ids=pillar_ids or [],
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            key_message=key_message,
            call_to_action=call_to_action,
            tone=tone,
            constraints=constraints or [],
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "objective_id": self.objective_id,
            "audience_id": self.audience_id,
            "pillar_ids": list(self.pillar_ids),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "budget": self.budget,
            "key_message": self.key_message,
            "call_to_action": self.call_to_action,
            "tone": self.tone,
            "constraints": list(self.constraints),
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CampaignBrief":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ContentPlan:
    """Scheduled content calendar with delivery slots."""
    id: str
    campaign_id: str
    items: list[ContentItem] = field(default_factory=list)
    schedule_start: str = ""
    schedule_end: str = ""
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        campaign_id: str,
        items: Optional[list[ContentItem]] = None,
        schedule_start: str = "",
        schedule_end: str = "",
        notes: Optional[str] = None,
    ) -> "ContentPlan":
        return cls(
            id=_new_id("pln_"),
            campaign_id=campaign_id,
            items=items or [],
            schedule_start=schedule_start,
            schedule_end=schedule_end,
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "items": [item.to_dict() for item in self.items],
            "schedule_start": self.schedule_start,
            "schedule_end": self.schedule_end,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContentPlan":
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        if "items" in fields and fields["items"]:
            raw_items = fields["items"]
            if raw_items and isinstance(raw_items[0], dict):
                fields["items"] = [ContentItem.from_dict(it) for it in raw_items]
        return cls(**fields)

    @property
    def item_count(self) -> int:
        return len(self.items)

    def add_item(self, item: ContentItem) -> None:
        self.items.append(item)


@dataclass
class CampaignPackage:
    """Fully assembled campaign deliverable — brief + plan + validation."""
    id: str
    name: str
    brief: Optional[CampaignBrief] = None
    plan: Optional[ContentPlan] = None
    validation_issues: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        name: str,
        brief: Optional[CampaignBrief] = None,
        plan: Optional[ContentPlan] = None,
        validation_issues: Optional[list[str]] = None,
        validation_warnings: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> "CampaignPackage":
        return cls(
            id=_new_id("pkg_"),
            name=name,
            brief=brief,
            plan=plan,
            validation_issues=validation_issues or [],
            validation_warnings=validation_warnings or [],
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "brief": self.brief.to_dict() if self.brief else None,
            "plan": self.plan.to_dict() if self.plan else None,
            "validation_issues": list(self.validation_issues),
            "validation_warnings": list(self.validation_warnings),
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CampaignPackage":
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        if "brief" in fields and isinstance(fields["brief"], dict):
            fields["brief"] = CampaignBrief.from_dict(fields["brief"])
        if "plan" in fields and isinstance(fields["plan"], dict):
            fields["plan"] = ContentPlan.from_dict(fields["plan"])
        return cls(**fields)

    @property
    def is_valid(self) -> bool:
        return len(self.validation_issues) == 0

    @property
    def content_count(self) -> int:
        if self.plan:
            return self.plan.item_count
        return 0
