"""DeepResearchWorkflow — molde ponta a ponta: tópico → STORM → akasha.

Wires existing OMNIS pieces without adding new algorithms:
  - RunContext (Onda 7)  → run_id único + teto de custo
  - ResearchConductorLego → pipeline STORM (perspectivas → artigo → citações)
  - AkashaSinkAdapter     → persiste evento com run_id no payload
  - cost_local_pct        → velocímetro local/cloud

Nenhuma nova lógica — apenas o molde que coordena as peças existentes.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.utils.run_context import RunContext
from src.interfaces.research_conductor import ResearchSpec, ResearchCitation, ResearchPerspective
from src.legos.research_conductor_lego import ResearchConductorLego
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent

_logger = logging.getLogger("omnis.workflows.deep_research")


@dataclass
class DeepResearchResult:
    """Resultado consolidado do workflow ponta a ponta."""

    run_id: str
    success: bool
    topic: str = ""
    report: str = ""
    citations: list[ResearchCitation] = field(default_factory=list)
    perspectives: list[ResearchPerspective] = field(default_factory=list)
    cost_local_pct: int = 0
    files_created: list[str] = field(default_factory=list)
    akasha_event_id: str = ""
    dry_run: bool = True
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def citation_count(self) -> int:
        return len(self.citations)

    @property
    def perspective_count(self) -> int:
        return len(self.perspectives)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "topic": self.topic,
            "report_chars": len(self.report),
            "citation_count": self.citation_count,
            "perspective_count": self.perspective_count,
            "cost_local_pct": self.cost_local_pct,
            "files_created": self.files_created,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "error": self.error,
            "artifacts": self.artifacts,
        }


class DeepResearchWorkflow:
    """Workflow ponta a ponta: tópico → STORM → akasha.

    Injeção de dependências para facilitar testes:
      research_lego  → ResearchConductorLego (default: instância padrão)
      akasha_sink    → AkashaSinkAdapter (default: FileAkashaSink dry_run=True)
    """

    def __init__(
        self,
        research_lego: ResearchConductorLego | None = None,
        akasha_sink: AkashaSinkAdapter | None = None,
        output_dir: str = "output/research/",
        akasha_dir: str = "output/akasha/research/",
        budget_usd: float = 0.0,
    ) -> None:
        self._lego = research_lego or ResearchConductorLego()
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)
        self._output_dir = output_dir
        self._budget_usd = budget_usd

    def run(
        self,
        topic: str,
        max_perspectives: int = 3,
        dry_run: bool = True,
    ) -> DeepResearchResult:
        """Executa o workflow completo para um tópico.

        Args:
            topic: O que pesquisar.
            max_perspectives: Quantas perspectivas STORM gerar.
            dry_run: True → retorna plano sem chamar LLM real nem criar arquivos.
        """
        ctx = RunContext.new(budget_usd=self._budget_usd)
        _logger.info("%s DeepResearchWorkflow.run: topic='%s', dry_run=%s", ctx.log_prefix(), topic[:80], dry_run)

        spec = ResearchSpec(
            topic=topic,
            max_perspectives=max_perspectives,
            dry_run=dry_run,
            output_dir=self._output_dir if not dry_run else "",
            store_in_akasha=False,
            extra={"run_id": ctx.run_id},
        )

        research = self._lego.execute(spec)

        if not research.success:
            _logger.warning("%s research failed: %s", ctx.log_prefix(), research.error)
            return DeepResearchResult(
                run_id=ctx.run_id,
                success=False,
                topic=topic,
                dry_run=dry_run,
                error=research.error,
            )

        cost_local = research.artifacts.get("cost_local_pct", 0)
        _logger.info(
            "%s research OK — perspectives=%d, citations=%d, cost_local=%d%%",
            ctx.log_prefix(), research.perspective_count, research.citation_count, cost_local,
        )

        event = SinkEvent(
            event_type="deep_research_completed",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "topic": topic,
                "report": research.report,
                "citation_count": research.citation_count,
                "perspective_count": research.perspective_count,
                "cost_local_pct": cost_local,
                "llm_model": research.artifacts.get("llm_model", ""),
                "search_backend": research.artifacts.get("search_backend", "null"),
                "dry_run": dry_run,
                "files_created": research.files_created,
            },
        )
        written = self._sink.write_event(event)
        _logger.info("%s akasha write: event_id=%s, ok=%s", ctx.log_prefix(), event.event_id, written)

        return DeepResearchResult(
            run_id=ctx.run_id,
            success=True,
            topic=topic,
            report=research.report,
            citations=research.citations,
            perspectives=research.perspectives,
            cost_local_pct=cost_local,
            files_created=research.files_created,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
            artifacts={
                **research.artifacts,
                "run_id": ctx.run_id,
                "akasha_event_id": event.event_id,
            },
        )
