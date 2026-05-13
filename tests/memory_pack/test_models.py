"""Testes para modelos do Memory Pack."""
import json

import pytest

from src.memory_pack.models import (
    MemorySource,
    MemoryQuery,
    MemoryHit,
    ContextPack,
    MissionMemoryRecord,
    MemoryWritePlan,
    MemorySourceType,
    SOURCE_AKASHA,
    SOURCE_OBSIDIAN,
    SOURCE_MEM0,
    SOURCE_GRINGOTTS,
    SOURCE_BIBLIOTECA,
    SOURCE_SESSION,
    SOURCE_STATIC,
    VALID_SOURCES,
    VALID_SECTORS,
    VALID_RELEVANCES,
    VALID_FORMATS,
    VALID_WRITE_ACTIONS,
    VALID_RECORD_STATUSES,
    RELEVANCE_RANK,
    RELEVANCE_EXACT,
    RELEVANCE_HIGH,
    RELEVANCE_MEDIUM,
    RELEVANCE_LOW,
    RELEVANCE_NONE,
    FORMAT_JSON,
    FORMAT_MARKDOWN,
    FORMAT_DICT,
    ACTION_INSERT,
    ACTION_UPDATE,
    ACTION_UPSERT,
    ACTION_DELETE,
    STATUS_DRAFT,
    STATUS_ACTIVE,
    STATUS_ARCHIVED,
    STATUS_SUPERSEDED,
    SECTOR_MIDIA,
    SECTOR_COMERCIAL,
    SECTOR_VENDAS,
    SECTOR_CONHECIMENTO,
    SECTOR_PRODUTO,
    SECTOR_FINANCEIRO,
    SECTOR_OPERACOES,
)
from src.memory_pack.errors import (
    SerializationError,
)


# ── Constants ───────────────────────────────────────────────────────────────

class TestConstants:
    """Valida integridade das constantes do modulo."""

    def test_all_sources_registered(self):
        """7 fontes de memoria registradas."""
        assert len(VALID_SOURCES) == 7
        assert SOURCE_AKASHA in VALID_SOURCES

    def test_all_sectors_registered(self):
        """7 setores JARVIS registrados."""
        assert len(VALID_SECTORS) == 7
        for s in [SECTOR_MIDIA, SECTOR_COMERCIAL, SECTOR_VENDAS, SECTOR_CONHECIMENTO,
                   SECTOR_PRODUTO, SECTOR_FINANCEIRO, SECTOR_OPERACOES]:
            assert s in VALID_SECTORS

    def test_all_relevances_registered(self):
        """5 niveis de relevancia registrados."""
        assert len(VALID_RELEVANCES) == 5

    def test_relevance_rank_monotonic(self):
        """Rank deve ser monotonicamente decrescente por nivel."""
        ranks = [
            RELEVANCE_RANK[RELEVANCE_EXACT],
            RELEVANCE_RANK[RELEVANCE_HIGH],
            RELEVANCE_RANK[RELEVANCE_MEDIUM],
            RELEVANCE_RANK[RELEVANCE_LOW],
            RELEVANCE_RANK[RELEVANCE_NONE],
        ]
        assert ranks == sorted(ranks, reverse=True)

    def test_all_formats_registered(self):
        """3 formatos de export."""
        assert len(VALID_FORMATS) == 3

    def test_all_write_actions_registered(self):
        """4 acoes de write."""
        assert len(VALID_WRITE_ACTIONS) == 4

    def test_all_record_statuses_registered(self):
        """4 status de registro."""
        assert len(VALID_RECORD_STATUSES) == 4

    def test_memory_source_type_enum_covers_all(self):
        """Enum MemorySourceType cobre todas as fontes."""
        enum_values = {e.value for e in MemorySourceType}
        assert enum_values == VALID_SOURCES


# ── MemorySource ────────────────────────────────────────────────────────────

class TestMemorySource:
    """Testes para o modelo MemorySource."""

    def test_new_creates_with_valid_data(self):
        src = MemorySource.new(
            source_type=SOURCE_AKASHA,
            label="Test Source",
            description="A test source",
            is_primary=True,
            priority=90,
        )
        assert src.source_type == SOURCE_AKASHA
        assert src.label == "Test Source"
        assert src.description == "A test source"
        assert src.is_primary is True
        assert src.priority == 90
        assert src.source_id.startswith("src_")
        assert src.created_at is not None

    def test_new_defaults(self):
        src = MemorySource.new(source_type=SOURCE_SESSION, label="Session")
        assert src.is_primary is False
        assert src.priority == 50
        assert src.is_available is True
        assert src.metadata == {}

    def test_new_rejects_invalid_source_type(self):
        with pytest.raises(ValueError, match="Tipo de fonte invalido"):
            MemorySource.new(source_type="invalid", label="Bad")

    def test_new_rejects_invalid_priority_low(self):
        with pytest.raises(ValueError, match="priority deve estar entre 0 e 100"):
            MemorySource.new(source_type=SOURCE_AKASHA, label="Bad", priority=-1)

    def test_new_rejects_invalid_priority_high(self):
        with pytest.raises(ValueError, match="priority deve estar entre 0 e 100"):
            MemorySource.new(source_type=SOURCE_AKASHA, label="Bad", priority=101)

    def test_new_accepts_priority_boundaries(self):
        """Priority 0 e 100 sao validos."""
        s0 = MemorySource.new(source_type=SOURCE_AKASHA, label="Min", priority=0)
        assert s0.priority == 0
        s100 = MemorySource.new(source_type=SOURCE_AKASHA, label="Max", priority=100)
        assert s100.priority == 100

    def test_to_dict_and_back(self):
        src = MemorySource.new(
            source_type=SOURCE_GRINGOTTS,
            label="Roundtrip",
            description="Test roundtrip",
            metadata={"key": "value"},
        )
        data = src.to_dict()
        restored = MemorySource.from_dict(data)
        assert restored.source_id == src.source_id
        assert restored.source_type == src.source_type
        assert restored.label == src.label
        assert restored.metadata == src.metadata


# ── MemoryQuery ─────────────────────────────────────────────────────────────

class TestMemoryQuery:
    """Testes para o modelo MemoryQuery."""

    def test_new_creates_with_valid_data(self):
        q = MemoryQuery.new(
            text="busca por hoteis em SP",
            sources=[SOURCE_AKASHA],
            sectors=[SECTOR_COMERCIAL],
            max_hits=5,
            min_relevance=RELEVANCE_MEDIUM,
        )
        assert q.text == "busca por hoteis em SP"
        assert q.sources == [SOURCE_AKASHA]
        assert q.sectors == [SECTOR_COMERCIAL]
        assert q.max_hits == 5
        assert q.min_relevance == RELEVANCE_MEDIUM
        assert q.dry_run is True
        assert q.query_id.startswith("qry_")

    def test_new_defaults(self):
        q = MemoryQuery.new(text="busca generica")
        assert q.sources == []
        assert q.sectors == []
        assert q.max_hits == 10
        assert q.min_relevance == RELEVANCE_LOW
        assert q.filters == {}

    def test_new_rejects_empty_text(self):
        with pytest.raises(ValueError, match="text da query nao pode ser vazio"):
            MemoryQuery.new(text="")

    def test_new_rejects_whitespace_text(self):
        with pytest.raises(ValueError, match="text da query nao pode ser vazio"):
            MemoryQuery.new(text="   ")

    def test_new_rejects_invalid_source(self):
        with pytest.raises(ValueError, match="Fontes invalidas"):
            MemoryQuery.new(text="test", sources=["invalid"])

    def test_new_rejects_invalid_sector(self):
        with pytest.raises(ValueError, match="Setores invalidos"):
            MemoryQuery.new(text="test", sectors=["invalid"])

    def test_new_rejects_invalid_relevance(self):
        with pytest.raises(ValueError, match="Relevancia invalida"):
            MemoryQuery.new(text="test", min_relevance="super_high")

    def test_new_rejects_zero_max_hits(self):
        with pytest.raises(ValueError, match="max_hits deve ser >= 1"):
            MemoryQuery.new(text="test", max_hits=0)

    def test_new_strips_text(self):
        q = MemoryQuery.new(text="  padded  ")
        assert q.text == "padded"

    def test_min_rank_property(self):
        q_high = MemoryQuery.new(text="test", min_relevance=RELEVANCE_HIGH)
        assert q_high.min_rank == RELEVANCE_RANK[RELEVANCE_HIGH]

    def test_to_dict_and_back(self):
        q = MemoryQuery.new(
            text="roundtrip test",
            sources=[SOURCE_AKASHA, SOURCE_OBSIDIAN],
            sectors=[SECTOR_MIDIA],
            max_hits=15,
        )
        data = q.to_dict()
        restored = MemoryQuery.from_dict(data)
        assert restored.query_id == q.query_id
        assert restored.text == q.text
        assert restored.sources == q.sources
        assert restored.dry_run is True


# ── MemoryHit ───────────────────────────────────────────────────────────────

class TestMemoryHit:
    """Testes para o modelo MemoryHit."""

    def test_new_creates_with_valid_data(self):
        hit = MemoryHit.new(
            query_id="qry_test",
            source_type=SOURCE_AKASHA,
            source_id="src_test",
            relevance=RELEVANCE_HIGH,
            title="Titulo",
            snippet="Resumo do conteudo...",
        )
        assert hit.query_id == "qry_test"
        assert hit.source_type == SOURCE_AKASHA
        assert hit.relevance == RELEVANCE_HIGH
        assert hit.rank_score == RELEVANCE_RANK[RELEVANCE_HIGH]
        assert hit.title == "Titulo"
        assert hit.hit_id.startswith("hit_")
        assert hit.chunk_id.startswith("chk_")

    def test_new_defaults(self):
        hit = MemoryHit.new(
            query_id="qry_test",
            source_type=SOURCE_SESSION,
            source_id="src_test",
        )
        assert hit.relevance == RELEVANCE_MEDIUM
        assert hit.rank_score == RELEVANCE_RANK[RELEVANCE_MEDIUM]
        assert hit.title == ""
        assert hit.snippet == ""

    def test_new_generates_chunk_id_if_empty(self):
        hit = MemoryHit.new(
            query_id="qry_test",
            source_type=SOURCE_AKASHA,
            source_id="src_test",
        )
        assert hit.chunk_id.startswith("chk_")

    def test_new_accepts_explicit_chunk_id(self):
        hit = MemoryHit.new(
            query_id="qry_test",
            source_type=SOURCE_AKASHA,
            source_id="src_test",
            chunk_id="my_chunk_1",
        )
        assert hit.chunk_id == "my_chunk_1"

    def test_new_rejects_invalid_source(self):
        with pytest.raises(ValueError, match="Tipo de fonte invalido"):
            MemoryHit.new(query_id="q", source_type="bad", source_id="s")

    def test_new_rejects_invalid_relevance(self):
        with pytest.raises(ValueError, match="Relevancia invalida"):
            MemoryHit.new(query_id="q", source_type=SOURCE_AKASHA, source_id="s", relevance="bad")

    def test_rank_score_matches_relevance(self):
        for rel, score in RELEVANCE_RANK.items():
            hit = MemoryHit.new(
                query_id="q", source_type=SOURCE_AKASHA, source_id="s", relevance=rel
            )
            assert hit.rank_score == score

    def test_to_dict_and_back(self):
        hit = MemoryHit.new(
            query_id="qry_test",
            source_type=SOURCE_MEM0,
            source_id="src_test",
            relevance=RELEVANCE_EXACT,
            title="Roundtrip",
            metadata={"key": "val"},
        )
        data = hit.to_dict()
        restored = MemoryHit.from_dict(data)
        assert restored.hit_id == hit.hit_id
        assert restored.rank_score == hit.rank_score
        assert restored.metadata == hit.metadata


# ── ContextPack ─────────────────────────────────────────────────────────────

class TestContextPack:
    """Testes para o modelo ContextPack."""

    def test_new_creates_empty_pack(self):
        pack = ContextPack.new(query_id="qry_test")
        assert pack.pack_id.startswith("pack_")
        assert pack.query_id == "qry_test"
        assert pack.total_hits == 0
        assert pack.total_sources == 0
        assert pack.top_relevance == RELEVANCE_NONE
        assert pack.dry_run is True
        assert pack.is_empty is True

    def test_assemble_populates_pack(self):
        pack = ContextPack.new(query_id="qry_test")
        hits = [
            MemoryHit.new(query_id="qry_test", source_type=SOURCE_AKASHA, source_id="s1",
                          relevance=RELEVANCE_HIGH, title="A", snippet="snippet A"),
            MemoryHit.new(query_id="qry_test", source_type=SOURCE_OBSIDIAN, source_id="s2",
                          relevance=RELEVANCE_MEDIUM, title="B", snippet="snippet B"),
        ]
        pack.assemble(hits)
        assert pack.total_hits == 2
        assert pack.total_sources == 2
        assert pack.top_relevance == RELEVANCE_HIGH
        assert pack.is_empty is False
        assert SOURCE_AKASHA in pack.source_summary
        assert SOURCE_OBSIDIAN in pack.source_summary

    def test_assemble_generates_text(self):
        pack = ContextPack.new(query_id="qry_test")
        hits = [
            MemoryHit.new(query_id="qry_test", source_type=SOURCE_AKASHA, source_id="s1",
                          relevance=RELEVANCE_HIGH, title="Titulo", snippet="Conteudo"),
        ]
        pack.assemble(hits)
        assert "Titulo" in pack.assembled_text
        assert "Conteudo" in pack.assembled_text
        assert "[akasha:high]" in pack.assembled_text

    def test_assemble_empty_hits(self):
        pack = ContextPack.new(query_id="qry_test")
        pack.assemble([])
        assert pack.is_empty is True
        assert pack.total_hits == 0

    def test_top_relevance_is_max(self):
        pack = ContextPack.new(query_id="qry_test")
        hits = [
            MemoryHit.new(query_id="qry_test", source_type=SOURCE_AKASHA, source_id="s1",
                          relevance=RELEVANCE_LOW, title="Low"),
            MemoryHit.new(query_id="qry_test", source_type=SOURCE_AKASHA, source_id="s2",
                          relevance=RELEVANCE_EXACT, title="Exact"),
            MemoryHit.new(query_id="qry_test", source_type=SOURCE_AKASHA, source_id="s3",
                          relevance=RELEVANCE_MEDIUM, title="Med"),
        ]
        pack.assemble(hits)
        assert pack.top_relevance == RELEVANCE_EXACT

    def test_to_dict_and_back(self):
        pack = ContextPack.new(query_id="qry_test")
        hits = [
            MemoryHit.new(query_id="qry_test", source_type=SOURCE_AKASHA, source_id="s1",
                          relevance=RELEVANCE_HIGH, title="T", snippet="S"),
        ]
        pack.assemble(hits)
        data = pack.to_dict()
        restored = ContextPack.from_dict(data)
        assert restored.pack_id == pack.pack_id
        assert restored.total_hits == pack.total_hits
        assert len(restored.hits) == 1
        assert restored.hits[0].title == "T"


# ── MissionMemoryRecord ─────────────────────────────────────────────────────

class TestMissionMemoryRecord:
    """Testes para o modelo MissionMemoryRecord."""

    def test_new_creates_with_valid_data(self):
        rec = MissionMemoryRecord.new(
            mission_id="mis_001",
            sector=SECTOR_COMERCIAL,
            title="Prospeccao SP",
            summary="Resumo da missao",
            key_insights=["Insight 1", "Insight 2"],
            decisions=["Decisao 1"],
            outcomes=["Outcome 1"],
        )
        assert rec.mission_id == "mis_001"
        assert rec.sector == SECTOR_COMERCIAL
        assert rec.title == "Prospeccao SP"
        assert len(rec.key_insights) == 2
        assert rec.status == STATUS_DRAFT
        assert rec.record_id.startswith("rec_")

    def test_new_defaults(self):
        rec = MissionMemoryRecord.new(
            mission_id="mis_002",
            sector=SECTOR_MIDIA,
            title="Default test",
            summary="...",
        )
        assert rec.key_insights == []
        assert rec.decisions == []
        assert rec.outcomes == []
        assert rec.source_type == SOURCE_SESSION
        assert rec.tags == []

    def test_new_rejects_empty_title(self):
        with pytest.raises(ValueError, match="title nao pode ser vazio"):
            MissionMemoryRecord.new(mission_id="m", sector=SECTOR_MIDIA, title="", summary="s")

    def test_new_rejects_invalid_sector(self):
        with pytest.raises(ValueError, match="Setor invalido"):
            MissionMemoryRecord.new(
                mission_id="m", sector="invalid", title="T", summary="s"
            )

    def test_new_rejects_invalid_source_type(self):
        with pytest.raises(ValueError, match="Tipo de fonte invalido"):
            MissionMemoryRecord.new(
                mission_id="m", sector=SECTOR_MIDIA, title="T", summary="s",
                source_type="invalid",
            )

    def test_archive_updates_status(self):
        rec = MissionMemoryRecord.new(
            mission_id="m", sector=SECTOR_MIDIA, title="T", summary="s"
        )
        rec.archive()
        assert rec.status == STATUS_ARCHIVED

    def test_activate_updates_status(self):
        rec = MissionMemoryRecord.new(
            mission_id="m", sector=SECTOR_MIDIA, title="T", summary="s"
        )
        rec.activate()
        assert rec.status == STATUS_ACTIVE

    def test_supersede_updates_status(self):
        rec = MissionMemoryRecord.new(
            mission_id="m", sector=SECTOR_MIDIA, title="T", summary="s"
        )
        rec.supersede()
        assert rec.status == STATUS_SUPERSEDED

    def test_strips_title(self):
        rec = MissionMemoryRecord.new(
            mission_id="m", sector=SECTOR_MIDIA, title="  Padded  ", summary="s"
        )
        assert rec.title == "Padded"

    def test_to_dict_and_back(self):
        rec = MissionMemoryRecord.new(
            mission_id="mis_003",
            sector=SECTOR_PRODUTO,
            title="Roundtrip",
            summary="Test",
            tags=["tag1", "tag2"],
        )
        data = rec.to_dict()
        restored = MissionMemoryRecord.from_dict(data)
        assert restored.record_id == rec.record_id
        assert restored.tags == rec.tags
        assert restored.status == rec.status


# ── MemoryWritePlan ─────────────────────────────────────────────────────────

class TestMemoryWritePlan:
    """Testes para o modelo MemoryWritePlan."""

    def test_new_creates_dry_run_plan(self):
        plan = MemoryWritePlan.new(
            target_source=SOURCE_AKASHA,
            action=ACTION_UPSERT,
        )
        assert plan.plan_id.startswith("wrp_")
        assert plan.target_source == SOURCE_AKASHA
        assert plan.action == ACTION_UPSERT
        assert plan.is_dry_run is True
        assert plan.requires_approval is True
        assert plan.record_count == 0
        assert len(plan.safety_rules_applied) == 5

    def test_new_rejects_invalid_source(self):
        with pytest.raises(ValueError, match="Tipo de fonte invalido"):
            MemoryWritePlan.new(target_source="invalid")

    def test_new_rejects_invalid_action(self):
        with pytest.raises(ValueError, match="Acao invalida"):
            MemoryWritePlan.new(target_source=SOURCE_AKASHA, action="invalid")

    def test_new_blocks_delete_action(self):
        with pytest.raises(ValueError, match="Acao DELETE bloqueada"):
            MemoryWritePlan.new(target_source=SOURCE_AKASHA, action=ACTION_DELETE)

    def test_new_accepts_insert_and_update(self):
        for action in [ACTION_INSERT, ACTION_UPDATE, ACTION_UPSERT]:
            plan = MemoryWritePlan.new(target_source=SOURCE_AKASHA, action=action)
            assert plan.action == action

    def test_add_record_increments_count(self, sample_record):
        plan = MemoryWritePlan.new(target_source=SOURCE_AKASHA)
        assert plan.record_count == 0
        plan.add_record(sample_record)
        assert plan.record_count == 1

    def test_add_chunk_increments_count(self):
        plan = MemoryWritePlan.new(target_source=SOURCE_AKASHA)
        assert plan.chunk_count == 0
        plan.add_chunk(chunk_id="chk_1", content="content")
        assert plan.chunk_count == 1

    def test_add_chunk_stores_data(self):
        plan = MemoryWritePlan.new(target_source=SOURCE_AKASHA)
        plan.add_chunk(chunk_id="chk_x", content="hello", metadata={"k": "v"})
        assert plan.target_chunks[0]["chunk_id"] == "chk_x"
        assert plan.target_chunks[0]["content"] == "hello"
        assert plan.target_chunks[0]["metadata"] == {"k": "v"}

    def test_to_dict_and_back(self, sample_record):
        plan = MemoryWritePlan.new(target_source=SOURCE_OBSIDIAN, action=ACTION_INSERT)
        plan.add_record(sample_record)
        plan.add_chunk(chunk_id="c1", content="data")
        data = plan.to_dict()
        restored = MemoryWritePlan.from_dict(data)
        assert restored.plan_id == plan.plan_id
        assert restored.record_count == 1
        assert restored.chunk_count == 1
        assert restored.records[0].title == sample_record.title


# ── Cross-model JSON serialization ──────────────────────────────────────────

class TestJsonSerialization:
    """Testes de serializacao JSON completa."""

    def test_full_roundtrip_all_models(self):
        """Serializar e restaurar todos os modelos em cadeia."""
        src = MemorySource.new(source_type=SOURCE_AKASHA, label="Test")
        query = MemoryQuery.new(text="test query", sources=[SOURCE_AKASHA])
        hit = MemoryHit.new(
            query_id=query.query_id,
            source_type=SOURCE_AKASHA,
            source_id=src.source_id,
            relevance=RELEVANCE_HIGH,
            title="Hit title",
        )
        pack = ContextPack.new(query_id=query.query_id)
        pack.assemble([hit])
        rec = MissionMemoryRecord.new(
            mission_id="mis_test", sector=SECTOR_MIDIA, title="Rec", summary="s"
        )
        plan = MemoryWritePlan.new(target_source=SOURCE_AKASHA)
        plan.add_record(rec)

        # Serialize all to JSON strings
        models = {
            "source": src.to_dict(),
            "query": query.to_dict(),
            "hit": hit.to_dict(),
            "pack": pack.to_dict(),
            "record": rec.to_dict(),
            "plan": plan.to_dict(),
        }
        serialized = json.dumps(models, ensure_ascii=False)
        assert isinstance(serialized, str)

        # Restore
        restored = json.loads(serialized)
        assert restored["source"]["source_type"] == SOURCE_AKASHA
        assert restored["pack"]["total_hits"] == 1
        assert restored["plan"]["is_dry_run"] is True
