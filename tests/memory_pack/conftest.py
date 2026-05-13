"""Fixtures compartilhadas para testes do memory_pack."""
from __future__ import annotations

import pytest

from src.memory_pack.models import (
    MemorySource,
    MemoryQuery,
    MemoryHit,
    MissionMemoryRecord,
    ContextPack,
    MemoryWritePlan,
    SOURCE_AKASHA,
    SOURCE_OBSIDIAN,
    SOURCE_SESSION,
    RELEVANCE_HIGH,
    RELEVANCE_MEDIUM,
    RELEVANCE_LOW,
    SECTOR_COMERCIAL,
    SECTOR_MIDIA,
    ACTION_UPSERT,
)
from src.memory_pack.service import MemoryPackPlanner


@pytest.fixture
def planner() -> MemoryPackPlanner:
    """Planner default com fontes registradas."""
    return MemoryPackPlanner.create()


@pytest.fixture
def akasha_source() -> MemorySource:
    """Fonte Akasha de exemplo."""
    return MemorySource.new(
        source_type=SOURCE_AKASHA,
        label="Akasha Test",
        is_primary=True,
        priority=95,
    )


@pytest.fixture
def sample_query() -> MemoryQuery:
    """Query de exemplo para testes."""
    return MemoryQuery.new(
        text="estrategia de conteudo para hoteis",
        sources=[SOURCE_AKASHA, SOURCE_OBSIDIAN],
        sectors=[SECTOR_COMERCIAL, SECTOR_MIDIA],
    )


@pytest.fixture
def sample_hits(sample_query: MemoryQuery) -> list[MemoryHit]:
    """Hits de exemplo para testes."""
    return [
        MemoryHit.new(
            query_id=sample_query.query_id,
            source_type=SOURCE_AKASHA,
            source_id="src_test_1",
            relevance=RELEVANCE_HIGH,
            title="Estrategia de conteudo para hoteis",
            snippet="Conteudo relevante sobre estrategia hoteleira...",
        ),
        MemoryHit.new(
            query_id=sample_query.query_id,
            source_type=SOURCE_OBSIDIAN,
            source_id="src_test_2",
            relevance=RELEVANCE_MEDIUM,
            title="Nota sobre comercial SDR",
            snippet="Reflexao sobre venda de collabs...",
        ),
        MemoryHit.new(
            query_id=sample_query.query_id,
            source_type=SOURCE_AKASHA,
            source_id="src_test_3",
            relevance=RELEVANCE_LOW,
            title="Historico de collabs",
            snippet="Dados historicos de collabs...",
        ),
    ]


@pytest.fixture
def sample_record() -> MissionMemoryRecord:
    """Registro de missao de exemplo."""
    return MissionMemoryRecord.new(
        mission_id="mis_test_001",
        sector=SECTOR_COMERCIAL,
        title="Prospeccao hoteis SP",
        summary="Missao de prospeccao de 150 hoteis no interior de SP",
        key_insights=["Hoteis preferem pacotes visuais", "Tiket medio R$350-990"],
        decisions=["Focar no pacote Growth R$990"],
        outcomes=["15 respostas positivas"],
    )


@pytest.fixture
def sample_context_pack(sample_query: MemoryQuery, sample_hits: list[MemoryHit]) -> ContextPack:
    """ContextPack montado de exemplo."""
    pack = ContextPack.new(query_id=sample_query.query_id)
    pack.assemble(sample_hits)
    return pack


@pytest.fixture
def sample_write_plan(sample_record: MissionMemoryRecord) -> MemoryWritePlan:
    """Write plan de exemplo."""
    plan = MemoryWritePlan.new(
        target_source=SOURCE_AKASHA,
        action=ACTION_UPSERT,
    )
    plan.add_record(sample_record)
    return plan
