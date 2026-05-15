"""Memory Context Builder — builds 02_context_used.md from MemoryIntelligence queries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ContextResult:
    """Result of a context-building operation — the filled 02_context_used.md content."""

    mission_id: str
    account_handle: str = ""
    intent: str = ""
    sector: str = ""
    context_markdown: str = ""
    sources_used: list[str] = field(default_factory=list)
    hits_count: int = 0
    top_relevance: str = ""
    similar_missions_count: int = 0
    patterns_detected: bool = False
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "account_handle": self.account_handle,
            "intent": self.intent,
            "sector": self.sector,
            "context_markdown": self.context_markdown,
            "sources_used": self.sources_used,
            "hits_count": self.hits_count,
            "top_relevance": self.top_relevance,
            "similar_missions_count": self.similar_missions_count,
            "patterns_detected": self.patterns_detected,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }


class MemoryContextBuilder:
    """Builds populated 02_context_used.md by querying MemoryIntelligence.

    Integrates Mission OS contracts with the Memory layer.
    """

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    def build(
        self,
        mission_id: str,
        intent: str,
        sector: str,
        account_handle: str = "",
        tags: Optional[list[str]] = None,
        max_hits: int = 8,
    ) -> ContextResult:
        from src.memory_intel.service import MemoryIntelligence

        mi = MemoryIntelligence(dry_run=self.dry_run)

        try:
            retrieval = mi.retrieve(
                intent=intent,
                sector=sector,
                mission_id=mission_id,
                max_hits=max_hits,
                tags=tags,
            )
        except Exception:
            return ContextResult(
                mission_id=mission_id,
                account_handle=account_handle,
                intent=intent,
                sector=sector,
                context_markdown=self._empty_context(mission_id, account_handle, intent),
                sources_used=[],
            )

        pack = retrieval.pack
        md = self._build_markdown(
            mission_id=mission_id,
            account_handle=account_handle,
            intent=intent,
            sector=sector,
            pack_hits=[h.to_dict() for h in pack.hits],
            assembled_text=pack.assembled_text,
            source_summary=pack.source_summary,
            similar_missions=[s.to_dict() for s in retrieval.similar_missions],
            patterns=retrieval.patterns,
        )

        return ContextResult(
            mission_id=mission_id,
            account_handle=account_handle,
            intent=intent,
            sector=sector,
            context_markdown=md,
            sources_used=list(pack.source_summary.keys()),
            hits_count=pack.total_hits,
            top_relevance=pack.top_relevance,
            similar_missions_count=retrieval.similarity_count,
            patterns_detected=bool(retrieval.patterns.get("sample_count", 0) > 0),
            dry_run=self.dry_run,
        )

    def build_minimal(
        self,
        mission_id: str,
        intent: str,
        sector: str,
        account_handle: str = "",
    ) -> ContextResult:
        """Quick context without similarity/patterns (faster)."""
        from src.memory_intel.service import MemoryIntelligence

        mi = MemoryIntelligence(dry_run=self.dry_run)
        try:
            pack = mi.retrieve_context(intent=intent, sector=sector, max_hits=5)
        except Exception:
            return ContextResult(
                mission_id=mission_id,
                account_handle=account_handle,
                intent=intent,
                sector=sector,
                context_markdown=self._empty_context(mission_id, account_handle, intent),
            )

        md = self._build_markdown(
            mission_id=mission_id,
            account_handle=account_handle,
            intent=intent,
            sector=sector,
            pack_hits=[h.to_dict() for h in pack.hits],
            assembled_text=pack.assembled_text,
            source_summary=pack.source_summary,
        )

        return ContextResult(
            mission_id=mission_id,
            account_handle=account_handle,
            intent=intent,
            sector=sector,
            context_markdown=md,
            sources_used=list(pack.source_summary.keys()),
            hits_count=pack.total_hits,
            top_relevance=pack.top_relevance,
            dry_run=self.dry_run,
        )

    def _build_markdown(
        self,
        mission_id: str,
        account_handle: str,
        intent: str,
        sector: str,
        pack_hits: list[dict],
        assembled_text: str,
        source_summary: dict,
        similar_missions: list[dict] | None = None,
        patterns: dict | None = None,
    ) -> str:
        similar_missions = similar_missions or []
        patterns = patterns or {}

        lines = [
            f"# Contexto Usado — {mission_id}",
            "",
            f"**Conta:** @{account_handle or 'nao informada'}",
            f"**Intent:** {intent}",
            f"**Setor:** {sector}",
            f"**Data:** {_now_iso()}",
            "",
            "## Fontes consultadas",
            "",
        ]

        for src, count in sorted(source_summary.items()):
            lines.append(f"- {src}: {count} hits")

        if not source_summary:
            lines.append("- (nenhuma fonte disponivel — simulacao dry-run)")

        lines.extend([
            "",
            "## Hits relevantes",
            "",
        ])

        for h in pack_hits:
            title = h.get("title", "sem titulo")
            relevance = h.get("relevance", "low")
            snippet = h.get("snippet", "")
            source = h.get("source_type", "desconhecido")
            lines.append(f"### [{source}:{relevance}] {title}")
            lines.append("")
            if snippet:
                lines.append(f"> {snippet}")
            lines.append("")

        if assembled_text:
            lines.extend([
                "## Texto consolidado",
                "",
                assembled_text,
                "",
            ])

        if similar_missions:
            lines.extend([
                "## Missoes similares",
                "",
            ])
            for sim in similar_missions[:5]:
                sm = sim.get("source_mission", {})
                score = sim.get("similarity_score", 0)
                title = sm.get("title", "?")
                insights = sim.get("relevant_learnings", [])
                lines.append(f"- [{score:.0%}] {title}")
                for ins in insights[:3]:
                    lines.append(f"  - {ins}")
            lines.append("")

        if patterns.get("sample_count", 0) > 0:
            lines.extend([
                "## Padroes detectados",
                "",
                f"- Amostras: {patterns.get('sample_count', 0)}",
            ])
            for hook in patterns.get("successful_hooks", [])[:3]:
                lines.append(f"- Hook: {hook}")
            for insight in patterns.get("insights", [])[:3]:
                lines.append(f"- Insight: {insight}")
            lines.append("")

        return "\n".join(lines)

    def _empty_context(self, mission_id: str, account_handle: str, intent: str) -> str:
        return f"""# Contexto Usado — {mission_id}

**Conta:** @{account_handle or 'nao informada'}
**Intent:** {intent}

## Fontes consultadas

- (nenhuma — memoria offline ou erro no retrieval)

## Contexto

> Contexto nao disponivel nesta execucao. Preencher manualmente se necessario.
"""
