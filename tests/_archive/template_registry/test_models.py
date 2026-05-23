"""Tests for TemplateEntry model."""

import pytest

from src.template_registry.models import (
    TemplateEntry,
    TemplateCategory,
    TemplateStatus,
)


class TestTemplateCategory:
    def test_all_categories_exist(self):
        assert TemplateCategory.MARKETING == "marketing"
        assert TemplateCategory.VIDEO == "video"
        assert TemplateCategory.APP_FACTORY == "app_factory"
        assert TemplateCategory.SALES == "sales"
        assert TemplateCategory.OPS == "ops"
        assert TemplateCategory.DESIGN == "design"
        assert TemplateCategory.AUTOMATION == "automation"

    def test_category_count(self):
        assert len(TemplateCategory) == 7


class TestTemplateStatus:
    def test_status_flow(self):
        assert TemplateStatus.DRAFT == "draft"
        assert TemplateStatus.REVIEW == "review"
        assert TemplateStatus.APPROVED == "approved"
        assert TemplateStatus.ACTIVE == "active"
        assert TemplateStatus.DEPRECATED == "deprecated"
        assert TemplateStatus.ARCHIVED == "archived"


class TestTemplateEntry:
    def test_minimal_construction(self):
        entry = TemplateEntry(
            template_id="t1",
            name="Test Template",
            category=TemplateCategory.MARKETING,
            description="A test template",
        )
        assert entry.template_id == "t1"
        assert entry.name == "Test Template"
        assert entry.category == TemplateCategory.MARKETING
        assert entry.status == TemplateStatus.DRAFT
        assert entry.version == 1
        assert entry.tags == []
        assert entry.content == {}
        assert entry.score is None
        assert entry.usage_count == 0

    def test_full_construction(self):
        entry = TemplateEntry(
            template_id="carousel_v1",
            name="Carrossel Autoridade",
            category=TemplateCategory.DESIGN,
            description="Template de carrossel para autoridade",
            status=TemplateStatus.ACTIVE,
            version=3,
            tags=["carrossel", "autoridade", "instagram"],
            content={"slides": 10, "aspect_ratio": "1:1"},
            source_mission_id="MIS-001",
            source_output_path="/exports/carousel_01",
            score=9.2,
            usage_count=15,
            files=["slide_01.png"],
            dependencies=["caption_template_01"],
        )
        assert entry.version == 3
        assert entry.score == 9.2
        assert entry.usage_count == 15

    def test_to_dict_roundtrip(self):
        entry = TemplateEntry(
            template_id="r1",
            name="Roundtrip",
            category=TemplateCategory.VIDEO,
            description="Roundtrip test",
            status=TemplateStatus.APPROVED,
            version=2,
            tags=["reels", "video"],
            content={"duration": "30s"},
            score=8.0,
        )
        d = entry.to_dict()
        restored = TemplateEntry.from_dict(d)
        assert restored.template_id == entry.template_id
        assert restored.name == entry.name
        assert restored.category == entry.category
        assert restored.status == entry.status
        assert restored.version == entry.version
        assert restored.tags == entry.tags
        assert restored.content == entry.content
        assert restored.score == entry.score

    def test_from_dict_preserves_enums(self):
        d = {
            "template_id": "e1",
            "name": "Enum Test",
            "category": "sales",
            "description": "Testing enum roundtrip",
            "status": "active",
        }
        entry = TemplateEntry.from_dict(d)
        assert isinstance(entry.category, TemplateCategory)
        assert isinstance(entry.status, TemplateStatus)
        assert entry.category == TemplateCategory.SALES
        assert entry.status == TemplateStatus.ACTIVE

    def test_bump_version(self):
        entry = TemplateEntry(
            template_id="v1", name="Versioned", category=TemplateCategory.OPS,
            description="Version test", version=5,
        )
        entry.bump_version()
        assert entry.version == 6

    def test_touch_updates_timestamp(self):
        entry = TemplateEntry(
            template_id="t1", name="Touch", category=TemplateCategory.OPS,
            description="Touch test",
        )
        old_ts = entry.updated_at
        import time
        time.sleep(0.001)
        entry.touch()
        assert entry.updated_at > old_ts

    def test_multiple_entries_independent(self):
        e1 = TemplateEntry(
            template_id="a", name="A", category=TemplateCategory.MARKETING,
            description="First",
        )
        e2 = TemplateEntry(
            template_id="b", name="B", category=TemplateCategory.VIDEO,
            description="Second",
        )
        assert e1.template_id != e2.template_id
