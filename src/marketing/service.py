"""P5 Marketing Supreme — deterministic Marketing Planner service.

All operations are dry-run by default. Zero LLM. Zero network. Zero database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.marketing.models import (
    _now_iso,
    _new_id,
    AudienceProfile,
    CampaignBrief,
    CampaignPackage,
    ContentPlan,
    ContentPillar,
    ContentItem,
    MarketingObjective,
    PRIORITY_MEDIUM,
    CTA_LINK_BIO,
    TONE_PROFESSIONAL,
    FREQUENCY_WEEKLY,
    CONTENT_FORMAT_CAROUSEL,
    CONTENT_FORMAT_POST,
    PLATFORM_INSTAGRAM,
    VALID_CTAS,
    VALID_TONES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assign_date(start: str, item_index: int, pillar_count: int) -> str:
    """Assign a date string for a content item. Uses start_date as-is if provided,
    otherwise returns empty string (caller should fill in)."""
    if not start:
        return ""
    day_offset = item_index // max(pillar_count, 1)
    return f"day_{day_offset + 1}"


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Outcome of campaign validation."""
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
# Marketing Planner
# ---------------------------------------------------------------------------


class MarketingPlanner:
    """Deterministic marketing planner — dry-run by default.

    Models campaigns end-to-end without publishing, LLM calls,
    network access or database writes.
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._objectives: list[MarketingObjective] = []
        self._audiences: list[AudienceProfile] = []
        self._pillars: list[ContentPillar] = []
        self._briefs: list[CampaignBrief] = []
        self._plans: list[ContentPlan] = []
        self._packages: list[CampaignPackage] = []

    # -- Define entities --------------------------------------------------

    def define_objective(
        self,
        name: str,
        description: str,
        objective_type: str,
        priority: str = PRIORITY_MEDIUM,
        target_metric: str = "",
        target_value: float = 0.0,
        notes: Optional[str] = None,
    ) -> MarketingObjective:
        obj = MarketingObjective.new(
            name=name,
            description=description,
            objective_type=objective_type,
            priority=priority,
            target_metric=target_metric,
            target_value=target_value,
            notes=notes,
        )
        self._objectives.append(obj)
        return obj

    def define_audience(
        self,
        name: str,
        description: str,
        demographics: Optional[list[str]] = None,
        interests: Optional[list[str]] = None,
        pain_points: Optional[list[str]] = None,
        platforms: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> AudienceProfile:
        audience = AudienceProfile.new(
            name=name,
            description=description,
            demographics=demographics,
            interests=interests,
            pain_points=pain_points,
            platforms=platforms,
            notes=notes,
        )
        self._audiences.append(audience)
        return audience

    def define_pillar(
        self,
        name: str,
        description: str,
        pillar_type: str,
        topics: Optional[list[str]] = None,
        content_formats: Optional[list[str]] = None,
        frequency: str = FREQUENCY_WEEKLY,
        notes: Optional[str] = None,
    ) -> ContentPillar:
        pillar = ContentPillar.new(
            name=name,
            description=description,
            pillar_type=pillar_type,
            topics=topics,
            content_formats=content_formats,
            frequency=frequency,
            notes=notes,
        )
        self._pillars.append(pillar)
        return pillar

    # -- Build brief ------------------------------------------------------

    def build_campaign_brief(
        self,
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
    ) -> CampaignBrief:
        brief = CampaignBrief.new(
            name=name,
            objective_id=objective_id,
            audience_id=audience_id,
            pillar_ids=pillar_ids,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            key_message=key_message,
            call_to_action=call_to_action,
            tone=tone,
            constraints=constraints,
            notes=notes,
        )
        self._briefs.append(brief)
        return brief

    # -- Generate content plan --------------------------------------------

    def generate_content_plan(
        self,
        campaign_id: str,
        pillars: list[ContentPillar],
        start_date: str = "",
        end_date: str = "",
        posts_per_pillar: int = 1,
        default_platform: str = PLATFORM_INSTAGRAM,
    ) -> ContentPlan:
        """Deterministically generate a content calendar from pillars."""
        items: list[ContentItem] = []
        for pillar in pillars:
            fmt = pillar.content_formats[0] if pillar.content_formats else CONTENT_FORMAT_POST
            for i in range(posts_per_pillar):
                topic = pillar.topics[i % len(pillar.topics)] if pillar.topics else pillar.name
                items.append(
                    ContentItem(
                        date=_assign_date(start_date, i, len(pillars)),
                        pillar_id=pillar.id,
                        topic=topic,
                        content_format=fmt,
                        platform=default_platform,
                    )
                )
        plan = ContentPlan.new(
            campaign_id=campaign_id,
            items=items,
            schedule_start=start_date,
            schedule_end=end_date,
        )
        self._plans.append(plan)
        return plan

    # -- Build campaign package -------------------------------------------

    def build_campaign_package(
        self,
        name: str,
        brief: CampaignBrief,
        plan: ContentPlan,
        notes: Optional[str] = None,
    ) -> CampaignPackage:
        package = CampaignPackage.new(
            name=name,
            brief=brief,
            plan=plan,
            notes=notes,
        )
        self._packages.append(package)
        return package

    # -- Validate ---------------------------------------------------------

    def validate_campaign(self, brief: CampaignBrief, plan: Optional[ContentPlan] = None) -> ValidationResult:
        issues: list[str] = []
        warnings: list[str] = []

        if not brief.name.strip():
            issues.append("Campaign brief name is empty")
        if not brief.objective_id.strip():
            issues.append("Campaign brief has no objective_id")
        if not brief.audience_id.strip():
            issues.append("Campaign brief has no audience_id")
        if not brief.pillar_ids:
            warnings.append("Campaign brief has no content pillars")
        if brief.budget < 0:
            issues.append(f"Budget cannot be negative (got {brief.budget})")
        if brief.start_date and brief.end_date and brief.start_date > brief.end_date:
            issues.append(f"start_date {brief.start_date} is after end_date {brief.end_date}")

        if plan is not None:
            if plan.item_count == 0:
                warnings.append("Content plan has zero items")
            seen_dates: set[str] = set()
            for item in plan.items:
                if item.content_format not in {CONTENT_FORMAT_CAROUSEL, "reel", "multi_copy", "story", "post"}:
                    issues.append(f"Unknown content_format {item.content_format!r} in item {item.date}")
                if item.cta not in VALID_CTAS:
                    issues.append(f"Invalid CTA {item.cta!r} in item {item.date}")
                if item.date in seen_dates:
                    warnings.append(f"Multiple items on same date: {item.date}")
                seen_dates.add(item.date)

        if issues:
            return ValidationResult.failure(issues, warnings)
        return ValidationResult.success(warnings)

    # -- Properties -------------------------------------------------------

    @property
    def objective_count(self) -> int:
        return len(self._objectives)

    @property
    def audience_count(self) -> int:
        return len(self._audiences)

    @property
    def pillar_count(self) -> int:
        return len(self._pillars)

    @property
    def brief_count(self) -> int:
        return len(self._briefs)

    @property
    def plan_count(self) -> int:
        return len(self._plans)

    @property
    def package_count(self) -> int:
        return len(self._packages)

    @property
    def total_entities(self) -> int:
        return (
            self.objective_count
            + self.audience_count
            + self.pillar_count
            + self.brief_count
            + self.plan_count
            + self.package_count
        )
