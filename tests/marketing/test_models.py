"""Tests for P5 Marketing Supreme models and constants."""

from __future__ import annotations

import pytest

from src.marketing.models import (
    MarketingObjective,
    AudienceProfile,
    ContentPillar,
    ContentItem,
    CampaignBrief,
    ContentPlan,
    CampaignPackage,
    OBJECTIVE_TYPE_AWARENESS,
    OBJECTIVE_TYPE_ENGAGEMENT,
    OBJECTIVE_TYPE_CONVERSION,
    OBJECTIVE_TYPE_RETENTION,
    VALID_OBJECTIVE_TYPES,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    PRIORITY_HIGH,
    PRIORITY_CRITICAL,
    VALID_PRIORITIES,
    PILLAR_TYPE_EDUCATIONAL,
    PILLAR_TYPE_ENTERTAINING,
    PILLAR_TYPE_INSPIRATIONAL,
    PILLAR_TYPE_PROMOTIONAL,
    VALID_PILLAR_TYPES,
    CONTENT_FORMAT_CAROUSEL,
    CONTENT_FORMAT_REEL,
    CONTENT_FORMAT_MULTI_COPY,
    CONTENT_FORMAT_STORY,
    CONTENT_FORMAT_POST,
    VALID_CONTENT_FORMATS,
    PLATFORM_INSTAGRAM,
    PLATFORM_FACEBOOK,
    PLATFORM_TIKTOK,
    PLATFORM_YOUTUBE,
    VALID_PLATFORMS,
    FREQUENCY_DAILY,
    FREQUENCY_WEEKLY,
    FREQUENCY_BIWEEKLY,
    FREQUENCY_MONTHLY,
    VALID_FREQUENCIES,
    TONE_PROFESSIONAL,
    TONE_CASUAL,
    TONE_HUMOROUS,
    TONE_INSPIRATIONAL,
    TONE_URGENT,
    VALID_TONES,
    CTA_LINK_BIO,
    CTA_DM,
    CTA_COMMENT,
    CTA_SHARE,
    CTA_SAVE,
    CTA_VISIT,
    CTA_BOOK,
    VALID_CTAS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_objective(**kw) -> MarketingObjective:
    return MarketingObjective.new(
        name=kw.pop("name", "Boost Engagement"),
        description=kw.pop("description", "Increase IG engagement by 20%"),
        objective_type=kw.pop("objective_type", OBJECTIVE_TYPE_ENGAGEMENT),
        **kw,
    )


def _make_audience(**kw) -> AudienceProfile:
    return AudienceProfile.new(
        name=kw.pop("name", "Viajantes Familia"),
        description=kw.pop("description", "Families that travel with kids"),
        **kw,
    )


def _make_pillar(**kw) -> ContentPillar:
    return ContentPillar.new(
        name=kw.pop("name", "Dicas de Viagem"),
        description=kw.pop("description", "Travel tips for families"),
        pillar_type=kw.pop("pillar_type", PILLAR_TYPE_EDUCATIONAL),
        **kw,
    )


def _make_brief(**kw) -> CampaignBrief:
    return CampaignBrief.new(
        name=kw.pop("name", "Summer Launch"),
        objective_id=kw.pop("objective_id", "mktobj_abc123"),
        audience_id=kw.pop("audience_id", "aud_def456"),
        **kw,
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_valid_objective_types_count(self):
        assert len(VALID_OBJECTIVE_TYPES) == 4

    def test_valid_priorities_count(self):
        assert len(VALID_PRIORITIES) == 4

    def test_valid_pillar_types_count(self):
        assert len(VALID_PILLAR_TYPES) == 4

    def test_valid_content_formats_count(self):
        assert len(VALID_CONTENT_FORMATS) == 5

    def test_valid_platforms_count(self):
        assert len(VALID_PLATFORMS) == 4

    def test_valid_frequencies_count(self):
        assert len(VALID_FREQUENCIES) == 4

    def test_valid_tones_count(self):
        assert len(VALID_TONES) == 5

    def test_valid_ctas_count(self):
        assert len(VALID_CTAS) == 7

    def test_constant_sets_are_disjoint_objective(self):
        # constants within same group are distinct
        vals = {OBJECTIVE_TYPE_AWARENESS, OBJECTIVE_TYPE_ENGAGEMENT, OBJECTIVE_TYPE_CONVERSION, OBJECTIVE_TYPE_RETENTION}
        assert len(vals) == 4


# ---------------------------------------------------------------------------
# MarketingObjective
# ---------------------------------------------------------------------------


class TestMarketingObjective:
    def test_new_creates_with_id_prefix(self):
        obj = _make_objective()
        assert obj.id.startswith("mktobj_")
        assert obj.name == "Boost Engagement"

    def test_new_defaults_priority(self):
        obj = _make_objective()
        assert obj.priority == PRIORITY_MEDIUM

    def test_new_rejects_invalid_objective_type(self):
        with pytest.raises(ValueError, match="Invalid objective_type"):
            _make_objective(objective_type="bogus")

    def test_new_rejects_invalid_priority(self):
        with pytest.raises(ValueError, match="Invalid priority"):
            _make_objective(priority="extreme")

    def test_round_trip_dict(self):
        obj = _make_objective(
            name="Sales",
            description="Drive bookings",
            objective_type=OBJECTIVE_TYPE_CONVERSION,
            priority=PRIORITY_HIGH,
            target_metric="bookings",
            target_value=100.0,
        )
        d = obj.to_dict()
        restored = MarketingObjective.from_dict(d)
        assert restored.id == obj.id
        assert restored.name == obj.name
        assert restored.objective_type == OBJECTIVE_TYPE_CONVERSION
        assert restored.target_value == 100.0

    @pytest.mark.parametrize("val", sorted(VALID_OBJECTIVE_TYPES))
    def test_all_valid_objective_types(self, val):
        obj = _make_objective(objective_type=val)
        assert obj.objective_type == val

    @pytest.mark.parametrize("val", sorted(VALID_PRIORITIES))
    def test_all_valid_priorities(self, val):
        obj = _make_objective(priority=val)
        assert obj.priority == val

    def test_default_notes_is_none(self):
        obj = _make_objective()
        assert obj.notes is None


# ---------------------------------------------------------------------------
# AudienceProfile
# ---------------------------------------------------------------------------


class TestAudienceProfile:
    def test_new_creates_with_id_prefix(self):
        aud = _make_audience()
        assert aud.id.startswith("aud_")

    def test_new_defaults_empty_lists(self):
        aud = _make_audience()
        assert aud.demographics == []
        assert aud.interests == []
        assert aud.platforms == []

    def test_new_rejects_invalid_platform(self):
        with pytest.raises(ValueError, match="Invalid platforms"):
            _make_audience(platforms=["instagram", "snapchat"])

    def test_persona_slug(self):
        aud = _make_audience(name="Viajantes Familia")
        assert aud.persona_slug == "viajantes_familia"

    def test_round_trip_dict(self):
        aud = _make_audience(
            demographics=["25-40", "com filhos"],
            interests=["viagem", "hotel"],
            platforms=[PLATFORM_INSTAGRAM],
        )
        d = aud.to_dict()
        restored = AudienceProfile.from_dict(d)
        assert restored.id == aud.id
        assert restored.demographics == aud.demographics
        assert restored.platforms == aud.platforms


# ---------------------------------------------------------------------------
# ContentPillar
# ---------------------------------------------------------------------------


class TestContentPillar:
    def test_new_creates_with_id_prefix(self):
        pil = _make_pillar()
        assert pil.id.startswith("pil_")

    def test_new_defaults_frequency(self):
        pil = _make_pillar()
        assert pil.frequency == FREQUENCY_WEEKLY

    def test_new_rejects_invalid_pillar_type(self):
        with pytest.raises(ValueError, match="Invalid pillar_type"):
            _make_pillar(pillar_type="fake")

    def test_new_rejects_invalid_frequency(self):
        with pytest.raises(ValueError, match="Invalid frequency"):
            _make_pillar(frequency="annually")

    def test_new_rejects_invalid_content_format(self):
        with pytest.raises(ValueError, match="Invalid content_formats"):
            _make_pillar(content_formats=["tiktok_live"])

    def test_round_trip_dict(self):
        pil = _make_pillar(
            pillar_type=PILLAR_TYPE_PROMOTIONAL,
            topics=["hotel", "resort"],
            content_formats=[CONTENT_FORMAT_CAROUSEL, CONTENT_FORMAT_REEL],
            frequency=FREQUENCY_BIWEEKLY,
        )
        d = pil.to_dict()
        restored = ContentPillar.from_dict(d)
        assert restored.id == pil.id
        assert restored.pillar_type == PILLAR_TYPE_PROMOTIONAL
        assert restored.topics == ["hotel", "resort"]
        assert restored.frequency == FREQUENCY_BIWEEKLY

    def test_valid_content_formats_subset(self):
        pil = _make_pillar(content_formats=[CONTENT_FORMAT_CAROUSEL])
        assert pil.content_formats == [CONTENT_FORMAT_CAROUSEL]

    @pytest.mark.parametrize("val", sorted(VALID_PILLAR_TYPES))
    def test_all_valid_pillar_types(self, val):
        pil = _make_pillar(pillar_type=val)
        assert pil.pillar_type == val


# ---------------------------------------------------------------------------
# ContentItem
# ---------------------------------------------------------------------------


class TestContentItem:
    def test_defaults(self):
        item = ContentItem(date="2026-06-01", pillar_id="pil_abc", topic="Hotel tips", content_format=CONTENT_FORMAT_POST, platform=PLATFORM_INSTAGRAM)
        assert item.hook == ""
        assert item.cta == CTA_LINK_BIO
        assert item.notes == ""

    def test_round_trip_dict(self):
        item = ContentItem(
            date="2026-06-01",
            pillar_id="pil_abc",
            topic="Dicas Resort",
            content_format=CONTENT_FORMAT_CAROUSEL,
            platform=PLATFORM_INSTAGRAM,
            hook="Top 5 resorts",
            cta=CTA_BOOK,
        )
        d = item.to_dict()
        restored = ContentItem.from_dict(d)
        assert restored.date == "2026-06-01"
        assert restored.pillar_id == "pil_abc"
        assert restored.hook == "Top 5 resorts"
        assert restored.cta == CTA_BOOK


# ---------------------------------------------------------------------------
# CampaignBrief
# ---------------------------------------------------------------------------


class TestCampaignBrief:
    def test_new_creates_with_id_prefix(self):
        brief = _make_brief()
        assert brief.id.startswith("cmp_")

    def test_new_defaults(self):
        brief = _make_brief()
        assert brief.budget == 0.0
        assert brief.tone == TONE_PROFESSIONAL
        assert brief.call_to_action == CTA_LINK_BIO
        assert brief.pillar_ids == []
        assert brief.constraints == []

    def test_new_rejects_invalid_cta(self):
        with pytest.raises(ValueError, match="Invalid call_to_action"):
            _make_brief(call_to_action="send_money")

    def test_new_rejects_invalid_tone(self):
        with pytest.raises(ValueError, match="Invalid tone"):
            _make_brief(tone="angry")

    def test_round_trip_dict(self):
        brief = _make_brief(
            name="Winter Promo",
            pillar_ids=["pil_a", "pil_b"],
            start_date="2026-06-01",
            end_date="2026-06-30",
            budget=5000.0,
            key_message="Book now",
            tone=TONE_URGENT,
            call_to_action=CTA_VISIT,
            constraints=["no competitor mentions"],
        )
        d = brief.to_dict()
        restored = CampaignBrief.from_dict(d)
        assert restored.id == brief.id
        assert restored.budget == 5000.0
        assert restored.tone == TONE_URGENT
        assert restored.call_to_action == CTA_VISIT


# ---------------------------------------------------------------------------
# ContentPlan
# ---------------------------------------------------------------------------


class TestContentPlan:
    def test_new_creates_with_id_prefix(self):
        plan = ContentPlan.new(campaign_id="cmp_abc")
        assert plan.id.startswith("pln_")
        assert plan.campaign_id == "cmp_abc"

    def test_default_empty_items(self):
        plan = ContentPlan.new(campaign_id="cmp_xyz")
        assert plan.items == []
        assert plan.item_count == 0

    def test_add_item(self):
        plan = ContentPlan.new(campaign_id="cmp_abc")
        item = ContentItem(date="2026-06-01", pillar_id="pil_a", topic="X", content_format=CONTENT_FORMAT_POST, platform=PLATFORM_INSTAGRAM)
        plan.add_item(item)
        assert plan.item_count == 1

    def test_round_trip_dict(self):
        plan = ContentPlan.new(
            campaign_id="cmp_abc",
            schedule_start="2026-06-01",
            schedule_end="2026-06-30",
        )
        plan.add_item(ContentItem(date="2026-06-01", pillar_id="pil_a", topic="X", content_format=CONTENT_FORMAT_POST, platform=PLATFORM_INSTAGRAM))
        d = plan.to_dict()
        restored = ContentPlan.from_dict(d)
        assert restored.id == plan.id
        assert restored.item_count == 1
        assert restored.items[0].topic == "X"


# ---------------------------------------------------------------------------
# CampaignPackage
# ---------------------------------------------------------------------------


class TestCampaignPackage:
    def test_new_creates_with_id_prefix(self):
        pkg = CampaignPackage.new(name="Test Package")
        assert pkg.id.startswith("pkg_")

    def test_default_is_valid(self):
        pkg = CampaignPackage.new(name="Empty")
        assert pkg.is_valid is True
        assert pkg.content_count == 0

    def test_round_trip_dict(self):
        brief = _make_brief(name="Summer Sale")
        plan = ContentPlan.new(campaign_id=brief.id)
        pkg = CampaignPackage.new(
            name="Summer Package",
            brief=brief,
            plan=plan,
            validation_warnings=["no content yet"],
        )
        d = pkg.to_dict()
        restored = CampaignPackage.from_dict(d)
        assert restored.id == pkg.id
        assert restored.name == "Summer Package"
        assert restored.brief.id == brief.id
        assert restored.is_valid is True

    def test_with_issues(self):
        pkg = CampaignPackage.new(name="Broken", validation_issues=["no objective"])
        assert pkg.is_valid is False

    def test_content_count_with_plan(self):
        brief = _make_brief()
        plan = ContentPlan.new(campaign_id=brief.id)
        plan.add_item(ContentItem(date="2026-06-01", pillar_id="pil_a", topic="T", content_format=CONTENT_FORMAT_POST, platform=PLATFORM_INSTAGRAM))
        plan.add_item(ContentItem(date="2026-06-02", pillar_id="pil_b", topic="U", content_format=CONTENT_FORMAT_REEL, platform=PLATFORM_INSTAGRAM))
        pkg = CampaignPackage.new(name="Filled", brief=brief, plan=plan)
        assert pkg.content_count == 2
