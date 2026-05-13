"""P4 Memory Pack service — planner, context pack builder, ranker, writeback planner."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

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
    SOURCE_GRINGOTTS,
    SOURCE_BIBLIOTECA,
    SOURCE_SESSION,
    SOURCE_STATIC,
    VALID_SOURCES,
    VALID_SECTORS,
    VALID_RELEVANCES,
    VALID_FORMATS,
    VALID_WRITE_ACTIONS,
    RELEVANCE_RANK,
    RELEVANCE_EXACT,
    RELEVANCE_HIGH,
    RELEVANCE_MEDIUM,
    RELEVANCE_LOW,
    RELEVANCE_NONE,
    FORMAT_JSON,
    FORMAT_MARKDOWN,
    FORMAT_DICT,
    ACTION_UPSERT,
    ACTION_INSERT,
    ACTION_UPDATE,
    STATUS_DRAFT,
    STATUS_ACTIVE,
    _new_id,
)
from src.memory_pack.errors import (
    MemoryPackError,
    QueryValidationError,
    EmptyQueryError,
    InvalidSourceError,
    InvalidSectorError,
    ContextPackError,
    EmptyHitListError,
    RankingError,
    WritePlanError,
    DestructiveActionBlockedError,
    WritebackBlockedError,
    AkashaConnectionProhibitedError,
    ExportError,
    InvalidFormatError,
    SerializationError,
)


@dataclass
class MemoryPackPlanner:
    """Planejador central do Memory Pack — opera em modo dry-run por padrao.

    Nao realiza conexoes reais com Akasha, Postgres ou qualquer banco externo.
    Todas as operacoes sao de modelagem e planejamento.
    """

    sources: list[MemorySource] = field(default_factory=list)
    dry_run: bool = True

    @classmethod
    def create(cls) -> "MemoryPackPlanner":
        """Cria planner com as fontes padrao registradas (sem conexao real)."""
        default_sources = [
            MemorySource.new(
                source_type=SOURCE_AKASHA,
                label="Akasha pgvector",
                description="Base vetorial principal — 20K docs, 606K chunks",
                is_primary=True,
                priority=95,
            ),
            MemorySource.new(
                source_type=SOURCE_OBSIDIAN,
                label="Obsidian Vault",
                description="7.792 arquivos declarativos de conhecimento",
                is_primary=True,
                priority=90,
            ),
            MemorySource.new(
                source_type=SOURCE_MEM0,
                label="Mem0 + Kuzu",
                description="Grafo relacional de memoria (Qdrant :6333)",
                priority=80,
            ),
            MemorySource.new(
                source_type=SOURCE_GRINGOTTS,
                label="Gringotts",
                description="Schema de negocio unificado",
                priority=75,
            ),
            MemorySource.new(
                source_type=SOURCE_BIBLIOTECA,
                label="Biblioteca Sabedoria",
                description="376 livros, 5.917 insights",
                priority=70,
            ),
            MemorySource.new(
                source_type=SOURCE_SESSION,
                label="Session Memory",
                description="Contexto da sessao atual (efemero)",
                priority=60,
            ),
            MemorySource.new(
                source_type=SOURCE_STATIC,
                label="Static Knowledge",
                description="Conhecimento estatico embutido",
                priority=50,
            ),
        ]
        return cls(sources=default_sources, dry_run=True)

    def get_available_sources(self) -> list[MemorySource]:
        """Retorna fontes marcadas como disponiveis."""
        return [s for s in self.sources if s.is_available]

    def get_primary_sources(self) -> list[MemorySource]:
        """Retorna fontes primarias ordenadas por prioridade."""
        primary = [s for s in self.sources if s.is_primary and s.is_available]
        return sorted(primary, key=lambda s: s.priority, reverse=True)

    def validate_query(self, query: MemoryQuery) -> dict:
        """Valida uma query de memoria e retorna relatorio de validacao.

        Args:
            query: MemoryQuery a validar

        Returns:
            dict com chaves: valid, errors, warnings, suggestions
        """
        errors = []
        warnings = []
        suggestions = []

        if not query.text.strip():
            errors.append("Query text is empty")

        invalid_sources = [s for s in query.sources if s not in VALID_SOURCES]
        if invalid_sources:
            errors.append(f"Invalid sources: {invalid_sources}")

        invalid_sectors = [s for s in query.sectors if s not in VALID_SECTORS]
        if invalid_sectors:
            errors.append(f"Invalid sectors: {invalid_sectors}")

        if query.min_relevance not in VALID_RELEVANCES:
            errors.append(f"Invalid min_relevance: {query.min_relevance!r}")

        if query.max_hits < 1:
            errors.append(f"max_hits must be >= 1, got {query.max_hits}")

        if not query.sources:
            warnings.append("No sources specified — all available sources will be used")
            suggestions.append("Consider specifying sources for targeted retrieval")

        if not query.sectors:
            warnings.append("No sectors specified — cross-sector search")

        if query.max_hits > 50:
            warnings.append(f"Large max_hits ({query.max_hits}) may produce noise")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
        }

    def rank_hits(
        self,
        hits: list[MemoryHit],
        min_relevance: str = RELEVANCE_LOW,
        max_hits: int = 10,
    ) -> list[MemoryHit]:
        """Ranqueia hits por relevance e prioridade de fonte.

        Ordena por rank_score decrescente e filtra por relevancia minima.
        Empatia resolvida por prioridade da fonte.

        Args:
            hits: Lista de MemoryHit a ranquear
            min_relevance: Relevancia minima para inclusao
            max_hits: Numero maximo de hits retornados

        Returns:
            Lista ranqueada e truncada de MemoryHit
        """
        if min_relevance not in VALID_RELEVANCES:
            raise RankingError(
                f"Relevancia invalida: {min_relevance!r}. Deve ser uma de {sorted(VALID_RELEVANCES)}"
            )

        min_rank = RELEVANCE_RANK.get(min_relevance, 0)
        filtered = [h for h in hits if h.rank_score >= min_rank]

        source_priority = {s.source_type: s.priority for s in self.sources}

        def sort_key(hit: MemoryHit) -> tuple[int, int]:
            src_prio = source_priority.get(hit.source_type, 0)
            return (hit.rank_score, src_prio)

        ranked = sorted(filtered, key=sort_key, reverse=True)
        return ranked[:max_hits]

    def build_context_pack(
        self,
        query: MemoryQuery,
        hits: list[MemoryHit],
    ) -> ContextPack:
        """Monta um ContextPack a partir de uma query e seus hits.

        Args:
            query: MemoryQuery original
            hits: Lista de MemoryHit (ja ranqueados)

        Returns:
            ContextPack montado com texto agregado e metadados
        """
        if not hits:
            raise EmptyHitListError("hits list is empty — cannot build context pack")

        ranked = self.rank_hits(
            hits,
            min_relevance=query.min_relevance,
            max_hits=query.max_hits,
        )

        pack = ContextPack.new(query_id=query.query_id)
        pack.assemble(ranked)
        return pack

    def plan_memory_writeback(
        self,
        records: list[MissionMemoryRecord],
        target_source: str = SOURCE_AKASHA,
        action: str = ACTION_UPSERT,
        notes: str = "",
    ) -> MemoryWritePlan:
        """Planeja writeback de registros para uma fonte — nunca executa.

        Args:
            records: Registros a incluir no plano
            target_source: Fonte destino (default: akasha)
            action: Acao planejada (insert, update, upsert)
            notes: Notas do plano

        Returns:
            MemoryWritePlan descrevendo o que seria escrito
        """
        if target_source not in VALID_SOURCES:
            raise WritePlanError(
                f"Fonte invalida: {target_source!r}. Deve ser uma de {sorted(VALID_SOURCES)}"
            )

        plan = MemoryWritePlan.new(
            target_source=target_source,
            action=action,
            notes=notes or f"Writeback plan for {len(records)} records to {target_source}",
        )

        for record in records:
            plan.add_record(record)

        return plan

    def export_context_pack(
        self,
        pack: ContextPack,
        fmt: str = FORMAT_JSON,
    ) -> str:
        """Exporta um ContextPack no formato especificado.

        Args:
            pack: ContextPack a exportar
            fmt: Formato — json, markdown, ou dict

        Returns:
            String formatada ou JSON serializado
        """
        if fmt not in VALID_FORMATS:
            raise InvalidFormatError(
                f"Formato invalido: {fmt!r}. Deve ser um de {sorted(VALID_FORMATS)}"
            )

        if fmt == FORMAT_DICT:
            return json.dumps(pack.to_dict(), indent=2, ensure_ascii=False)

        if fmt == FORMAT_MARKDOWN:
            lines = [
                f"# Context Pack: {pack.pack_id}",
                f"",
                f"- **Query:** {pack.query_id}",
                f"- **Total Hits:** {pack.total_hits}",
                f"- **Sources:** {pack.total_sources}",
                f"- **Top Relevance:** {pack.top_relevance}",
                f"- **Dry Run:** {pack.dry_run}",
                f"- **Created:** {pack.created_at}",
                f"",
                f"## Source Summary",
                f"",
            ]
            for src, count in sorted(pack.source_summary.items()):
                lines.append(f"- {src}: {count} hit(s)")
            lines.append("")
            lines.append("## Assembled Context")
            lines.append("")
            lines.append(pack.assembled_text)
            return "\n".join(lines)

        # JSON format
        return json.dumps(pack.to_dict(), indent=2, ensure_ascii=False)

    def simulate_query(
        self,
        query: MemoryQuery,
    ) -> dict:
        """Simula uma query gerando hits sinteticos — para teste e validacao.

        Nao conecta com fonte real. Gera hits simulados com relevance baseada
        em matching textual simples (substring) contra titulos estaticos.

        Args:
            query: MemoryQuery com o texto de busca

        Returns:
            dict com query_id, hits gerados e metadata da simulacao
        """
        synthetic_titles = {
            SOURCE_AKASHA: [
                "Estrategia de conteudo para Instagram 2026",
                "Padroes virais detectados em Reels",
                "SEOgram otimizacao de legenda",
                "Historico de collabs com hoteis",
            ],
            SOURCE_OBSIDIAN: [
                "Nota diaria — comercial SDR hoteis",
                "Reflexao sobre precificacao de pacotes",
                "Aprendizados com cliente X",
            ],
            SOURCE_MEM0: [
                "Relacao: lucastigrereal → afamiliatigrereal",
                "Cluster de topicos: viagem familia",
            ],
            SOURCE_BIBLIOTECA: [
                "Livro: Marketing para hoteis",
                "Insight: Pricing psychology in tourism",
            ],
        }

        target_sources = query.sources or list(synthetic_titles.keys())
        hits = []

        for src in target_sources:
            if src not in synthetic_titles:
                continue
            src_priority = 50
            for s in self.sources:
                if s.source_type == src:
                    src_priority = s.priority
                    break
            for title in synthetic_titles[src]:
                query_words = set(query.text.lower().split())
                title_words = set(title.lower().split())
                overlap = query_words & title_words
                if overlap:
                    relevance = RELEVANCE_HIGH if len(overlap) >= 2 else RELEVANCE_MEDIUM
                else:
                    relevance = RELEVANCE_LOW

                hit = MemoryHit.new(
                    query_id=query.query_id,
                    source_type=src,
                    source_id=f"sim_{src}",
                    relevance=relevance,
                    title=title,
                    snippet=f"Simulated snippet for: {title}",
                )
                hits.append(hit)

        ranked = self.rank_hits(hits, query.min_relevance, query.max_hits)

        return {
            "query_id": query.query_id,
            "simulated": True,
            "total_hits_generated": len(hits),
            "hits_after_ranking": len(ranked),
            "hits": ranked,
        }

    def simulate_writeback(
        self,
        plan: MemoryWritePlan,
    ) -> dict:
        """Simula execucao de um write plan — nunca escreve de verdade.

        Args:
            plan: MemoryWritePlan a simular

        Returns:
            dict com resultado da simulacao
        """
        return {
            "plan_id": plan.plan_id,
            "simulated": True,
            "executed": False,
            "target_source": plan.target_source,
            "action": plan.action,
            "records_count": plan.record_count,
            "chunks_count": plan.chunk_count,
            "status": "dry_run_completed",
            "note": "Nenhuma escrita real foi realizada. Plano requer aprovacao.",
            "approval_required": plan.requires_approval,
        }


# ── Module-level convenience functions ─────────────────────────────────────

_default_planner: Optional[MemoryPackPlanner] = None


def _get_planner() -> MemoryPackPlanner:
    global _default_planner
    if _default_planner is None:
        _default_planner = MemoryPackPlanner.create()
    return _default_planner


def validate_memory_query(query: MemoryQuery) -> dict:
    """Valida uma query de memoria.

    Args:
        query: MemoryQuery a validar

    Returns:
        dict com chaves: valid, errors, warnings, suggestions
    """
    return _get_planner().validate_query(query)


def rank_memory_hits(
    hits: list[MemoryHit],
    min_relevance: str = RELEVANCE_LOW,
    max_hits: int = 10,
) -> list[MemoryHit]:
    """Ranqueia hits de memoria por relevancia.

    Args:
        hits: Lista de MemoryHit
        min_relevance: Relevancia minima
        max_hits: Maximo de hits retornados

    Returns:
        Lista ranqueada de MemoryHit
    """
    return _get_planner().rank_hits(hits, min_relevance, max_hits)


def build_context_pack(query: MemoryQuery, hits: list[MemoryHit]) -> ContextPack:
    """Monta ContextPack a partir de query e hits.

    Args:
        query: MemoryQuery original
        hits: Lista de MemoryHit

    Returns:
        ContextPack montado
    """
    return _get_planner().build_context_pack(query, hits)


def plan_memory_writeback(
    records: list[MissionMemoryRecord],
    target_source: str = SOURCE_AKASHA,
    action: str = ACTION_UPSERT,
    notes: str = "",
) -> MemoryWritePlan:
    """Planeja writeback para uma fonte — nunca executa.

    Args:
        records: Registros a planejar
        target_source: Fonte destino
        action: Acao planejada
        notes: Notas do plano

    Returns:
        MemoryWritePlan
    """
    return _get_planner().plan_memory_writeback(records, target_source, action, notes)


def export_context_pack(pack: ContextPack, fmt: str = FORMAT_JSON) -> str:
    """Exporta ContextPack no formato especificado.

    Args:
        pack: ContextPack a exportar
        fmt: Formato — json, markdown, ou dict

    Returns:
        String formatada
    """
    return _get_planner().export_context_pack(pack, fmt)
