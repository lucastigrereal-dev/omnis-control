"""P21 Memory Intelligence models — config, similarity results, retrieval results."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from src.memory_pack.models import (
    ContextPack,
    MissionMemoryRecord,
    MemoryQuery,
    SOURCE_AKASHA,
    SOURCE_OBSIDIAN,
    SOURCE_SESSION,
    SOURCE_GRINGOTTS,
    SOURCE_BIBLIOTECA,
    VALID_SOURCES,
    VALID_SECTORS,
    SECTOR_MIDIA,
    SECTOR_COMERCIAL,
    SECTOR_VENDAS,
    SECTOR_CONHECIMENTO,
    SECTOR_PRODUTO,
    SECTOR_FINANCEIRO,
    SECTOR_OPERACOES,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Intent constants ─────────────────────────────────────────────────────────

INTENT_CREATE_CAMPAIGN = "create_campaign"
INTENT_PUBLISH_CONTENT = "publish_content"
INTENT_DELIVER_TO_CLIENT = "deliver_to_client"
INTENT_ANALYZE_PERFORMANCE = "analyze_performance"
INTENT_COMMERCIAL_OUTREACH = "commercial_outreach"

VALID_INTENTS = {
    INTENT_CREATE_CAMPAIGN,
    INTENT_PUBLISH_CONTENT,
    INTENT_DELIVER_TO_CLIENT,
    INTENT_ANALYZE_PERFORMANCE,
    INTENT_COMMERCIAL_OUTREACH,
}

# ── Intent → Sources mapping ─────────────────────────────────────────────────

INTENT_TO_SOURCES = {
    INTENT_CREATE_CAMPAIGN: [SOURCE_AKASHA, SOURCE_OBSIDIAN, SOURCE_SESSION],
    INTENT_PUBLISH_CONTENT: [SOURCE_AKASHA, SOURCE_OBSIDIAN, SOURCE_SESSION],
    INTENT_DELIVER_TO_CLIENT: [SOURCE_SESSION, SOURCE_GRINGOTTS],
    INTENT_ANALYZE_PERFORMANCE: [SOURCE_AKASHA, SOURCE_SESSION, SOURCE_BIBLIOTECA],
    INTENT_COMMERCIAL_OUTREACH: [SOURCE_GRINGOTTS, SOURCE_SESSION, SOURCE_OBSIDIAN],
}

# ── Similarity score weights ─────────────────────────────────────────────────

SIMILARITY_WEIGHT_INTENT = 0.40
SIMILARITY_WEIGHT_SECTOR = 0.30
SIMILARITY_WEIGHT_TAGS = 0.20
SIMILARITY_WEIGHT_MODULES = 0.10

# ── Limits ───────────────────────────────────────────────────────────────────

MAX_ASSEMBLED_TEXT_CHARS = 2000
MAX_SNIPPET_CHARS = 300
MAX_HITS_PER_SOURCE = 3
MAX_RECORDS_PER_MISSION = 5
MAX_SIMILAR_MISSIONS_RESULTS = 5
DEFAULT_MAX_HITS = 8
MIN_SIMILARITY_THRESHOLD = 0.3


class MemoryIntelMode(str, Enum):
    RETRIEVAL = "retrieval"
    WRITEBACK = "writeback"


# ── Memory Intel Config ──────────────────────────────────────────────────────

@dataclass
class MemoryIntelConfig:
    """Configuracao do motor de inteligencia contextual."""
    config_id: str
    intent_to_sources: dict
    max_hits: int = DEFAULT_MAX_HITS
    max_assembled_chars: int = MAX_ASSEMBLED_TEXT_CHARS
    max_snippet_chars: int = MAX_SNIPPET_CHARS
    max_hits_per_source: int = MAX_HITS_PER_SOURCE
    max_records_per_mission: int = MAX_RECORDS_PER_MISSION
    max_similar_results: int = MAX_SIMILAR_MISSIONS_RESULTS
    similarity_threshold: float = MIN_SIMILARITY_THRESHOLD
    similarity_weight_intent: float = SIMILARITY_WEIGHT_INTENT
    similarity_weight_sector: float = SIMILARITY_WEIGHT_SECTOR
    similarity_weight_tags: float = SIMILARITY_WEIGHT_TAGS
    similarity_weight_modules: float = SIMILARITY_WEIGHT_MODULES
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, dry_run: bool = True) -> "MemoryIntelConfig":
        return cls(
            config_id=_new_id("mic"),
            intent_to_sources=dict(INTENT_TO_SOURCES),
            dry_run=dry_run,
        )

    @classmethod
    def load(cls) -> "MemoryIntelConfig":
        """Carrega configuracao default (sem arquivo externo)."""
        return cls.new()

    def get_sources_for_intent(self, intent: str) -> list[str]:
        """Retorna fontes recomendadas para um intent."""
        if intent not in VALID_INTENTS:
            return [SOURCE_AKASHA, SOURCE_SESSION]
        return list(self.intent_to_sources.get(intent, [SOURCE_AKASHA, SOURCE_SESSION]))

    def to_dict(self) -> dict:
        return {
            "config_id": self.config_id,
            "intent_to_sources": self.intent_to_sources,
            "max_hits": self.max_hits,
            "max_assembled_chars": self.max_assembled_chars,
            "max_snippet_chars": self.max_snippet_chars,
            "max_hits_per_source": self.max_hits_per_source,
            "max_records_per_mission": self.max_records_per_mission,
            "max_similar_results": self.max_similar_results,
            "similarity_threshold": self.similarity_threshold,
            "similarity_weight_intent": self.similarity_weight_intent,
            "similarity_weight_sector": self.similarity_weight_sector,
            "similarity_weight_tags": self.similarity_weight_tags,
            "similarity_weight_modules": self.similarity_weight_modules,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryIntelConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Mission Similarity Result ────────────────────────────────────────────────

@dataclass
class MissionSimilarityResult:
    """Resultado de busca por missoes similares."""
    sim_id: str
    source_mission: MissionMemoryRecord
    similarity_score: float
    matched_on: list[str] = field(default_factory=list)
    relevant_learnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        source_mission: MissionMemoryRecord,
        similarity_score: float,
        matched_on: list[str] | None = None,
        relevant_learnings: list[str] | None = None,
    ) -> "MissionSimilarityResult":
        if not (0.0 <= similarity_score <= 1.0):
            raise ValueError(
                f"similarity_score deve estar entre 0.0 e 1.0, recebido {similarity_score}"
            )
        return cls(
            sim_id=_new_id("sim"),
            source_mission=source_mission,
            similarity_score=round(similarity_score, 2),
            matched_on=matched_on or [],
            relevant_learnings=relevant_learnings or list(source_mission.key_insights),
        )

    def to_dict(self) -> dict:
        return {
            "sim_id": self.sim_id,
            "source_mission": self.source_mission.to_dict(),
            "similarity_score": self.similarity_score,
            "matched_on": self.matched_on,
            "relevant_learnings": self.relevant_learnings,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MissionSimilarityResult":
        data = dict(data)
        mission_data = data.pop("source_mission", {})
        field_kwargs = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        result = cls(
            source_mission=MissionMemoryRecord.from_dict(mission_data),
            **field_kwargs,
        )
        return result


# ── Retrieval Result ─────────────────────────────────────────────────────────

@dataclass
class RetrievalResult:
    """Resultado completo de retrieval: ContextPack + similares + patterns."""
    result_id: str
    query_id: str
    pack: ContextPack
    similar_missions: list[MissionSimilarityResult] = field(default_factory=list)
    patterns: dict = field(default_factory=dict)
    mode: str = "retrieval"
    dry_run: bool = True
    warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        query_id: str,
        pack: ContextPack,
        similar_missions: list[MissionSimilarityResult] | None = None,
        patterns: dict | None = None,
        dry_run: bool = True,
        warnings: list[str] | None = None,
    ) -> "RetrievalResult":
        return cls(
            result_id=_new_id("ret"),
            query_id=query_id,
            pack=pack,
            similar_missions=similar_missions or [],
            patterns=patterns or {},
            dry_run=dry_run,
            warnings=warnings or [],
        )

    @property
    def is_empty(self) -> bool:
        return self.pack.is_empty

    @property
    def similarity_count(self) -> int:
        return len(self.similar_missions)

    @property
    def top_similarity_score(self) -> float:
        if not self.similar_missions:
            return 0.0
        return max(s.similarity_score for s in self.similar_missions)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "query_id": self.query_id,
            "pack": self.pack.to_dict(),
            "similar_missions": [s.to_dict() for s in self.similar_missions],
            "patterns": self.patterns,
            "mode": self.mode,
            "dry_run": self.dry_run,
            "warnings": self.warnings,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RetrievalResult":
        data = dict(data)
        pack_data = data.pop("pack", {})
        sims_data = data.pop("similar_missions", [])
        field_kwargs = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        result = cls(
            pack=ContextPack.from_dict(pack_data),
            similar_missions=[MissionSimilarityResult.from_dict(s) for s in sims_data],
            **field_kwargs,
        )
        return result


# ── Pattern Result ───────────────────────────────────────────────────────────

@dataclass
class PatternResult:
    """Padroes extraidos de missoes passadas."""
    pattern_id: str
    sector: str
    intent: str
    successful_hooks: list[str] = field(default_factory=list)
    common_modules: list[str] = field(default_factory=list)
    failure_patterns: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    sample_count: int = 0
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        sector: str,
        intent: str,
        successful_hooks: list[str] | None = None,
        common_modules: list[str] | None = None,
        failure_patterns: list[str] | None = None,
        insights: list[str] | None = None,
        sample_count: int = 0,
    ) -> "PatternResult":
        return cls(
            pattern_id=_new_id("pat"),
            sector=sector,
            intent=intent,
            successful_hooks=successful_hooks or [],
            common_modules=common_modules or [],
            failure_patterns=failure_patterns or [],
            insights=insights or [],
            sample_count=sample_count,
        )

    @property
    def is_empty(self) -> bool:
        return self.sample_count == 0

    def to_dict(self) -> dict:
        return {
            "pattern_id": self.pattern_id,
            "sector": self.sector,
            "intent": self.intent,
            "successful_hooks": self.successful_hooks,
            "common_modules": self.common_modules,
            "failure_patterns": self.failure_patterns,
            "insights": self.insights,
            "sample_count": self.sample_count,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PatternResult":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
