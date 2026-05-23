"""Tests for MemoryContextBuilder — 02_context_used.md generation."""
from __future__ import annotations

import pytest

from src.memory.context_builder import MemoryContextBuilder, ContextResult


class TestMemoryContextBuilder:
    def test_build_minimal_returns_context(self):
        builder = MemoryContextBuilder(dry_run=True)
        result = builder.build_minimal(
            mission_id="test-001",
            intent="create_campaign",
            sector="midia",
            account_handle="afamiliatigrereal",
        )
        assert isinstance(result, ContextResult)
        assert result.mission_id == "test-001"
        assert result.account_handle == "afamiliatigrereal"
        assert len(result.context_markdown) > 0
        assert "Contexto Usado" in result.context_markdown
        assert result.dry_run is True

    def test_build_full_returns_context_with_similar(self):
        builder = MemoryContextBuilder(dry_run=True)
        result = builder.build(
            mission_id="test-002",
            intent="create_campaign",
            sector="midia",
            account_handle="lucastigrereal",
            tags=["hotel", "natal"],
        )
        assert isinstance(result, ContextResult)
        assert len(result.context_markdown) > 0
        assert "Fontes consultadas" in result.context_markdown
        assert "Hits relevantes" in result.context_markdown

    def test_build_captures_metrics(self):
        builder = MemoryContextBuilder(dry_run=True)
        result = builder.build(
            mission_id="test-003",
            intent="create_campaign",
            sector="midia",
            account_handle="oinatalrn",
        )
        assert result.hits_count >= 0
        assert result.top_relevance != ""
        assert isinstance(result.sources_used, list)

    def test_invalid_intent_returns_empty_context(self):
        builder = MemoryContextBuilder(dry_run=True)
        result = builder.build_minimal(
            mission_id="test-004",
            intent="invalid_intent",
            sector="invalid_sector",
        )
        assert len(result.context_markdown) > 0
        assert "Contexto Usado" in result.context_markdown

    def test_to_dict(self):
        result = ContextResult(
            mission_id="test",
            account_handle="afamiliatigrereal",
            intent="create_campaign",
            sector="midia",
            context_markdown="# Test",
            sources_used=["akasha", "session"],
            hits_count=3,
        )
        d = result.to_dict()
        assert d["mission_id"] == "test"
        assert d["hits_count"] == 3
        assert d["sources_used"] == ["akasha", "session"]

    def test_build_markdown_includes_optional_similarity_and_patterns(self):
        builder = MemoryContextBuilder(dry_run=True)

        md = builder._build_markdown(
            mission_id="test-005",
            account_handle="oinatalrn",
            intent="create_campaign",
            sector="midia",
            pack_hits=[
                {
                    "title": "Natal performa bem em reels",
                    "relevance": "high",
                    "snippet": "Use praia e familia no gancho.",
                    "source_type": "akasha",
                }
            ],
            assembled_text="Texto consolidado de campanha.",
            source_summary={"akasha": 1},
            similar_missions=[
                {
                    "source_mission": {"title": "Campanha Ponta Negra"},
                    "similarity_score": 0.82,
                    "relevant_learnings": ["Gancho com praia aumenta saves"],
                }
            ],
            patterns={
                "sample_count": 2,
                "successful_hooks": ["Praia ao amanhecer"],
                "insights": ["Familia gera comentarios"],
            },
        )

        assert "### [akasha:high] Natal performa bem em reels" in md
        assert "> Use praia e familia no gancho." in md
        assert "## Texto consolidado" in md
        assert "## Missoes similares" in md
        assert "- [82%] Campanha Ponta Negra" in md
        assert "## Padroes detectados" in md
        assert "- Hook: Praia ao amanhecer" in md
        assert "- Insight: Familia gera comentarios" in md
