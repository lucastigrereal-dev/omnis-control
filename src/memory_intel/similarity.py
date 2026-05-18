"""P21 Memory Intelligence — similarity matching and pattern extraction."""
from __future__ import annotations

from typing import Optional

from src.memory_intel.models import (
    MissionSimilarityResult,
    SIMILARITY_WEIGHT_INTENT,
    SIMILARITY_WEIGHT_SECTOR,
    SIMILARITY_WEIGHT_TAGS,
    SIMILARITY_WEIGHT_MODULES,
)
from src.memory_pack.models import MissionMemoryRecord


def find_similar_missions(
    intent: str,
    sector: str,
    tags: list[str],
    past_records: list[MissionMemoryRecord],
    limit: int = 5,
    embedding_provider=None,  # Optional EmbeddingProvider for semantic scoring
) -> list[MissionSimilarityResult]:
    """Calcula similaridade entre uma nova missao e registros passados.

    Score = weighted sum:
      - mesmo intent:      +0.40
      - mesmo sector:      +0.30
      - overlap de tags:   +0.20 (proporcional)
      - modulos em comum:  +0.10 (proporcional)

    Args:
        intent: Tipo da nova missao
        sector: Setor da nova missao
        tags: Tags da nova missao
        past_records: Registros historicos para comparar
        limit: Maximo de resultados

    Returns:
        Lista ranqueada de MissionSimilarityResult
    """
    # Build semantic index once if embedder available
    query_text = f"{intent} {sector} {' '.join(tags)}"
    semantic_scores: dict[str, float] = {}
    if embedding_provider and past_records:
        try:
            record_texts = [f"{r.metadata.get('intent','')} {r.sector} {' '.join(r.tags)}" for r in past_records]
            ranked = embedding_provider.rank(query_text, record_texts, k=len(past_records))
            for text, score in ranked:
                idx = next((i for i, t in enumerate(record_texts) if t == text), None)
                if idx is not None:
                    semantic_scores[past_records[idx].mission_id] = score
        except Exception:
            pass  # Fall back to rule-based scoring

    results: list[MissionSimilarityResult] = []

    for record in past_records:
        score = 0.0
        matched_on: list[str] = []

        # Intent match
        record_intent = record.metadata.get("intent", "")
        if record_intent and record_intent == intent:
            score += SIMILARITY_WEIGHT_INTENT
            matched_on.append("intent")

        # Sector match
        if record.sector == sector:
            score += SIMILARITY_WEIGHT_SECTOR
            matched_on.append("sector")

        # Tags overlap
        if tags and record.tags:
            tag_overlap = len(set(tags) & set(record.tags))
            if tag_overlap > 0:
                score += SIMILARITY_WEIGHT_TAGS * (tag_overlap / max(len(tags), 1))
                matched_on.append("tags")

        # Modules common (check tags + metadata for module references)
        record_modules = {t for t in record.tags if t.startswith(("P", "src/"))}
        request_modules = {t for t in tags if t.startswith(("P", "src/"))}
        if record_modules and request_modules:
            module_overlap = len(record_modules & request_modules)
            if module_overlap > 0:
                score += SIMILARITY_WEIGHT_MODULES * (module_overlap / max(len(request_modules), 1))
                matched_on.append("modules")

        # Blend semantic score when available (60% semantic + 40% rule-based)
        if record.mission_id in semantic_scores:
            blended = 0.6 * semantic_scores[record.mission_id] + 0.4 * min(score, 1.0)
            matched_on.append("semantic")
        else:
            blended = min(score, 1.0)

        results.append(
            MissionSimilarityResult.new(
                source_mission=record,
                similarity_score=round(blended, 3),
                matched_on=matched_on,
                relevant_learnings=list(record.key_insights),
            )
        )

    results.sort(key=lambda r: r.similarity_score, reverse=True)
    return results[:limit]


def compute_similarity_score(
    intent: str,
    sector: str,
    tags: list[str],
    record: MissionMemoryRecord,
) -> float:
    """Calcula score de similaridade para um unico registro.

    Args:
        intent: Tipo da nova missao
        sector: Setor da nova missao
        tags: Tags da nova missao
        record: Registro a comparar

    Returns:
        Score entre 0.0 e 1.0
    """
    score = 0.0

    record_intent = record.metadata.get("intent", "")
    if record_intent and record_intent == intent:
        score += SIMILARITY_WEIGHT_INTENT

    if record.sector == sector:
        score += SIMILARITY_WEIGHT_SECTOR

    if tags and record.tags:
        tag_overlap = len(set(tags) & set(record.tags))
        if tag_overlap > 0:
            score += SIMILARITY_WEIGHT_TAGS * (tag_overlap / max(len(tags), 1))

    return round(min(score, 1.0), 2)
