"""SDRPipelineWorkflow — consolida OutreachSequence + SDRBatch + SDRPlan.

Onda Consolidação — substitui 3 workflows por 1 com modo explícito:
  - mode="execute": score → filter HOT+WARM → outreach por lead (ex-SDRBatch)
  - mode="plan":    build_batch_plan com título/descrição (ex-SDRPlan)

OutreachSequence (outreach sem scoring) está subsumo pelo execute mode.

Uso:
  # Execute — pipeline completo
  wf = SDRPipelineWorkflow()
  result = wf.run(prospects, mode="execute", dry_run=True)
  print(result.actionable_count)

  # Plan — documento formalizado
  result = wf.run(prospects, mode="plan", title="Natal Jun/2026", dry_run=True)
  print(result.plan_id)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.commercial_sdr.models import (
    OpportunityScore, OutreachSequence, ProspectProfile, SDRPlan, ScoreTier,
)
from src.commercial_sdr.service import (
    build_batch_plan, build_outreach_sequence, score_prospect,
)
from src.commercial_sdr.errors import EmptyProspectListError
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.sdr_pipeline")

_COST_LOCAL_PCT = 100
_ACTIONABLE_TIERS = frozenset({ScoreTier.HOT, ScoreTier.WARM})
_VALID_MODES = frozenset({"execute", "plan"})


@dataclass
class SDRLead:
    """Prospect com score e sequência de outreach (execute mode)."""
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
            "tier": self.score.tier.value,
            "composite": round(self.score.composite, 3),
            "has_sequence": self.sequence is not None,
            "steps_count": len(self.sequence.steps) if self.sequence else 0,
        }


@dataclass
class SDRPipelineResult:
    """Resultado unificado do SDRPipelineWorkflow."""

    run_id: str
    success: bool
    mode: str  # "execute" | "plan"
    prospects_count: int = 0
    # execute fields
    leads: list[SDRLead] = field(default_factory=list)
    # plan fields
    plan: SDRPlan | None = None
    akasha_event_id: str = ""
    dry_run: bool = True
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None

    # ── execute properties ──────────────────────────────────────────────

    @property
    def actionable_count(self) -> int:
        return sum(1 for l in self.leads if l.is_actionable)

    @property
    def sequences_generated(self) -> int:
        return sum(1 for l in self.leads if l.sequence is not None)

    @property
    def hot_count(self) -> int:
        return sum(1 for l in self.leads if l.score.tier == ScoreTier.HOT)

    @property
    def warm_count(self) -> int:
        return sum(1 for l in self.leads if l.score.tier == ScoreTier.WARM)

    @property
    def cold_count(self) -> int:
        return sum(1 for l in self.leads if l.score.tier == ScoreTier.COLD)

    # ── plan properties ─────────────────────────────────────────────────

    @property
    def plan_id(self) -> str:
        return self.plan.plan_id if self.plan else ""

    @property
    def plan_sequences_count(self) -> int:
        return len(self.plan.sequences) if self.plan else 0

    @property
    def risk_flags(self) -> list[str]:
        return list(self.plan.risk_flags) if self.plan else []

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "run_id": self.run_id,
            "success": self.success,
            "mode": self.mode,
            "prospects_count": self.prospects_count,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
        }
        if self.mode == "execute":
            d.update({
                "actionable_count": self.actionable_count,
                "sequences_generated": self.sequences_generated,
                "hot_count": self.hot_count,
                "warm_count": self.warm_count,
                "cold_count": self.cold_count,
            })
        else:
            d.update({
                "plan_id": self.plan_id,
                "plan_sequences_count": self.plan_sequences_count,
                "risk_flags": self.risk_flags,
            })
        return d


class SDRPipelineWorkflow:
    """SDR unificado: score+outreach (execute) ou plano formalizado (plan)."""

    def __init__(
        self,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/sdr_pipeline/",
        budget_usd: float = 0.0,
    ) -> None:
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)
        self._budget_usd = budget_usd

    def run(
        self,
        prospects: list[ProspectProfile],
        mode: str = "execute",
        title: str = "",
        description: str = "",
        dry_run: bool = True,
        sequence_tiers: frozenset[ScoreTier] = _ACTIONABLE_TIERS,
    ) -> SDRPipelineResult:
        """Executa pipeline SDR no modo especificado.

        Args:
            prospects:      Lista de ProspectProfile.
            mode:           "execute" (score+outreach) ou "plan" (documento SDRPlan).
            title:          Título do plano (obrigatório para mode="plan").
            description:    Descrição do escopo (mode="plan").
            dry_run:        True → sem persistência de arquivos.
            sequence_tiers: Tiers que recebem outreach (execute mode).
        """
        ctx = RunContext.new(budget_usd=self._budget_usd)

        if mode not in _VALID_MODES:
            return SDRPipelineResult(
                run_id=ctx.run_id, success=False, mode=mode, dry_run=dry_run,
                error=f"invalid_mode:{mode}",
            )

        if not prospects:
            return SDRPipelineResult(
                run_id=ctx.run_id, success=False, mode=mode, dry_run=dry_run,
                error="empty_prospect_list",
            )

        if mode == "execute":
            return self._run_execute(ctx, prospects, dry_run, sequence_tiers)
        return self._run_plan(ctx, prospects, title, description, dry_run)

    # ── execute mode ────────────────────────────────────────────────────

    def _run_execute(
        self,
        ctx: RunContext,
        prospects: list[ProspectProfile],
        dry_run: bool,
        sequence_tiers: frozenset[ScoreTier],
    ) -> SDRPipelineResult:
        leads: list[SDRLead] = []

        for p in prospects:
            try:
                score = score_prospect(p)
                lead = SDRLead(profile=p, score=score)
                if score.tier in sequence_tiers:
                    try:
                        lead.sequence = build_outreach_sequence(p)
                    except Exception as exc:
                        _logger.warning("[sdr_pipeline] sequence failed %s: %s", p.profile_id, exc)
                leads.append(lead)
            except Exception as exc:
                _logger.warning("[sdr_pipeline] scoring failed %s: %s", p.profile_id, exc)

        if not leads:
            return SDRPipelineResult(
                run_id=ctx.run_id, success=False, mode="execute", dry_run=dry_run,
                error="all_scoring_failed",
            )

        leads.sort(key=lambda l: l.score.composite, reverse=True)

        event = SinkEvent(
            event_type="sdr_pipeline_execute_completed",
            source=ctx.run_id,
            payload={
                "prospects_count": len(prospects),
                "scored_count": len(leads),
                "actionable_count": sum(1 for l in leads if l.is_actionable),
                "sequences_generated": sum(1 for l in leads if l.sequence is not None),
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return SDRPipelineResult(
            run_id=ctx.run_id,
            success=True,
            mode="execute",
            prospects_count=len(prospects),
            leads=leads,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
        )

    # ── plan mode ───────────────────────────────────────────────────────

    def _run_plan(
        self,
        ctx: RunContext,
        prospects: list[ProspectProfile],
        title: str,
        description: str,
        dry_run: bool,
    ) -> SDRPipelineResult:
        if not title:
            return SDRPipelineResult(
                run_id=ctx.run_id, success=False, mode="plan", dry_run=dry_run,
                error="empty_title",
            )

        try:
            plan = build_batch_plan(title, description, prospects)
        except EmptyProspectListError as exc:
            return SDRPipelineResult(
                run_id=ctx.run_id, success=False, mode="plan", dry_run=dry_run,
                error="empty_prospect_list",
            )

        event = SinkEvent(
            event_type="sdr_pipeline_plan_generated",
            source=ctx.run_id,
            payload={
                "plan_id": plan.plan_id,
                "prospects_count": len(prospects),
                "sequences_count": len(plan.sequences),
                "risk_flags": list(plan.risk_flags),
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return SDRPipelineResult(
            run_id=ctx.run_id,
            success=True,
            mode="plan",
            prospects_count=len(prospects),
            plan=plan,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
        )
