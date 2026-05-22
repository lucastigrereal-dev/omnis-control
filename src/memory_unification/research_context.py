"""ResearchContext — enriched context for content generation based on memory queries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.memory_unification.memory_router import MemoryRouter, MemoryQueryResult


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ResearchContext:
    """Context gathered from memory sources before content generation.

    Feeds into CaptionFactory to produce more relevant, higher-engagement captions.
    """

    topic: str = ""
    page: str = ""

    # Filled from memory queries
    top_hooks: list[str] = field(default_factory=list)
    saturated_themes: list[str] = field(default_factory=list)
    viral_patterns: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    audience_notes: list[str] = field(default_factory=list)

    # Metadata
    sources_queried: list[str] = field(default_factory=list)
    sources_failed: list[str] = field(default_factory=list)
    query_time_ms: int = 0
    generated_at: str = field(default_factory=_now_iso)

    @property
    def is_empty(self) -> bool:
        return not any([self.top_hooks, self.insights, self.viral_patterns])

    @property
    def enrichment_summary(self) -> str:
        """One-line summary of what was found."""
        parts = []
        if self.top_hooks:
            parts.append(f"{len(self.top_hooks)} hooks")
        if self.insights:
            parts.append(f"{len(self.insights)} insights")
        if self.saturated_themes:
            parts.append(f"{len(self.saturated_themes)} temas saturados")
        if self.viral_patterns:
            parts.append(f"{len(self.viral_patterns)} padrões virais")
        return ", ".join(parts) if parts else "nenhum dado encontrado"

    def to_prompt_hint(self) -> str:
        """Convert research context into a prompt hint for the LLM."""
        lines = ["[CONTEXTO DE PESQUISA — use para enriquecer a legenda]"]
        if self.top_hooks:
            lines.append(f"Hooks que engajaram neste nicho: {' | '.join(self.top_hooks[:3])}")
        if self.saturated_themes:
            lines.append(f"EVITAR temas saturados: {' | '.join(self.saturated_themes[:3])}")
        if self.viral_patterns:
            lines.append(f"Padrões virais: {' | '.join(self.viral_patterns[:3])}")
        if self.insights:
            lines.append(f"Insights relevantes: {' | '.join(self.insights[:3])}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "page": self.page,
            "top_hooks": self.top_hooks,
            "saturated_themes": self.saturated_themes,
            "viral_patterns": self.viral_patterns,
            "insights": self.insights,
            "audience_notes": self.audience_notes,
            "sources_queried": self.sources_queried,
            "sources_failed": self.sources_failed,
            "query_time_ms": self.query_time_ms,
            "enrichment_summary": self.enrichment_summary,
            "generated_at": self.generated_at,
        }


class ResearchContextBuilder:
    """Builds a ResearchContext by querying memory sources."""

    def __init__(self, router: MemoryRouter | None = None, dry_run: bool = True):
        self.router = router or MemoryRouter(dry_run=dry_run)
        self.dry_run = dry_run

    def build(self, topic: str, page: str = "") -> ResearchContext:
        """Query memory sources and build a ResearchContext."""
        import time
        t0 = time.perf_counter()

        ctx = ResearchContext(topic=topic, page=page)

        # Query 1: hooks + patterns for this niche
        hooks_result = self.router.query(
            f"{topic} hooks engajamento alto",
            sources=["akasha", "qdrant"],
            top_k=8,
        )
        ctx.top_hooks = hooks_result.top_hooks
        ctx.saturated_themes = hooks_result.saturated_themes
        ctx.viral_patterns = hooks_result.viral_patterns
        ctx.sources_queried.extend(hooks_result.sources_queried)
        ctx.sources_failed.extend(hooks_result.sources_failed)

        # Query 2: insights from books + obsidian
        insights_result = self.router.query(
            f"{topic} psicologia comportamento memória afetiva",
            sources=["biblioteca", "obsidian"],
            top_k=6,
        )
        ctx.insights = insights_result.insights
        ctx.sources_queried.extend(insights_result.sources_queried)
        ctx.sources_failed.extend(insights_result.sources_failed)

        ctx.query_time_ms = int((time.perf_counter() - t0) * 1000)
        return ctx
