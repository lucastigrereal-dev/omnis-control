"""MemoryInterface — wrapper limpo sobre as fontes de memória do OMNIS.

Isola os agentes dos detalhes de implementação (Akasha, pgvector, Obsidian).
Dry-run safe: sem IO externo se dry_run=True.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MemoryContext:
    """Resultado de uma consulta de memória para um agente."""

    mission_id: str
    account_handle: str
    intent: str
    hits: list[dict[str, object]] = field(default_factory=list)
    similar_captions: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    context_markdown: str = ""
    dry_run: bool = True

    @property
    def has_context(self) -> bool:
        return bool(self.hits or self.similar_captions or self.patterns)

    def to_dict(self) -> dict[str, object]:
        return {
            "mission_id": self.mission_id,
            "account_handle": self.account_handle,
            "intent": self.intent,
            "hits": self.hits,
            "similar_captions": self.similar_captions,
            "patterns": self.patterns,
            "context_markdown": self.context_markdown,
            "dry_run": self.dry_run,
        }


class MemoryInterface:
    """Interface unificada de memória para agentes OMNIS.

    Em dry_run=True retorna contexto stub sem IO real.
    Em dry_run=False tenta context_builder + learning_reuse.
    """

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    def query(
        self,
        mission_id: str,
        account_handle: str,
        intent: str,
        top_k: int = 5,
    ) -> MemoryContext:
        if self.dry_run:
            return self._stub_context(mission_id, account_handle, intent)
        return self._real_query(mission_id, account_handle, intent, top_k)

    # ── internals ───────────────────────────────────────────────────────

    def _stub_context(
        self, mission_id: str, account_handle: str, intent: str
    ) -> MemoryContext:
        return MemoryContext(
            mission_id=mission_id,
            account_handle=account_handle,
            intent=intent,
            hits=[],
            similar_captions=[],
            patterns=["dry_run_stub"],
            context_markdown=f"# Contexto stub\nMissão: {mission_id}\nConta: {account_handle}\nIntenção: {intent}",
            dry_run=True,
        )

    def _real_query(
        self, mission_id: str, account_handle: str, intent: str, top_k: int
    ) -> MemoryContext:
        hits: list[dict[str, object]] = []
        similar_captions: list[str] = []
        patterns: list[str] = []

        try:
            from src.memory.context_builder import ContextBuilder  # type: ignore
            cb = ContextBuilder()
            result = cb.build(
                mission_id=mission_id,
                account_handle=account_handle,
                intent=intent,
            )
            hits = result.sources_used  # type: ignore[assignment]
            patterns = ["context_builder_ok"]
        except Exception:
            patterns.append("context_builder_unavailable")

        try:
            from src.memory.learning_reuse import LearningReuse  # type: ignore
            lr = LearningReuse()
            reuse = lr.find_similar(account_handle=account_handle, intent=intent, top_k=top_k)
            similar_captions = [r.get("text", "") for r in (reuse or [])]
        except Exception:
            patterns.append("learning_reuse_unavailable")

        context_md = (
            f"# Contexto real\nMissão: {mission_id}\nConta: {account_handle}\n"
            f"Intenção: {intent}\nFontes: {len(hits)}\nSimilares: {len(similar_captions)}"
        )

        return MemoryContext(
            mission_id=mission_id,
            account_handle=account_handle,
            intent=intent,
            hits=hits,
            similar_captions=similar_captions,
            patterns=patterns,
            context_markdown=context_md,
            dry_run=False,
        )
