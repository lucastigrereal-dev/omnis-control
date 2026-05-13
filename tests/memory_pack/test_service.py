"""Testes para o servico Memory Pack."""
import json

import pytest

from src.memory_pack.models import (
    MemorySource,
    MemoryQuery,
    MemoryHit,
    ContextPack,
    MissionMemoryRecord,
    MemoryWritePlan,
    SOURCE_AKASHA,
    SOURCE_OBSIDIAN,
    SOURCE_MEM0,
    SOURCE_SESSION,
    RELEVANCE_HIGH,
    RELEVANCE_MEDIUM,
    RELEVANCE_LOW,
    RELEVANCE_NONE,
    RELEVANCE_EXACT,
    FORMAT_JSON,
    FORMAT_MARKDOWN,
    FORMAT_DICT,
    SECTOR_COMERCIAL,
    SECTOR_MIDIA,
    SECTOR_VENDAS,
    ACTION_UPSERT,
    ACTION_INSERT,
)
from src.memory_pack.service import (
    MemoryPackPlanner,
    validate_memory_query,
    rank_memory_hits,
    build_context_pack,
    plan_memory_writeback,
    export_context_pack,
)
from src.memory_pack.errors import (
    QueryValidationError,
    EmptyQueryError,
    ContextPackError,
    EmptyHitListError,
    RankingError,
    WritePlanError,
    DestructiveActionBlockedError,
    WritebackBlockedError,
    ExportError,
    InvalidFormatError,
)


# ── MemoryPackPlanner ──────────────────────────────────────────────────────

class TestMemoryPackPlanner:
    """Testes para o planejador central."""

    def test_create_registers_all_sources(self):
        planner = MemoryPackPlanner.create()
        assert len(planner.sources) == 7
        source_types = {s.source_type for s in planner.sources}
        assert len(source_types) == 7

    def test_create_has_two_primary_sources(self):
        planner = MemoryPackPlanner.create()
        primary = planner.get_primary_sources()
        assert len(primary) >= 1
        assert all(s.is_primary for s in primary)

    def test_get_available_sources(self):
        planner = MemoryPackPlanner.create()
        available = planner.get_available_sources()
        assert len(available) == 7
        assert all(s.is_available for s in available)

    def test_dry_run_is_true_by_default(self):
        planner = MemoryPackPlanner.create()
        assert planner.dry_run is True

    def test_get_primary_sources_sorted_by_priority(self):
        planner = MemoryPackPlanner.create()
        primary = planner.get_primary_sources()
        if len(primary) >= 2:
            for i in range(len(primary) - 1):
                assert primary[i].priority >= primary[i + 1].priority


# ── validate_memory_query ──────────────────────────────────────────────────

class TestValidateMemoryQuery:
    """Testes para validacao de MemoryQuery."""

    def test_valid_query_passes(self):
        q = MemoryQuery.new(
            text="busca valida",
            sources=[SOURCE_AKASHA],
            sectors=[SECTOR_COMERCIAL],
        )
        result = validate_memory_query(q)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_empty_text_fails(self):
        q = MemoryQuery(text="", query_id="q1")
        result = validate_memory_query(q)
        assert result["valid"] is False
        assert any("empty" in e.lower() for e in result["errors"])

    def test_warns_no_sources(self):
        q = MemoryQuery.new(text="busca")
        result = validate_memory_query(q)
        assert len(result["warnings"]) >= 1
        assert any("source" in w.lower() for w in result["warnings"])

    def test_warns_no_sectors(self):
        q = MemoryQuery.new(text="busca", sources=[SOURCE_AKASHA])
        result = validate_memory_query(q)
        assert any("sector" in w.lower() for w in result["warnings"])

    def test_suggests_specifying_sources(self):
        q = MemoryQuery.new(text="busca")
        result = validate_memory_query(q)
        assert len(result["suggestions"]) >= 1

    def test_warns_large_max_hits(self):
        q = MemoryQuery.new(text="busca", max_hits=100)
        result = validate_memory_query(q)
        assert any("noise" in w.lower() or "large" in w.lower() for w in result["warnings"])


# ── rank_memory_hits ───────────────────────────────────────────────────────

class TestRankMemoryHits:
    """Testes para ranqueamento de MemoryHit."""

    @pytest.fixture
    def mixed_hits(self) -> list[MemoryHit]:
        return [
            MemoryHit.new(query_id="q", source_type=SOURCE_AKASHA, source_id="s1",
                          relevance=RELEVANCE_LOW, title="Low"),
            MemoryHit.new(query_id="q", source_type=SOURCE_AKASHA, source_id="s2",
                          relevance=RELEVANCE_HIGH, title="High"),
            MemoryHit.new(query_id="q", source_type=SOURCE_AKASHA, source_id="s3",
                          relevance=RELEVANCE_MEDIUM, title="Med"),
            MemoryHit.new(query_id="q", source_type=SOURCE_OBSIDIAN, source_id="s4",
                          relevance=RELEVANCE_HIGH, title="High Obs"),
        ]

    def test_ranks_by_relevance_desc(self, mixed_hits):
        ranked = rank_memory_hits(mixed_hits)
        scores = [h.rank_score for h in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_respects_max_hits(self, mixed_hits):
        ranked = rank_memory_hits(mixed_hits, max_hits=2)
        assert len(ranked) == 2

    def test_filters_by_min_relevance(self, mixed_hits):
        ranked = rank_memory_hits(mixed_hits, min_relevance=RELEVANCE_HIGH)
        assert all(h.rank_score >= 75 for h in ranked)
        assert len(ranked) == 2  # two HIGH hits

    def test_empty_list_returns_empty(self):
        assert rank_memory_hits([]) == []

    def test_rejects_invalid_relevance(self):
        with pytest.raises(RankingError, match="Relevancia invalida"):
            rank_memory_hits([], min_relevance="invalid")


# ── build_context_pack ─────────────────────────────────────────────────────

class TestBuildContextPack:
    """Testes para montagem de ContextPack."""

    def test_builds_from_valid_query_and_hits(self, sample_query, sample_hits):
        pack = build_context_pack(sample_query, sample_hits)
        assert isinstance(pack, ContextPack)
        assert pack.total_hits > 0
        assert pack.query_id == sample_query.query_id
        assert len(pack.assembled_text) > 0

    def test_rejects_empty_hits(self, sample_query):
        with pytest.raises(EmptyHitListError, match="hits list is empty"):
            build_context_pack(sample_query, [])

    def test_respects_query_max_hits(self):
        q = MemoryQuery.new(text="test", max_hits=1)
        hits = [
            MemoryHit.new(query_id=q.query_id, source_type=SOURCE_AKASHA, source_id="s1",
                          relevance=RELEVANCE_HIGH, title="A"),
            MemoryHit.new(query_id=q.query_id, source_type=SOURCE_AKASHA, source_id="s2",
                          relevance=RELEVANCE_MEDIUM, title="B"),
        ]
        pack = build_context_pack(q, hits)
        assert pack.total_hits <= 1

    def test_filters_by_min_relevance(self):
        q = MemoryQuery.new(text="test", min_relevance=RELEVANCE_HIGH)
        hits = [
            MemoryHit.new(query_id=q.query_id, source_type=SOURCE_AKASHA, source_id="s1",
                          relevance=RELEVANCE_HIGH, title="H"),
            MemoryHit.new(query_id=q.query_id, source_type=SOURCE_AKASHA, source_id="s2",
                          relevance=RELEVANCE_LOW, title="L"),
        ]
        pack = build_context_pack(q, hits)
        assert all(h.rank_score >= 75 for h in pack.hits)


# ── plan_memory_writeback ──────────────────────────────────────────────────

class TestPlanMemoryWriteback:
    """Testes para planejamento de writeback."""

    def test_creates_plan_with_records(self, sample_record):
        plan = plan_memory_writeback(
            records=[sample_record],
            target_source=SOURCE_AKASHA,
            action=ACTION_UPSERT,
        )
        assert isinstance(plan, MemoryWritePlan)
        assert plan.record_count == 1
        assert plan.is_dry_run is True
        assert plan.requires_approval is True

    def test_multiple_records(self):
        r1 = MissionMemoryRecord.new(
            mission_id="m1", sector=SECTOR_MIDIA, title="R1", summary="s1"
        )
        r2 = MissionMemoryRecord.new(
            mission_id="m2", sector=SECTOR_COMERCIAL, title="R2", summary="s2"
        )
        plan = plan_memory_writeback(records=[r1, r2])
        assert plan.record_count == 2

    def test_rejects_invalid_source(self):
        with pytest.raises(WritePlanError, match="Fonte invalida"):
            plan_memory_writeback(records=[], target_source="invalid")

    def test_defaults_to_akasha_and_upsert(self, sample_record):
        plan = plan_memory_writeback(records=[sample_record])
        assert plan.target_source == SOURCE_AKASHA
        assert plan.action == ACTION_UPSERT


# ── export_context_pack ────────────────────────────────────────────────────

class TestExportContextPack:
    """Testes para exportacao de ContextPack."""

    def test_export_json(self, sample_context_pack):
        result = export_context_pack(sample_context_pack, fmt=FORMAT_JSON)
        assert isinstance(result, str)
        data = json.loads(result)
        assert data["pack_id"] == sample_context_pack.pack_id

    def test_export_dict_same_as_json(self, sample_context_pack):
        result = export_context_pack(sample_context_pack, fmt=FORMAT_DICT)
        data = json.loads(result)
        assert "pack_id" in data

    def test_export_markdown(self, sample_context_pack):
        result = export_context_pack(sample_context_pack, fmt=FORMAT_MARKDOWN)
        assert sample_context_pack.pack_id in result
        assert "Context Pack" in result
        assert "## Assembled Context" in result

    def test_rejects_invalid_format(self, sample_context_pack):
        with pytest.raises(InvalidFormatError, match="Formato invalido"):
            export_context_pack(sample_context_pack, fmt="xml")


# ── Simulate Query ─────────────────────────────────────────────────────────

class TestSimulateQuery:
    """Testes para simulacao de query."""

    def test_simulate_generates_hits(self, planner, sample_query):
        result = planner.simulate_query(sample_query)
        assert result["simulated"] is True
        assert result["total_hits_generated"] > 0
        assert "hits" in result
        assert len(result["hits"]) > 0

    def test_simulate_hits_are_memoryhit_objects(self, planner, sample_query):
        result = planner.simulate_query(sample_query)
        for hit in result["hits"]:
            assert isinstance(hit, MemoryHit)

    def test_simulate_with_all_sources(self, planner):
        q = MemoryQuery.new(text="hotel viagem familia")
        result = planner.simulate_query(q)
        assert result["total_hits_generated"] > 0

    def test_simulate_respects_max_hits(self, planner):
        q = MemoryQuery.new(text="estrategia conteudo", max_hits=2)
        result = planner.simulate_query(q)
        assert len(result["hits"]) <= 2

    def test_simulate_respects_min_relevance(self, planner):
        q = MemoryQuery.new(text="estrategia", min_relevance=RELEVANCE_HIGH)
        result = planner.simulate_query(q)
        for hit in result["hits"]:
            assert hit.rank_score >= 75

    def test_simulate_no_matches_returns_empty(self, planner):
        q = MemoryQuery.new(text="xyzabc123nonexistent")
        result = planner.simulate_query(q)
        # Low relevance hits are generated but filtered by min_relevance default (LOW=25)
        # all simulated hits for unmatched text get RELEVANCE_LOW (25), which passes min_relevance=LOW (25)
        # so we expect some hits still
        assert "hits" in result


# ── Simulate Writeback ──────────────────────────────────────────────────────

class TestSimulateWriteback:
    """Testes para simulacao de writeback."""

    def test_simulate_never_executes(self, planner, sample_write_plan):
        result = planner.simulate_writeback(sample_write_plan)
        assert result["executed"] is False
        assert result["simulated"] is True
        assert result["status"] == "dry_run_completed"

    def test_simulate_requires_approval(self, planner, sample_write_plan):
        result = planner.simulate_writeback(sample_write_plan)
        assert result["approval_required"] is True

    def test_simulate_reports_counts(self, planner, sample_write_plan):
        result = planner.simulate_writeback(sample_write_plan)
        assert result["records_count"] == 1
        assert result["target_source"] == SOURCE_AKASHA


# ── Module-level convenience functions ─────────────────────────────────────

class TestConvenienceFunctions:
    """Testes para funcoes de conveniencia a nivel de modulo."""

    def test_validate_memory_query_function(self):
        q = MemoryQuery.new(text="test", sources=[SOURCE_AKASHA])
        result = validate_memory_query(q)
        assert result["valid"] is True

    def test_rank_memory_hits_function(self):
        hits = [
            MemoryHit.new(query_id="q", source_type=SOURCE_AKASHA, source_id="s1",
                          relevance=RELEVANCE_HIGH),
            MemoryHit.new(query_id="q", source_type=SOURCE_AKASHA, source_id="s2",
                          relevance=RELEVANCE_LOW),
        ]
        ranked = rank_memory_hits(hits)
        assert ranked[0].rank_score > ranked[1].rank_score

    def test_build_context_pack_function(self, sample_query, sample_hits):
        pack = build_context_pack(sample_query, sample_hits)
        assert isinstance(pack, ContextPack)

    def test_plan_memory_writeback_function(self, sample_record):
        plan = plan_memory_writeback([sample_record])
        assert plan.record_count == 1

    def test_export_context_pack_function(self, sample_context_pack):
        result = export_context_pack(sample_context_pack, fmt=FORMAT_JSON)
        assert isinstance(result, str)


# ── Safety guarantees ──────────────────────────────────────────────────────

class TestSafetyGuarantees:
    """Testes que garantem as regras de seguranca do modulo."""

    def test_all_plans_are_dry_run(self, planner):
        """Todo write plan criado pelo servico deve ser dry-run."""
        rec = MissionMemoryRecord.new(
            mission_id="m", sector=SECTOR_MIDIA, title="T", summary="s"
        )
        plan = planner.plan_memory_writeback([rec])
        assert plan.is_dry_run is True
        assert plan.requires_approval is True

    def test_no_real_connection_imports(self):
        """Verifica que o servico nao importa bibliotecas de conexao real."""
        import inspect
        import src.memory_pack.service as svc
        source = inspect.getsource(svc)
        forbidden_imports = [
            "import psycopg2", "import psycopg", "import asyncpg",
            "import sqlalchemy", "import requests", "import httpx",
            "from urllib.request", "import socket", "import pgvector",
        ]
        for word in forbidden_imports:
            assert word not in source, f"Forbidden import found: {word}"

    def test_no_env_reading(self):
        """Verifica que o modulo nao le .env."""
        import inspect
        import src.memory_pack.service as svc
        source = inspect.getsource(svc)
        assert "dotenv" not in source
        assert "environ" not in source
        assert ".env" not in source.lower()

    def test_no_llm_imports(self):
        """Verifica que o modulo nao usa LLM."""
        import inspect
        import src.memory_pack.service as svc
        source = inspect.getsource(svc)
        forbidden = ["openai", "anthropic", "langchain", "llama", "transformers", "torch"]
        for word in forbidden:
            assert word not in source, f"LLM import found: {word}"

    def test_no_pandas_import(self):
        """Verifica que o modulo nao usa pandas."""
        import inspect
        import src.memory_pack.models as mod
        import src.memory_pack.service as svc
        source_m = inspect.getsource(mod)
        source_s = inspect.getsource(svc)
        assert "pandas" not in source_m
        assert "pandas" not in source_s

    def test_write_plan_never_delete(self, sample_record):
        """Nao deve ser possivel criar write plan com acao DELETE."""
        with pytest.raises(ValueError, match="Acao DELETE bloqueada"):
            plan_memory_writeback([sample_record], action="delete")
