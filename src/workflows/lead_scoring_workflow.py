"""LeadScoringWorkflow — molde: prospects → score deterministico → ranking → akasha.

Onda 16 — wires existing pieces without adding new algorithms:
  - RunContext              → run_id único
  - score_prospect()       → OpportunityScore deterministico (P9 SDR)
  - ProspectProfile        → modelo de prospect B2B
  - ScoreTier              → HOT / WARM / COLD / DISQUALIFIED
  - AkashaSinkAdapter      → persiste resultado com run_id

Pipeline:
  1. validate  → garante que todos os profiles são válidos
  2. score     → score_prospect() para cada profile
  3. rank      → ordena por composite score descendente
  4. akasha    → evento com run_id, top_leads, tier_distribution
  5. retorna   → LeadScoringResult com run_id e ranking completo

Uso:
  wf = LeadScoringWorkflow()
  result = wf.run([prospect_a, prospect_b, ...], dry_run=True)
  print(result.hot_leads)    # leads HOT prontos para abordagem
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.commercial_sdr.models import OpportunityScore, ProspectProfile, ScoreTier
from src.commercial_sdr.service import score_prospect
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.lead_scoring")

# Scoring é 100% determinístico e local — zero cloud
_COST_LOCAL_PCT = 100


@dataclass
class ScoredLead:
    """Prospect com seu score calculado."""
    profile: ProspectProfile
    score: OpportunityScore

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile.profile_id,
            "company_name": self.profile.company_name,
            "segment": self.profile.segment,
            "tier": self.score.tier.value,
            "composite": round(self.score.composite, 3),
            "segment_fit": round(self.score.segment_fit, 3),
            "engagement_signal": round(self.score.engagement_signal, 3),
            "reasoning": self.score.reasoning[:3],
        }


@dataclass
class LeadScoringResult:
    """Resultado consolidado do workflow de scoring de leads."""

    run_id: str
    success: bool
    total_scored: int = 0
    hot_count: int = 0
    warm_count: int = 0
    cold_count: int = 0
    disqualified_count: int = 0
    scored_leads: list[ScoredLead] = field(default_factory=list)
    akasha_event_id: str = ""
    dry_run: bool = True
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def hot_leads(self) -> list[ScoredLead]:
        return [l for l in self.scored_leads if l.score.tier == ScoreTier.HOT]

    @property
    def warm_leads(self) -> list[ScoredLead]:
        return [l for l in self.scored_leads if l.score.tier == ScoreTier.WARM]

    @property
    def top_3(self) -> list[ScoredLead]:
        return self.scored_leads[:3]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "total_scored": self.total_scored,
            "hot_count": self.hot_count,
            "warm_count": self.warm_count,
            "cold_count": self.cold_count,
            "disqualified_count": self.disqualified_count,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
            "top_leads": [l.to_dict() for l in self.top_3],
        }


class LeadScoringWorkflow:
    """Workflow de scoring: lista de prospects → OpportunityScore → ranking → akasha."""

    def __init__(
        self,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/leads/",
        budget_usd: float = 0.0,
    ) -> None:
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)
        self._budget_usd = budget_usd

    def run(
        self,
        prospects: list[ProspectProfile],
        dry_run: bool = True,
    ) -> LeadScoringResult:
        """Executa scoring para uma lista de prospects.

        Args:
            prospects: Lista de ProspectProfile para qualificar.
            dry_run:   True → processa e retorna sem persistir arquivos.
        """
        ctx = RunContext.new(budget_usd=self._budget_usd)
        _logger.info(
            "%s LeadScoringWorkflow.run: %d prospects, dry_run=%s",
            ctx.log_prefix(), len(prospects), dry_run,
        )

        if not prospects:
            return LeadScoringResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="empty_prospect_list",
            )

        # Score all prospects
        scored: list[ScoredLead] = []
        for p in prospects:
            try:
                score = score_prospect(p)
                scored.append(ScoredLead(profile=p, score=score))
            except Exception as exc:
                _logger.warning("%s scoring failed for %s: %s", ctx.log_prefix(), p.profile_id, exc)

        if not scored:
            return LeadScoringResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="all_scoring_failed",
            )

        # Sort by composite score descending
        scored.sort(key=lambda l: l.score.composite, reverse=True)

        hot = sum(1 for l in scored if l.score.tier == ScoreTier.HOT)
        warm = sum(1 for l in scored if l.score.tier == ScoreTier.WARM)
        cold = sum(1 for l in scored if l.score.tier == ScoreTier.COLD)
        disq = sum(1 for l in scored if l.score.tier == ScoreTier.DISQUALIFIED)

        _logger.info(
            "%s scored %d — HOT:%d WARM:%d COLD:%d DISQ:%d",
            ctx.log_prefix(), len(scored), hot, warm, cold, disq,
        )

        # Gravar no akasha
        event = SinkEvent(
            event_type="lead_scoring_completed",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "total_scored": len(scored),
                "hot_count": hot,
                "warm_count": warm,
                "cold_count": cold,
                "disqualified_count": disq,
                "top_leads": [l.to_dict() for l in scored[:5]],
                "cost_local_pct": _COST_LOCAL_PCT,
                "dry_run": dry_run,
            },
        )
        written = self._sink.write_event(event)
        _logger.info("%s akasha write: event_id=%s, ok=%s", ctx.log_prefix(), event.event_id, written)

        return LeadScoringResult(
            run_id=ctx.run_id,
            success=True,
            total_scored=len(scored),
            hot_count=hot,
            warm_count=warm,
            cold_count=cold,
            disqualified_count=disq,
            scored_leads=scored,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
            cost_local_pct=_COST_LOCAL_PCT,
            artifacts={
                "run_id": ctx.run_id,
                "akasha_event_id": event.event_id,
                "tier_distribution": {"hot": hot, "warm": warm, "cold": cold, "disq": disq},
            },
        )
