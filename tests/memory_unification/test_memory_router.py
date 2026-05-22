"""Tests for MemoryRouter — unified query across memory sources."""
from __future__ import annotations

import pytest

from src.memory_unification.memory_router import (
    MemoryRouter,
    MemoryChunk,
    MemoryQueryResult,
    MOCK_MEMORY,
)


class TestMemoryChunk:
    def test_chunk_defaults(self):
        chunk = MemoryChunk(source="akasha", content="Test")
        assert chunk.chunk_id.startswith("mem_")
        assert chunk.relevance == 0.0
        assert chunk.source == "akasha"

    def test_chunk_to_dict(self):
        chunk = MemoryChunk(
            source="biblioteca",
            content="Insight valioso",
            relevance=0.85,
            metadata={"type": "insight", "livro": "StoryBrand"},
        )
        d = chunk.to_dict()
        assert d["source"] == "biblioteca"
        assert d["relevance"] == 0.85
        assert d["metadata"]["type"] == "insight"


class TestMemoryQueryResult:
    def test_empty_result(self):
        result = MemoryQueryResult(query="test")
        assert result.top_hooks == []
        assert result.saturated_themes == []
        assert result.insights == []

    def test_extracts_hooks(self):
        result = MemoryQueryResult(query="viagem", chunks=[
            MemoryChunk(source="akasha", content="Hook 1", metadata={"type": "hook"}),
            MemoryChunk(source="akasha", content="Hook 2", metadata={"type": "hook"}),
            MemoryChunk(source="qdrant", content="Not a hook", metadata={"type": "saturated_theme"}),
        ])
        assert len(result.top_hooks) == 2
        assert "Hook 1" in result.top_hooks
        assert "Hook 2" in result.top_hooks

    def test_extracts_saturated_themes(self):
        result = MemoryQueryResult(query="viagem", chunks=[
            MemoryChunk(source="qdrant", content="Tema saturado", metadata={"type": "saturated_theme"}),
        ])
        assert len(result.saturated_themes) == 1

    def test_extracts_viral_patterns(self):
        result = MemoryQueryResult(query="viagem", chunks=[
            MemoryChunk(source="qdrant", content="Pattern viral", metadata={"type": "viral_pattern"}),
        ])
        assert len(result.viral_patterns) == 1

    def test_extracts_insights(self):
        result = MemoryQueryResult(query="viagem", chunks=[
            MemoryChunk(source="biblioteca", content="Insight", metadata={"type": "insight"}),
            MemoryChunk(source="obsidian", content="Nota", metadata={"type": "insight"}),
        ])
        assert len(result.insights) == 2

    def test_to_dict_includes_properties(self):
        result = MemoryQueryResult(query="viagem", chunks=[
            MemoryChunk(source="akasha", content="H", metadata={"type": "hook"}),
            MemoryChunk(source="biblioteca", content="I", metadata={"type": "insight"}),
        ])
        d = result.to_dict()
        assert "top_hooks" in d
        assert "insights" in d
        assert "saturated_themes" in d
        assert len(d["top_hooks"]) == 1


class TestMemoryRouter:
    def test_router_defaults_to_dry_run(self):
        router = MemoryRouter()
        assert router.dry_run is True

    def test_query_mock_returns_results(self):
        router = MemoryRouter(dry_run=True)
        result = router.query("viagem em família")
        assert len(result.chunks) > 0
        assert result.sources_queried == ["akasha", "qdrant", "biblioteca", "obsidian"]
        assert result.total_time_ms >= 0

    def test_query_mock_matches_keywords(self):
        router = MemoryRouter(dry_run=True)
        result = router.query("hotel fazenda interior SP")
        assert len(result.chunks) > 0
        # "hotel" should match the "hotel" niche
        assert any("hotel" in c.metadata.get("niche", "") for c in result.chunks)

    def test_query_mock_fallback_when_no_match(self):
        router = MemoryRouter(dry_run=True)
        result = router.query("tópico completamente aleatório que não existe")
        assert len(result.chunks) > 0  # fallback returns generic results

    def test_query_respects_top_k(self):
        router = MemoryRouter(dry_run=True)
        result = router.query("viagem", top_k=2)
        assert len(result.chunks) <= 2

    def test_query_logs_queries(self):
        router = MemoryRouter(dry_run=True)
        router.query("test A")
        router.query("test B")
        assert len(router.queries) == 2

    def test_query_natal_returns_obsidian_notes(self):
        router = MemoryRouter(dry_run=True)
        result = router.query("natal rn")
        obsidian_chunks = [c for c in result.chunks if c.source == "obsidian"]
        assert len(obsidian_chunks) >= 1

    def test_query_with_specific_sources(self):
        router = MemoryRouter(dry_run=True)
        result = router.query("viagem", sources=["akasha", "biblioteca"])
        assert "qdrant" not in result.sources_queried
        assert "obsidian" not in result.sources_queried

    def test_mock_memory_has_all_niches(self):
        niches = list(MOCK_MEMORY.keys())
        assert "viagem" in niches
        assert "família" in niches
        assert "gastronomia" in niches
        assert "hotel" in niches
        assert "natal rn" in niches

    def test_mock_memory_chunks_have_metadata_types(self):
        for niche, chunks in MOCK_MEMORY.items():
            for chunk in chunks:
                assert "type" in chunk.metadata, f"{niche} chunk missing type"
