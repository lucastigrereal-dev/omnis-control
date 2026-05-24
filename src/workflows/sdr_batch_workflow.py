"""SDRBatchWorkflow — pipeline completo: prospects → score → outreach → akasha.

Onda 19 — integra LeadScoringWorkflow + OutreachSequenceWorkflow sem adicionar
novos algoritmos:
  - RunContext         → run_id único
  - score_prospect()   → filtra HOT+WARM antes de gerar sequências
  - build_outreach_sequence() → sequências para leads qualificados
  - AkashaSinkAdapter  → persiste resultado com run_id

Pipeline:
  1. score   → score_prospect() para todos os prospects
  2. filter  → mantém apenas HOT + WARM (os leads acionáveis)
  3. sequence → build_outreach_sequence() para cada lead qualificado
  4. akasha  → evento com run_id, tier counts, sequences_count
  5. retorna → SDRBatchResult com ranking + sequências

Uso (pipeline completo SDR — zero LLM):
  wf = SDRBatchWorkflow()
  result = wf.run([prospect_a, prospect_b, ...], dry_run=True)
  print(result.actionable_count)  # leads HOT+WARM com sequências geradas
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.commercial_sdr.models import OpportunityScore, OutreachSequence, ProspectProfile, ScoreTier
from src.commercial_sdr.service import build_outreach_sequence, score_prospect
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.sdr_batch")

_COST_LOCAL_PCT = 100
_ACTIONABLE_TIERS = frozenset({ScoreTier.HOT, ScoreTier.WARM})


@dataclass
class SDRLead:
    """Prospect com score + sequência de outreach."""
    profile: ProspectProfile
    score: OpportunityScore
    sequence: OutreachSequence | None = None

    @property
    def is_actionable(self) -> bool:
        return self.score.tier in _ACTIONABLE_TIERS

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile.profile_id,
            "company_name": self.profile.company_name,
            "segment": self.profile.segment,
            "tier": self.score.tier.value,
            "composite": round(self.score.composite, 3),
            "has_sequence": self.sequence is not None,
            "steps_count": len(self.sequence.steps) if self.sequence else 0,
        }


@dataclass
class SDRBatchResult:
    """Resultado consolidado do pipeline SDR completo."""

    run_id: str
    success: bool
    total_prospects: int = 0
    leads: list[SDRLead] = field(default_factory=list)
    akasha_event_id: str = ""
    dry_run: bool = True
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def scored_count(self) -> int:
        return len(self.leads)

    @property
    def actionable_count(self) -> int:
        return sum(1 for l in self.leads if l.is_actionable)

    @property
    def hot_leads(self) -> list[SDRLead]:
        return [l for l in self.leads if l.score.tier == ScoreTier.HOT]

    @property
    def warm_leads(self) -> list[SDRLead]:
        return [l for l in self.leads if l.score.tier == ScoreTier.WARM]

    @property
    def cold_leads(self) -> list[SDRLead]:
        return [l for l in self.leads if l.score.tier == ScoreTier.COLD]

    @property
    def sequences_generated(self) -> int:
        return sum(1 for l in self.leads if l.sequence is not None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "total_prospects": self.total_prospects,
            "scored_count": self.scored_count,
            "actionable_count": self.actionable_count,
            "sequences_generated": self.sequences_generated,
            "hot_count": len(self.hot_leads),
            "warm_count": len(self.warm_leads),
            "cold_count": len(self.cold_leads),
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
            "leads": [l.to_dict() for l in self.leads],
        }


class SDRBatchWorkflow:
    """Pipeline SDR: prospects → score → filter HOT+WARM → outreach → akasha."""

    def __init__(
        self,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/sdr_batch/",
        budget_usd: float = 0.0,
    ) -> None:
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)
        self._budget_usd = budget_usd

    def run(
        self,
        prospects: list[ProspectProfile],
        dry_run: bool = True,
        sequence_tiers: frozenset[ScoreTier] = _ACTIONABLE_TIERS,
    ) -> SDRBatchResult:
        """Executa pipeline SDR completo para uma lista de prospects.

        Args:
            prospects:      Lista de ProspectProfile para qualificar.
            dry_run:        True → processa e retorna sem persistir arquivos.
            sequence_tiers: Tiers que recebem sequência de outreach (default: HOT+WARM).
        """
        ctx = RunContext.new(budget_usd=self._budget_usd)
        _logger.info(
            "%s SDRBatchWorkflow.run: %d prospects, dry_run=%s",
            ctx.log_prefix(), len(prospects), dry_run,
        )

        if not prospects:
            return SDRBatchResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="empty_prospect_list",
            )

        leads: list[SDRLead] = []

        for p in prospects:
            try:
                score = score_prospect(p)
                lead = SDRLead(profile=p, score=score)

                if score.tier in sequence_tiers:
                    try:
                        lead.sequence = build_outreach_sequence(p)
                    except Exception as seq_exc:
                        _logger.warning(
                            "%s sequence failed for %s: %s",
                            ctx.log_prefix(), p.profile_id, seq_exc,
                        )

                leads.append(lead)
            except Exception as exc:
                _logger.warning(
                    "%s scoring failed for %s: %s", ctx.log_prefix(), p.profile_id, exc
                )

        if not leads:
            return SDRBatchResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="all_scoring_failed",
            )

        leads.sort(key=lambda l: l.score.composite, reverse=True)

        actionable = sum(1 for l in leads if l.is_actionable)
        sequences = sum(1 for l in leads if l.sequence is not None)
        hot = sum(1 for l in leads if l.score.tier == ScoreTier.HOT)
        warm = sum(1 for l in leads if l.score.tier == ScoreTier.WARM)
        cold = sum(1 for l in leads if l.score.tier == ScoreTier.COLD)
        disq = sum(1 for l in leads if l.score.tier == ScoreTier.DISQUALIFIED)

        _logger.info(
            "%s SDR batch: %d scored, %d actionable, %d sequences — HOT:%d WARM:%d COLD:%d DISQ:%d",
            ctx.log_prefix(), len(leads), actionable, sequences, hot, warm, cold, disq,
        )

        event = SinkEvent(
            event_type="sdr_batch_completed",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "total_prospects": len(prospects),
                "scored_count": len(leads),
                "actionable_count": actionable,
                "sequences_generated": sequences,
                "hot_count": hot,
                "warm_count": warm,
                "cold_count": cold,
                "disqualified_count": disq,
                "cost_local_pct": _COST_LOCAL_PCT,
                "dry_run": dry_run,
            },
        )
        written = self._sink.write_event(event)
        _logger.info(
            "%s akasha write: event_id=%s, ok=%s", ctx.log_prefix(), event.event_id, written
        )

        return SDRBatchResult(
            run_id=ctx.run_id,
            success=True,
            total_prospects=len(prospects),
            leads=leads,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
            cost_local_pct=_COST_LOCAL_PCT,
            artifacts={
                "run_id": ctx.run_id,
                "akasha_event_id": event.event_id,
                "actionable_count": actionable,
                "sequences_generated": sequences,
            },
        )
