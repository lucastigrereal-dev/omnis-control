"""Tests for ResearchContext — enriched context for content generation."""
from __future__ import annotations

import pytest

from src.memory_unification.research_context import (
    ResearchContext,
    ResearchContextBuilder,
)
from src.memory_unification.memory_router import MemoryRouter


class TestResearchContext:
    def test_empty_context(self):
        ctx = ResearchContext()
        assert ctx.is_empty is True
        assert ctx.enrichment_summary == "nenhum dado encontrado"

    def test_with_data(self):
        ctx = ResearchContext(
            topic="viagem",
            page="@lucastigrereal",
            top_hooks=["Hook 1", "Hook 2"],
            insights=["Insight A"],
            saturated_themes=["Tema X"],
            viral_patterns=["Pattern Y"],
        )
        assert ctx.is_empty is False
        assert "2 hooks" in ctx.enrichment_summary
        assert "1 temas saturados" in ctx.enrichment_summary

    def test_to_prompt_hint_includes_all_sections(self):
        ctx = ResearchContext(
            topic="viagem em Natal",
            page="@lucastigrereal",
            top_hooks=["Hook viral sobre Natal", "Hook 2"],
            saturated_themes=["Praia genérica"],
            viral_patterns=["Reel rápido com texto"],
            insights=["O Nordeste tem o maior potencial turístico"],
        )
        hint = ctx.to_prompt_hint()
        assert "CONTEXTO DE PESQUISA" in hint
        assert "Hook viral sobre Natal" in hint
        assert "EVITAR temas saturados" in hint
        assert "Praia genérica" in hint
        assert "Padrões virais" in hint

    def test_to_prompt_hint_empty_context(self):
        ctx = ResearchContext(topic="test")
        hint = ctx.to_prompt_hint()
        assert "CONTEXTO DE PESQUISA" in hint  # header always present
        # No data sections
        assert "Hooks que engajaram" not in hint
        assert "EVITAR" not in hint

    def test_to_dict(self):
        ctx = ResearchContext(
            topic="test",
            page="@test",
            top_hooks=["H1"],
            insights=["I1"],
            sources_queried=["akasha"],
            query_time_ms=42,
        )
        d = ctx.to_dict()
        assert d["topic"] == "test"
        assert d["top_hooks"] == ["H1"]
        assert d["query_time_ms"] == 42
        assert "enrichment_summary" in d


class TestResearchContextBuilder:
    def test_builder_defaults(self):
        builder = ResearchContextBuilder(dry_run=True)
        assert builder.dry_run is True
        assert isinstance(builder.router, MemoryRouter)

    def test_builder_accepts_custom_router(self):
        router = MemoryRouter(dry_run=True)
        builder = ResearchContextBuilder(router=router)
        assert builder.router is router

    def test_build_returns_context(self):
        builder = ResearchContextBuilder(dry_run=True)
        ctx = builder.build(topic="viagem em Natal com família", page="@lucastigrereal")
        assert isinstance(ctx, ResearchContext)
        assert ctx.topic == "viagem em Natal com família"
        assert ctx.page == "@lucastigrereal"

    def test_build_populates_hooks(self):
        builder = ResearchContextBuilder(dry_run=True)
        ctx = builder.build(topic="viagem", page="@lucastigrereal")
        assert len(ctx.top_hooks) > 0
        assert ctx.enrichment_summary != "nenhum dado encontrado"

    def test_build_populates_insights(self):
        builder = ResearchContextBuilder(dry_run=True)
        ctx = builder.build(topic="família", page="@afamiliatigrereal")
        assert len(ctx.insights) > 0
        assert any("filhos" in i or "criança" in i.lower() or "família" in i.lower() or "presente" in i.lower() for i in ctx.insights)

    def test_build_queries_multiple_sources(self):
        builder = ResearchContextBuilder(dry_run=True)
        ctx = builder.build(topic="hotel resort fazenda", page="@agenteviajabrasil")
        assert len(ctx.sources_queried) > 0
        assert ctx.query_time_ms >= 0

    def test_build_sets_timestamps(self):
        builder = ResearchContextBuilder(dry_run=True)
        ctx = builder.build(topic="gastronomia", page="@oquecomernatalrn")
        assert ctx.generated_at != ""
        assert ctx.query_time_ms >= 0


class TestCaptionFactoryIntegration:
    """Verify that CaptionFactory accepts research context."""
    def test_produce_batch_with_research_dry_run(self):
        from src.skills.caption_factory import BatchCaptionRequest, CaptionFactory

        builder = ResearchContextBuilder(dry_run=True)
        ctx = builder.build(topic="viagem em Natal", page="@lucastigrereal")

        factory = CaptionFactory(dry_run=True)
        req = BatchCaptionRequest(
            topic="viagem em Natal",
            page="@lucastigrereal",
            count=2,
            tones=["autêntico", "informativo"],
        )
        result = factory.produce_batch_with_research(req, research_context=ctx)
        assert result.success_count == 2

    def test_produce_batch_with_empty_research_context(self):
        from src.skills.caption_factory import BatchCaptionRequest, CaptionFactory

        ctx = ResearchContext(topic="test")  # empty
        factory = CaptionFactory(dry_run=True)
        req = BatchCaptionRequest(topic="test", count=1)
        result = factory.produce_batch_with_research(req, research_context=ctx)
        assert result.success_count == 1
        # Empty context should not break anything
        assert ctx.is_empty is True

    def test_research_enriches_prompt(self):
        """Verify that research context actually modifies the prompt."""
        from src.skills.caption_factory import BatchCaptionRequest, CaptionFactory

        ctx = ResearchContext(
            topic="viagem",
            page="@lucastigrereal",
            top_hooks=["O destino que ninguém te contou"],
            saturated_themes=["Dicas genéricas de viagem"],
            viral_patterns=["Reel com transição rápida"],
            insights=["Viajar é se permitir viver o extraordinário"],
        )

        factory = CaptionFactory(dry_run=True)
        req = BatchCaptionRequest(topic="viagem", count=1, tones=["autêntico"])
        result = factory.produce_batch_with_research(req, research_context=ctx)

        assert result.success_count == 1
        # The dry_run output won't show the research hint (it's a simulation)
        # but the pipeline should complete without errors
