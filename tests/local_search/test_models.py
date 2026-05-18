"""Tests for local search models."""

import pytest

from src.local_search.models import SearchResult, SearchQuery, SourceType


class TestSourceType:
    def test_all_sources(self):
        assert SourceType.MISSION == "mission"
        assert SourceType.TEMPLATE == "template"
        assert SourceType.SKILL == "skill"
        assert SourceType.LOG == "log"
        assert SourceType.REPORT == "report"
        assert SourceType.DOC == "doc"
        assert SourceType.SCRIPT == "script"


class TestSearchResult:
    def test_minimal(self):
        r = SearchResult(
            source_type=SourceType.MISSION,
            source_path="missions/M1/brief.md",
            title="Mission 1 Brief",
            snippet="This is a mission brief.",
        )
        assert r.source_type == SourceType.MISSION
        assert r.score == 0.0
        assert r.tags == []

    def test_to_dict(self):
        r = SearchResult(
            source_type=SourceType.TEMPLATE,
            source_path="templates/t1.json",
            title="Template 1",
            snippet="Template content",
            score=4.5,
            tags=["carrossel", "instagram"],
            mission_id="MIS-001",
        )
        d = r.to_dict()
        assert d["source_type"] == "template"
        assert d["score"] == 4.5
        assert d["tags"] == ["carrossel", "instagram"]
        assert d["mission_id"] == "MIS-001"


class TestSearchQuery:
    def test_single_term(self):
        q = SearchQuery(query="carrossel")
        assert q.terms == ["carrossel"]

    def test_multi_term(self):
        q = SearchQuery(query="campanha hoteis nordeste")
        assert q.terms == ["campanha", "hoteis", "nordeste"]

    def test_short_words_filtered(self):
        q = SearchQuery(query="a b c de")
        assert q.terms == ["de"]

    def test_defaults(self):
        q = SearchQuery(query="test")
        assert q.max_results == 20
        assert q.min_score == 0.0
        assert q.source_types == []
