"""Tests for TemplateRegistry manager."""

import json
import tempfile
from pathlib import Path

import pytest

from src.template_registry.models import (
    TemplateEntry,
    TemplateCategory,
    TemplateStatus,
)
from src.template_registry.registry import TemplateRegistry


@pytest.fixture
def empty_registry():
    with tempfile.TemporaryDirectory() as tmp:
        reg_path = Path(tmp) / "template_registry.json"
        tmpl_dir = Path(tmp) / "templates"
        reg = TemplateRegistry(registry_path=reg_path, templates_dir=tmpl_dir)
        yield reg


@pytest.fixture
def populated_registry(empty_registry):
    entries = [
        TemplateEntry(
            template_id="mkt_01",
            name="Carrossel Alcance",
            category=TemplateCategory.MARKETING,
            description="Carrossel de alto alcance",
            status=TemplateStatus.ACTIVE,
            tags=["carrossel", "alcance"],
            score=9.0,
            usage_count=42,
        ),
        TemplateEntry(
            template_id="vid_01",
            name="Reels Template",
            category=TemplateCategory.VIDEO,
            description="Template base para reels",
            status=TemplateStatus.ACTIVE,
            tags=["reels", "video"],
            score=8.5,
            usage_count=15,
        ),
        TemplateEntry(
            template_id="sales_01",
            name="DM Prospecção",
            category=TemplateCategory.SALES,
            description="Primeira DM de prospecção",
            status=TemplateStatus.DRAFT,
            tags=["dm", "prospeccao"],
            score=6.0,
        ),
        TemplateEntry(
            template_id="ops_01",
            name="Audit Report",
            category=TemplateCategory.OPS,
            description="Relatório de auditoria",
            status=TemplateStatus.APPROVED,
            tags=["audit", "report"],
            score=7.5,
        ),
    ]
    for e in entries:
        empty_registry.add(e)
    return empty_registry


class TestTemplateRegistryLifecycle:
    def test_empty_registry(self, empty_registry):
        assert empty_registry.count == 0
        assert empty_registry.list_all() == []

    def test_add_and_get(self, empty_registry):
        entry = TemplateEntry(
            template_id="t1", name="T1", category=TemplateCategory.MARKETING,
            description="Test",
        )
        empty_registry.add(entry)
        assert empty_registry.count == 1
        assert empty_registry.get("t1") is entry

    def test_add_duplicate_raises(self, populated_registry):
        entry = TemplateEntry(
            template_id="mkt_01", name="Dup", category=TemplateCategory.MARKETING,
            description="Duplicate",
        )
        with pytest.raises(KeyError):
            populated_registry.add(entry)

    def test_update(self, populated_registry):
        populated_registry.update("mkt_01", name="Updated Name", score=9.5)
        e = populated_registry.get("mkt_01")
        assert e.name == "Updated Name"
        assert e.score == 9.5

    def test_remove(self, populated_registry):
        assert populated_registry.count == 4
        populated_registry.remove("sales_01")
        assert populated_registry.count == 3
        assert populated_registry.get("sales_01") is None

    def test_save_and_load_roundtrip(self, populated_registry):
        populated_registry.save()
        # Load into a fresh registry
        new_reg = TemplateRegistry(
            populated_registry.registry_path,
            populated_registry.templates_dir,
        )
        new_reg.load()
        assert new_reg.count == populated_registry.count
        for eid in ["mkt_01", "vid_01", "sales_01", "ops_01"]:
            assert new_reg.get(eid) is not None
            assert new_reg.get(eid).template_id == eid


class TestTemplateRegistryQuery:
    def test_by_category(self, populated_registry):
        marketing = populated_registry.by_category(TemplateCategory.MARKETING)
        assert len(marketing) == 1
        assert marketing[0].template_id == "mkt_01"

        video = populated_registry.by_category(TemplateCategory.VIDEO)
        assert len(video) == 1

    def test_by_status(self, populated_registry):
        active = populated_registry.by_status(TemplateStatus.ACTIVE)
        assert len(active) == 2

        drafts = populated_registry.by_status(TemplateStatus.DRAFT)
        assert len(drafts) == 1
        assert drafts[0].template_id == "sales_01"

    def test_by_tag(self, populated_registry):
        carrossel = populated_registry.by_tag("carrossel")
        assert len(carrossel) == 1
        assert carrossel[0].template_id == "mkt_01"

    def test_search(self, populated_registry):
        results = populated_registry.search("carrossel")
        assert len(results) == 1

        results = populated_registry.search("template")
        assert len(results) >= 1

        results = populated_registry.search("nonexistent")
        assert len(results) == 0

    def test_top_by_score(self, populated_registry):
        top = populated_registry.top_by_score(limit=2)
        assert len(top) == 2
        assert top[0].score >= top[1].score

    def test_top_by_score_filtered(self, populated_registry):
        top = populated_registry.top_by_score(category=TemplateCategory.VIDEO, limit=5)
        assert len(top) == 1
        assert top[0].template_id == "vid_01"


class TestTemplateRegistryLifecycleActions:
    def test_promote(self, populated_registry):
        e = populated_registry.promote("sales_01")
        assert e.status == TemplateStatus.APPROVED

    def test_approve(self, populated_registry):
        e = populated_registry.approve("mkt_01")
        assert e.status == TemplateStatus.ACTIVE

    def test_deprecate(self, populated_registry):
        e = populated_registry.deprecate("vid_01")
        assert e.status == TemplateStatus.DEPRECATED
        assert e.deprecated_at is not None

    def test_bump_version(self, populated_registry):
        e = populated_registry.bump_version("mkt_01")
        assert e.version == 2

    def test_deprecate_then_reactivate(self, populated_registry):
        populated_registry.deprecate("vid_01")
        populated_registry.update("vid_01", status=TemplateStatus.ACTIVE)
        e = populated_registry.get("vid_01")
        assert e.status == TemplateStatus.ACTIVE


class TestTemplateRegistryStats:
    def test_stats(self, populated_registry):
        s = populated_registry.stats()
        assert s["total"] == 4
        assert "by_category" in s
        assert "by_status" in s
        assert s["by_category"]["marketing"] == 1
        assert s["by_category"]["video"] == 1
        assert s["by_category"]["sales"] == 1
        assert s["by_category"]["ops"] == 1
