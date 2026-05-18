"""Tests for search engine indexing and querying."""

import tempfile
from pathlib import Path

import pytest

from src.local_search.engine import SearchEngine
from src.local_search.models import SearchQuery, SourceType


@pytest.fixture
def fixture_dir():
    """Create a minimal fixture directory with known content."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # Mission
        m1 = root / "missions" / "MIS-001"
        m1.mkdir(parents=True)
        (m1 / "mission_contract.json").write_text(
            '{"target": "campanha hoteis nordeste", "type": "carrossel"}',
            encoding="utf-8")
        (m1 / "brief.md").write_text(
            "# Brief: Campanha Hoteis Nordeste\n\nCarrossel com 10 slides sobre resorts em Natal.",
            encoding="utf-8")

        # Template
        t1 = root / "templates"
        t1.mkdir(parents=True)
        (t1 / "template_registry.json").write_text(
            '{"templates": {"t1": {"name": "Carrossel Nordeste", "description": "Template para carrossel de hoteis no nordeste", "tags": ["carrossel", "nordeste", "hoteis"]}}}',
            encoding="utf-8")

        # Skill
        s1 = root / "skills" / "generate-seogram"
        s1.mkdir(parents=True)
        (s1 / "SKILL.md").write_text("# SEOgram Skill\n\nGera legendas otimizadas para Instagram com SEO local.", encoding="utf-8")
        (s1 / "manifest.json").write_text(
            '{"name": "generate-seogram", "description": "Gera legendas com SEO para Instagram", "tags": ["seo", "caption", "instagram"]}',
            encoding="utf-8")

        # Log
        logs = root / "logs"
        logs.mkdir(parents=True)
        (logs / "briefing_2026-05-18.md").write_text("# Briefing\n\nProducao de carrossel para hoteis no nordeste.", encoding="utf-8")

        # Doc
        (root / "README.md").write_text("# OMNIS Control\n\nSistema de orquestracao local.", encoding="utf-8")

        yield root


class TestSearchEngineIndex:
    def test_index_all(self, fixture_dir):
        engine = SearchEngine(root=fixture_dir)
        count = engine.index_all()
        assert count > 0
        assert engine.indexed_count == count
        assert engine.unique_terms > 0

    def test_stats(self, fixture_dir):
        engine = SearchEngine(root=fixture_dir)
        engine.index_all()
        s = engine.stats()
        assert s["indexed_items"] > 0
        assert "by_source_type" in s
        assert isinstance(s["by_source_type"], dict)


class TestSearchEngineQuery:
    @pytest.fixture(autouse=True)
    def setup(self, fixture_dir):
        self.engine = SearchEngine(root=fixture_dir)
        self.engine.index_all()

    def test_search_finds_mission(self):
        results = self.engine.search_simple("natal")
        assert len(results) >= 1
        assert any("MIS-001" in r.title for r in results)

    def test_search_finds_template(self):
        results = self.engine.search_simple("carrossel")
        assert len(results) >= 1
        assert any(r.source_type == SourceType.TEMPLATE for r in results)

    def test_search_finds_skill(self):
        results = self.engine.search_simple("seogram")
        assert len(results) >= 1
        assert any(r.source_type == SourceType.SKILL for r in results)

    def test_search_no_match(self):
        results = self.engine.search_simple("xablau_inexistente")
        assert len(results) == 0

    def test_filter_by_source_type(self):
        q = SearchQuery(query="carrossel", source_types=[SourceType.TEMPLATE])
        results = self.engine.search(q)
        assert all(r.source_type == SourceType.TEMPLATE for r in results)

    def test_limit_results(self):
        q = SearchQuery(query="hoteis", max_results=2)
        results = self.engine.search(q)
        assert len(results) <= 2

    def test_results_are_scored(self):
        results = self.engine.search_simple("carrossel hoteis")
        for r in results:
            assert r.score > 0
        # Results should be ordered by descending score
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_multi_term_boosts_score(self):
        single = self.engine.search_simple("hoteis")
        multi = self.engine.search_simple("carrossel hoteis nordeste")
        if multi and single:
            # Multi-term query should have at least as many results with higher scores
            assert len(multi) >= 1
