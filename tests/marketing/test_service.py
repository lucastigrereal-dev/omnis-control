"""Tests for P5 Marketing Supreme service — MarketingPlanner."""

from __future__ import annotations

import pytest

from src.marketing.service import (
    MarketingPlanner,
    ValidationResult,
)
from src.marketing.models import (
    OBJECTIVE_TYPE_ENGAGEMENT,
    OBJECTIVE_TYPE_CONVERSION,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PILLAR_TYPE_EDUCATIONAL,
    PILLAR_TYPE_PROMOTIONAL,
    CONTENT_FORMAT_CAROUSEL,
    CONTENT_FORMAT_REEL,
    CONTENT_FORMAT_POST,
    PLATFORM_INSTAGRAM,
    FREQUENCY_WEEKLY,
    FREQUENCY_BIWEEKLY,
    TONE_URGENT,
    TONE_PROFESSIONAL,
    CTA_LINK_BIO,
    CTA_VISIT,
    CTA_BOOK,
    ContentItem,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_planner() -> MarketingPlanner:
    return MarketingPlanner(dry_run=True)


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
        r = ValidationResult.success(["low reach"])
        assert r.ok is True
        assert r.warnings == ["low reach"]

    def test_failure(self):
        r = ValidationResult.failure(["no objective"])
        assert r.ok is False
        assert r.valid is False

    def test_failure_with_warnings(self):
        r = ValidationResult.failure(["no objective"], ["no pillars"])
        assert r.ok is False
        assert r.warnings == ["no pillars"]


# ---------------------------------------------------------------------------
# MarketingPlanner — entity definition
# ---------------------------------------------------------------------------


class TestDefineEntities:
    def test_define_objective_adds_entity(self):
        planner = _setup_planner()
        obj = planner.define_objective("Awareness", "Build brand", "awareness")
        assert obj.name == "Awareness"
        assert planner.objective_count == 1

    def test_define_audience_adds_entity(self):
        planner = _setup_planner()
        aud = planner.define_audience("Travelers", "People who travel", platforms=["instagram"])
        assert aud.name == "Travelers"
        assert planner.audience_count == 1

    def test_define_pillar_adds_entity(self):
        planner = _setup_planner()
        pil = planner.define_pillar("Tips", "Travel tips", "educational")
        assert pil.name == "Tips"
        assert planner.pillar_count == 1

    def test_multiple_entities_accumulate(self):
        planner = _setup_planner()
        planner.define_objective("A1", "D1", OBJECTIVE_TYPE_ENGAGEMENT)
        planner.define_objective("A2", "D2", OBJECTIVE_TYPE_CONVERSION)
        planner.define_audience("Aud1", "Desc")
        assert planner.objective_count == 2
        assert planner.audience_count == 1
        assert planner.total_entities == 3


# ---------------------------------------------------------------------------
# MarketingPlanner — build_campaign_brief
# ---------------------------------------------------------------------------


class TestBuildCampaignBrief:
    def test_build_brief_adds_entity(self):
        planner = _setup_planner()
        brief = planner.build_campaign_brief(
            name="Summer Campaign",
            objective_id="mktobj_abc",
            audience_id="aud_def",
        )
        assert brief.name == "Summer Campaign"
        assert brief.id.startswith("cmp_")
        assert planner.brief_count == 1

    def test_build_brief_with_full_params(self):
        planner = _setup_planner()
        brief = planner.build_campaign_brief(
            name="Full Campaign",
            objective_id="mktobj_xyz",
            audience_id="aud_123",
            pillar_ids=["pil_a", "pil_b"],
            start_date="2026-06-01",
            end_date="2026-06-30",
            budget=10000.0,
            key_message="Viaje agora",
            call_to_action=CTA_BOOK,
            tone=TONE_URGENT,
            constraints=["sem concorrentes"],
            notes="Urgente",
        )
        assert brief.budget == 10000.0
        assert brief.tone == TONE_URGENT
        assert brief.call_to_action == CTA_BOOK
        assert "sem concorrentes" in brief.constraints


# ---------------------------------------------------------------------------
# MarketingPlanner — generate_content_plan
# ---------------------------------------------------------------------------


class TestGenerateContentPlan:
    def test_generates_plan_from_pillars(self):
        planner = _setup_planner()
        pil = planner.define_pillar(
            "Dicas",
            "Travel tips",
            PILLAR_TYPE_EDUCATIONAL,
            topics=["hotel", "resort"],
            content_formats=[CONTENT_FORMAT_CAROUSEL],
        )
        plan = planner.generate_content_plan(
            campaign_id="cmp_test",
            pillars=[pil],
            posts_per_pillar=2,
        )
        assert plan.campaign_id == "cmp_test"
        assert plan.item_count == 2

    def test_generates_plan_multiple_pillars(self):
        planner = _setup_planner()
        p1 = planner.define_pillar(
            "Dicas",
            "Tips",
            PILLAR_TYPE_EDUCATIONAL,
            topics=["hotel"],
            content_formats=[CONTENT_FORMAT_CAROUSEL],
        )
        p2 = planner.define_pillar(
            "Promos",
            "Offers",
            PILLAR_TYPE_PROMOTIONAL,
            topics=["desconto"],
            content_formats=[CONTENT_FORMAT_REEL],
        )
        plan = planner.generate_content_plan(
            campaign_id="cmp_multi",
            pillars=[p1, p2],
            posts_per_pillar=1,
        )
        assert plan.item_count == 2
        # first item from first pillar
        assert plan.items[0].pillar_id == p1.id
        assert plan.items[0].topic == "hotel"
        assert plan.items[0].content_format == CONTENT_FORMAT_CAROUSEL
        # second item from second pillar
        assert plan.items[1].pillar_id == p2.id
        assert plan.items[1].topic == "desconto"
        assert plan.items[1].content_format == CONTENT_FORMAT_REEL
        assert planner.plan_count == 1

    def test_plan_falls_back_to_post_format(self):
        planner = _setup_planner()
        pil = planner.define_pillar(
            "Sem formato",
            "No formats defined",
            PILLAR_TYPE_EDUCATIONAL,
            topics=["geral"],
            content_formats=[],
        )
        plan = planner.generate_content_plan("cmp_fallback", [pil], posts_per_pillar=1)
        assert plan.items[0].content_format == CONTENT_FORMAT_POST

    def test_plan_topic_wraps_for_extra_posts(self):
        planner = _setup_planner()
        pil = planner.define_pillar(
            "Wrap",
            "Wrapping test",
            PILLAR_TYPE_EDUCATIONAL,
            topics=["only_one"],
            content_formats=[CONTENT_FORMAT_POST],
        )
        plan = planner.generate_content_plan("cmp_wrap", [pil], posts_per_pillar=3)
        assert plan.item_count == 3
        assert plan.items[0].topic == "only_one"
        assert plan.items[1].topic == "only_one"
        assert plan.items[2].topic == "only_one"


# ---------------------------------------------------------------------------
# MarketingPlanner — build_campaign_package
# ---------------------------------------------------------------------------


class TestBuildCampaignPackage:
    def test_build_package(self):
        planner = _setup_planner()
        obj = planner.define_objective("Engage", "Boost", OBJECTIVE_TYPE_ENGAGEMENT)
        aud = planner.define_audience("Travelers", "Desc")
        pil = planner.define_pillar(
            "Content",
            "Pillar desc",
            PILLAR_TYPE_EDUCATIONAL,
            topics=["tips"],
            content_formats=[CONTENT_FORMAT_CAROUSEL],
        )
        brief = planner.build_campaign_brief("Campaign", obj.id, aud.id, pillar_ids=[pil.id])
        plan = planner.generate_content_plan(brief.id, [pil], posts_per_pillar=1)
        pkg = planner.build_campaign_package("Package 1", brief, plan)

        assert pkg.id.startswith("pkg_")
        assert pkg.brief.id == brief.id
        assert pkg.plan.id == plan.id
        assert planner.package_count == 1


# ---------------------------------------------------------------------------
# MarketingPlanner — validate_campaign
# ---------------------------------------------------------------------------


class TestValidateCampaign:
    def test_valid_brief(self):
        planner = _setup_planner()
        obj = planner.define_objective("Engage", "Boost", OBJECTIVE_TYPE_ENGAGEMENT)
        aud = planner.define_audience("Audience", "Desc")
        brief = planner.build_campaign_brief("Valid", obj.id, aud.id, pillar_ids=["pil_x"])
        result = planner.validate_campaign(brief)
        assert result.ok is True

    def test_brief_empty_name(self):
        planner = _setup_planner()
        brief = planner.build_campaign_brief("", "obj_id", "aud_id")
        result = planner.validate_campaign(brief)
        assert result.ok is False
        assert any("name is empty" in issue for issue in result.issues)

    def test_brief_no_objective(self):
        planner = _setup_planner()
        brief = planner.build_campaign_brief("Test", "", "aud_id")
        result = planner.validate_campaign(brief)
        assert result.ok is False
        assert any("objective_id" in issue for issue in result.issues)

    def test_brief_no_audience(self):
        planner = _setup_planner()
        brief = planner.build_campaign_brief("Test", "obj_id", "")
        result = planner.validate_campaign(brief)
        assert result.ok is False
        assert any("audience_id" in issue for issue in result.issues)

    def test_brief_negative_budget(self):
        planner = _setup_planner()
        brief = planner.build_campaign_brief("Test", "obj_id", "aud_id", budget=-100.0)
        result = planner.validate_campaign(brief)
        assert result.ok is False
        assert any("negative" in issue for issue in result.issues)

    def test_brief_date_inversion(self):
        planner = _setup_planner()
        brief = planner.build_campaign_brief("Test", "obj_id", "aud_id", start_date="2026-12-31", end_date="2026-01-01")
        result = planner.validate_campaign(brief)
        assert result.ok is False
        assert any("after" in issue for issue in result.issues)

    def test_empty_pillars_warns(self):
        planner = _setup_planner()
        brief = planner.build_campaign_brief("Test", "obj_id", "aud_id")
        result = planner.validate_campaign(brief)
        assert result.ok is True
        assert any("no content pillars" in w for w in result.warnings)

    def test_empty_plan_warns(self):
        planner = _setup_planner()
        brief = planner.build_campaign_brief("Test", "obj_id", "aud_id")
        plan = planner.generate_content_plan("cmp_test", [], posts_per_pillar=0)
        result = planner.validate_campaign(brief, plan)
        assert any("zero items" in w.lower() for w in result.warnings)

    def test_duplicate_dates_warns(self):
        planner = _setup_planner()
        brief = planner.build_campaign_brief("Test", "obj_id", "aud_id")
        plan = planner.generate_content_plan("cmp_dup", [], posts_per_pillar=0)
        plan.items = [
            ContentItem(date="2026-06-01", pillar_id="p1", topic="A", content_format=CONTENT_FORMAT_POST, platform=PLATFORM_INSTAGRAM),
            ContentItem(date="2026-06-01", pillar_id="p2", topic="B", content_format=CONTENT_FORMAT_POST, platform=PLATFORM_INSTAGRAM),
        ]
        result = planner.validate_campaign(brief, plan)
        assert any("same date" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# MarketingPlanner — dry_run flag
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_default_dry_run(self):
        planner = MarketingPlanner()
        assert planner.dry_run is True

    def test_explicit_dry_run_true(self):
        planner = MarketingPlanner(dry_run=True)
        obj = planner.define_objective("X", "Y", OBJECTIVE_TYPE_ENGAGEMENT)
        assert obj is not None

    def test_non_dry_run_also_works(self):
        planner = MarketingPlanner(dry_run=False)
        obj = planner.define_objective("X", "Y", OBJECTIVE_TYPE_ENGAGEMENT)
        assert obj is not None
