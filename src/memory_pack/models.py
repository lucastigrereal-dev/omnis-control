"""P4 Memory Pack models — memory sources, queries, hits, context packs, mission records."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

# ── Memory source type constants ───────────────────────────────────────────
SOURCE_AKASHA = "akasha"
SOURCE_OBSIDIAN = "obsidian"
SOURCE_MEM0 = "mem0"
SOURCE_GRINGOTTS = "gringotts"
SOURCE_BIBLIOTECA = "biblioteca"
SOURCE_SESSION = "session"
SOURCE_STATIC = "static"

VALID_SOURCES = {
    SOURCE_AKASHA,
    SOURCE_OBSIDIAN,
    SOURCE_MEM0,
    SOURCE_GRINGOTTS,
    SOURCE_BIBLIOTECA,
    SOURCE_SESSION,
    SOURCE_STATIC,
}

# ── Memory hit relevance constants ─────────────────────────────────────────
RELEVANCE_EXACT = "exact"
RELEVANCE_HIGH = "high"
RELEVANCE_MEDIUM = "medium"
RELEVANCE_LOW = "low"
RELEVANCE_NONE = "none"

VALID_RELEVANCES = {
    RELEVANCE_EXACT,
    RELEVANCE_HIGH,
    RELEVANCE_MEDIUM,
    RELEVANCE_LOW,
    RELEVANCE_NONE,
}

RELEVANCE_RANK = {
    RELEVANCE_EXACT: 100,
    RELEVANCE_HIGH: 75,
    RELEVANCE_MEDIUM: 50,
    RELEVANCE_LOW: 25,
    RELEVANCE_NONE: 0,
}

# ── Context pack format constants ──────────────────────────────────────────
FORMAT_JSON = "json"
FORMAT_MARKDOWN = "markdown"
FORMAT_DICT = "dict"

VALID_FORMATS = {FORMAT_JSON, FORMAT_MARKDOWN, FORMAT_DICT}

# ── Mission memory record status constants ─────────────────────────────────
STATUS_DRAFT = "draft"
STATUS_ACTIVE = "active"
STATUS_ARCHIVED = "archived"
STATUS_SUPERSEDED = "superseded"

VALID_RECORD_STATUSES = {STATUS_DRAFT, STATUS_ACTIVE, STATUS_ARCHIVED, STATUS_SUPERSEDED}

# ── Write plan action constants ────────────────────────────────────────────
ACTION_INSERT = "insert"
ACTION_UPDATE = "update"
ACTION_UPSERT = "upsert"
ACTION_DELETE = "delete"

VALID_WRITE_ACTIONS = {ACTION_INSERT, ACTION_UPDATE, ACTION_UPSERT, ACTION_DELETE}
DRY_RUN_ACTIONS = {ACTION_INSERT, ACTION_UPDATE, ACTION_UPSERT}  # delete blocked by default

# ── Sector constants (from JARVIS 7 sectors) ───────────────────────────────
SECTOR_MIDIA = "midia"
SECTOR_COMERCIAL = "comercial"
SECTOR_VENDAS = "vendas"
SECTOR_CONHECIMENTO = "conhecimento"
SECTOR_PRODUTO = "produto"
SECTOR_FINANCEIRO = "financeiro"
SECTOR_OPERACOES = "operacoes"

VALID_SECTORS = {
    SECTOR_MIDIA,
    SECTOR_COMERCIAL,
    SECTOR_VENDAS,
    SECTOR_CONHECIMENTO,
    SECTOR_PRODUTO,
    SECTOR_FINANCEIRO,
    SECTOR_OPERACOES,
}


class MemorySourceType(Enum):
    AKASHA = SOURCE_AKASHA
    OBSIDIAN = SOURCE_OBSIDIAN
    MEM0 = SOURCE_MEM0
    GRINGOTTS = SOURCE_GRINGOTTS
    BIBLIOTECA = SOURCE_BIBLIOTECA
    SESSION = SOURCE_SESSION
    STATIC = SOURCE_STATIC


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Memory Source ──────────────────────────────────────────────────────────

@dataclass
class MemorySource:
    """Fonte de memoria registrada no sistema — metadados, sem conexao real."""
    source_id: str
    source_type: str
    label: str
    description: str = ""
    is_available: bool = True
    is_primary: bool = False
    priority: int = 50
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        source_type: str,
        label: str,
        description: str = "",
        is_available: bool = True,
        is_primary: bool = False,
        priority: int = 50,
        metadata: Optional[dict] = None,
    ) -> "MemorySource":
        if source_type not in VALID_SOURCES:
            raise ValueError(
                f"Tipo de fonte invalido: {source_type!r}. Deve ser um de {sorted(VALID_SOURCES)}"
            )
        if not (0 <= priority <= 100):
            raise ValueError("priority deve estar entre 0 e 100")
        return cls(
            source_id=_new_id("src"),
            source_type=source_type,
            label=label,
            description=description,
            is_available=is_available,
            is_primary=is_primary,
            priority=priority,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "label": self.label,
            "description": self.description,
            "is_available": self.is_available,
            "is_primary": self.is_primary,
            "priority": self.priority,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemorySource":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Memory Query ───────────────────────────────────────────────────────────

@dataclass
class MemoryQuery:
    """Query de busca em memoria — estruturada, rastreavel, sem execucao real."""
    query_id: str
    text: str
    sources: list[str] = field(default_factory=list)
    sectors: list[str] = field(default_factory=list)
    max_hits: int = 10
    min_relevance: str = RELEVANCE_LOW
    filters: dict = field(default_factory=dict)
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        text: str,
        sources: Optional[list[str]] = None,
        sectors: Optional[list[str]] = None,
        max_hits: int = 10,
        min_relevance: str = RELEVANCE_LOW,
        filters: Optional[dict] = None,
    ) -> "MemoryQuery":
        if not text.strip():
            raise ValueError("text da query nao pode ser vazio")
        if min_relevance not in VALID_RELEVANCES:
            raise ValueError(
                f"Relevancia invalida: {min_relevance!r}. Deve ser uma de {sorted(VALID_RELEVANCES)}"
            )
        if max_hits < 1:
            raise ValueError("max_hits deve ser >= 1")
        srcs = sources or []
        invalid = [s for s in srcs if s not in VALID_SOURCES]
        if invalid:
            raise ValueError(f"Fontes invalidas: {invalid}")
        secs = sectors or []
        invalid_sec = [s for s in secs if s not in VALID_SECTORS]
        if invalid_sec:
            raise ValueError(f"Setores invalidos: {invalid_sec}")
        return cls(
            query_id=_new_id("qry"),
            text=text.strip(),
            sources=srcs,
            sectors=secs,
            max_hits=max_hits,
            min_relevance=min_relevance,
            filters=filters or {},
            dry_run=True,
        )

    @property
    def min_rank(self) -> int:
        return RELEVANCE_RANK.get(self.min_relevance, 0)

    def to_dict(self) -> dict:
        return {
            "query_id": self.query_id,
            "text": self.text,
            "sources": self.sources,
            "sectors": self.sectors,
            "max_hits": self.max_hits,
            "min_relevance": self.min_relevance,
            "filters": self.filters,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryQuery":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Memory Hit ─────────────────────────────────────────────────────────────

@dataclass
class MemoryHit:
    """Resultado de busca em memoria — apontador, nao o conteudo real completo."""
    hit_id: str
    query_id: str
    source_type: str
    source_id: str
    chunk_id: str
    relevance: str
    rank_score: int
    title: str = ""
    snippet: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        query_id: str,
        source_type: str,
        source_id: str,
        chunk_id: str = "",
        relevance: str = RELEVANCE_MEDIUM,
        title: str = "",
        snippet: str = "",
        metadata: Optional[dict] = None,
    ) -> "MemoryHit":
        if source_type not in VALID_SOURCES:
            raise ValueError(
                f"Tipo de fonte invalido: {source_type!r}. Deve ser um de {sorted(VALID_SOURCES)}"
            )
        if relevance not in VALID_RELEVANCES:
            raise ValueError(
                f"Relevancia invalida: {relevance!r}. Deve ser uma de {sorted(VALID_RELEVANCES)}"
            )
        return cls(
            hit_id=_new_id("hit"),
            query_id=query_id,
            source_type=source_type,
            source_id=source_id,
            chunk_id=chunk_id or _new_id("chk"),
            relevance=relevance,
            rank_score=RELEVANCE_RANK[relevance],
            title=title,
            snippet=snippet,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict:
        return {
            "hit_id": self.hit_id,
            "query_id": self.query_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "chunk_id": self.chunk_id,
            "relevance": self.relevance,
            "rank_score": self.rank_score,
            "title": self.title,
            "snippet": self.snippet,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryHit":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Context Pack ───────────────────────────────────────────────────────────

@dataclass
class ContextPack:
    """Pacote de contexto montado a partir de memory hits — imutavel apos build."""
    pack_id: str
    query_id: str
    hits: list[MemoryHit] = field(default_factory=list)
    assembled_text: str = ""
    source_summary: dict = field(default_factory=dict)
    total_hits: int = 0
    total_sources: int = 0
    top_relevance: str = RELEVANCE_NONE
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, query_id: str) -> "ContextPack":
        return cls(
            pack_id=_new_id("pack"),
            query_id=query_id,
        )

    @property
    def is_empty(self) -> bool:
        return self.total_hits == 0

    def assemble(self, hits: list[MemoryHit]) -> None:
        self.hits = hits
        self.total_hits = len(hits)
        sources_seen = {h.source_type for h in hits}
        self.total_sources = len(sources_seen)
        self.source_summary = {}
        for h in hits:
            self.source_summary.setdefault(h.source_type, 0)
            self.source_summary[h.source_type] += 1
        if hits:
            best = max(hits, key=lambda h: h.rank_score)
            self.top_relevance = best.relevance
        parts = []
        for h in hits:
            parts.append(f"[{h.source_type}:{h.relevance}] {h.title}\n{h.snippet}")
        self.assembled_text = "\n\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "pack_id": self.pack_id,
            "query_id": self.query_id,
            "hits": [h.to_dict() for h in self.hits],
            "assembled_text": self.assembled_text,
            "source_summary": self.source_summary,
            "total_hits": self.total_hits,
            "total_sources": self.total_sources,
            "top_relevance": self.top_relevance,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContextPack":
        hits_data = data.pop("hits", [])
        pack = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        pack.hits = [MemoryHit.from_dict(h) for h in hits_data]
        return pack


# ── Mission Memory Record ──────────────────────────────────────────────────

@dataclass
class MissionMemoryRecord:
    """Registro de memoria de missao — aprendizado persistente de uma missao."""
    record_id: str
    mission_id: str
    sector: str
    title: str
    summary: str
    key_insights: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)
    source_type: str = SOURCE_SESSION
    status: str = STATUS_DRAFT
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        mission_id: str,
        sector: str,
        title: str,
        summary: str,
        key_insights: Optional[list[str]] = None,
        decisions: Optional[list[str]] = None,
        outcomes: Optional[list[str]] = None,
        source_type: str = SOURCE_SESSION,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
    ) -> "MissionMemoryRecord":
        if sector not in VALID_SECTORS:
            raise ValueError(
                f"Setor invalido: {sector!r}. Deve ser um de {sorted(VALID_SECTORS)}"
            )
        if source_type not in VALID_SOURCES:
            raise ValueError(
                f"Tipo de fonte invalido: {source_type!r}. Deve ser um de {sorted(VALID_SOURCES)}"
            )
        if not title.strip():
            raise ValueError("title nao pode ser vazio")
        return cls(
            record_id=_new_id("rec"),
            mission_id=mission_id,
            sector=sector,
            title=title.strip(),
            summary=summary,
            key_insights=key_insights or [],
            decisions=decisions or [],
            outcomes=outcomes or [],
            source_type=source_type,
            tags=tags or [],
            metadata=metadata or {},
        )

    def archive(self) -> None:
        self.status = STATUS_ARCHIVED
        self.updated_at = _now_iso()

    def activate(self) -> None:
        self.status = STATUS_ACTIVE
        self.updated_at = _now_iso()

    def supersede(self) -> None:
        self.status = STATUS_SUPERSEDED
        self.updated_at = _now_iso()

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "mission_id": self.mission_id,
            "sector": self.sector,
            "title": self.title,
            "summary": self.summary,
            "key_insights": self.key_insights,
            "decisions": self.decisions,
            "outcomes": self.outcomes,
            "source_type": self.source_type,
            "status": self.status,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MissionMemoryRecord":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Memory Write Plan ──────────────────────────────────────────────────────

@dataclass
class MemoryWritePlan:
    """Plano de writeback — descreve O QUE escrever, sem nunca executar."""
    plan_id: str
    target_source: str
    action: str
    records: list[MissionMemoryRecord] = field(default_factory=list)
    target_chunks: list[dict] = field(default_factory=list)
    is_dry_run: bool = True
    requires_approval: bool = True
    safety_rules_applied: list[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        target_source: str,
        action: str = ACTION_UPSERT,
        notes: str = "",
    ) -> "MemoryWritePlan":
        if target_source not in VALID_SOURCES:
            raise ValueError(
                f"Tipo de fonte invalido: {target_source!r}. Deve ser um de {sorted(VALID_SOURCES)}"
            )
        if action not in VALID_WRITE_ACTIONS:
            raise ValueError(
                f"Acao invalida: {action!r}. Deve ser uma de {sorted(VALID_WRITE_ACTIONS)}"
            )
        if action == ACTION_DELETE:
            raise ValueError(
                "Acao DELETE bloqueada por padrao. Use dry-run para planejar, nunca executar."
            )
        return cls(
            plan_id=_new_id("wrp"),
            target_source=target_source,
            action=action,
            is_dry_run=True,
            requires_approval=True,
            safety_rules_applied=[
                "dry_run_only",
                "no_real_akasha_connection",
                "writeback_plan_never_execute",
                "approval_required",
                "no_delete_by_default",
            ],
            notes=notes,
        )

    @property
    def record_count(self) -> int:
        return len(self.records)

    @property
    def chunk_count(self) -> int:
        return len(self.target_chunks)

    def add_record(self, record: MissionMemoryRecord) -> None:
        self.records.append(record)

    def add_chunk(self, chunk_id: str, content: str, metadata: Optional[dict] = None) -> None:
        self.target_chunks.append({
            "chunk_id": chunk_id,
            "content": content,
            "metadata": metadata or {},
        })

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "target_source": self.target_source,
            "action": self.action,
            "records": [r.to_dict() for r in self.records],
            "target_chunks": self.target_chunks,
            "is_dry_run": self.is_dry_run,
            "requires_approval": self.requires_approval,
            "safety_rules_applied": self.safety_rules_applied,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryWritePlan":
        records_data = data.pop("records", [])
        plan = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        plan.records = [MissionMemoryRecord.from_dict(r) for r in records_data]
        return plan
