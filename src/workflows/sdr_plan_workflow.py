"""SDRPlanWorkflow — plano SDR finalizado: prospects → SDRPlan → akasha.

Onda 22 — wires CommercialSDRPlanner sem adicionar novos algoritmos:
  - RunContext              → run_id único
  - build_batch_plan()      → SDRPlan com scores + sequences + risk_flags
  - AkashaSinkAdapter       → persiste resultado com run_id

Diferença de SDRBatchWorkflow (Onda 19):
  - Onda 19: lista de SDRLead individuais, ordenada por composite
  - Onda 22: SDRPlan finalizado como documento, com risk_flags e sequences attached

Pipeline:
  1. validate  → garante lista não-vazia
  2. plan      → build_batch_plan(title, description, prospects)
  3. akasha    → evento "sdr_plan_generated" com plan_id, counts
  4. retorna   → SDRPlanResult com plan e sumário

Uso (plano mensal SDR — zero LLM):
  wf = SDRPlanWorkflow()
  result = wf.run(
      title="Prospecção Hotéis Natal — Junho/2026",
      description="Hotéis e pousadas do RN",
      prospects=[p1, p2, ...],
      dry_run=True,
  )
  print(result.plan.plan_id)
  print(result.sequences_count)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.commercial_sdr.models import ProspectProfile, SDRPlan
from src.commercial_sdr.service import build_batch_plan
from src.commercial_sdr.errors import EmptyProspectListError
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.sdr_plan")

_COST_LOCAL_PCT = 100


@dataclass
class SDRPlanResult:
    """Resultado do workflow de geração de plano SDR."""

    run_id: str
    success: bool
    plan: SDRPlan | None = None
    akasha_event_id: str = ""
    dry_run: bool = True
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def plan_id(self) -> str:
        return self.plan.plan_id if self.plan else ""

    @property
    def prospects_count(self) -> int:
        return len(self.plan.prospects) if self.plan else 0

    @property
    def sequences_count(self) -> int:
        return len(self.plan.sequences) if self.plan else 0

    @property
    def risk_flags(self) -> list[str]:
        return list(self.plan.risk_flags) if self.plan else []

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "plan_id": self.plan_id,
            "prospects_count": self.prospects_count,
            "sequences_count": self.sequences_count,
            "risk_flags": self.risk_flags,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
        }


class SDRPlanWorkflow:
    """Workflow de plano SDR: prospects → build_batch_plan → akasha."""

    def __init__(
        self,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/sdr_plan/",
        budget_usd: float = 0.0,
    ) -> None:
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)
        self._budget_usd = budget_usd

    def run(
        self,
        title: str,
        description: str,
        prospects: list[ProspectProfile],
        dry_run: bool = True,
    ) -> SDRPlanResult:
        """Gera plano SDR finalizado para uma lista de prospects.

        Args:
            title:       Título do plano (ex: "Hotéis Natal Junho/2026").
            description: Descrição do escopo.
            prospects:   Lista de ProspectProfile para incluir no plano.
            dry_run:     True → processa sem persistir arquivos.
        """
        ctx = RunContext.new(budget_usd=self._budget_usd)
        _logger.info(
            "%s SDRPlanWorkflow.run: '%s', %d prospects, dry_run=%s",
            ctx.log_prefix(), title, len(prospects), dry_run,
        )

        if not title:
            return SDRPlanResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="empty_title",
            )

        if not prospects:
            return SDRPlanResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="empty_prospect_list",
            )

        try:
            plan = build_batch_plan(title, description, prospects)
        except EmptyProspectListError as exc:
            _logger.warning("%s build_batch_plan failed: %s", ctx.log_prefix(), exc)
            return SDRPlanResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="empty_prospect_list",
            )

        sequences_count = len(plan.sequences)
        risk_flags = list(plan.risk_flags)

        _logger.info(
            "%s plan %s: %d prospects, %d sequences, %d risk_flags",
            ctx.log_prefix(), plan.plan_id,
            len(plan.prospects), sequences_count, len(risk_flags),
        )

        event = SinkEvent(
            event_type="sdr_plan_generated",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "plan_id": plan.plan_id,
                "title": title,
                "prospects_count": len(plan.prospects),
                "sequences_count": sequences_count,
                "risk_flags": risk_flags,
                "cost_local_pct": _COST_LOCAL_PCT,
                "dry_run": dry_run,
            },
        )
        written = self._sink.write_event(event)
        _logger.info(
            "%s akasha write: event_id=%s, ok=%s", ctx.log_prefix(), event.event_id, written
        )

        return SDRPlanResult(
            run_id=ctx.run_id,
            success=True,
            plan=plan,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
            cost_local_pct=_COST_LOCAL_PCT,
            artifacts={
                "run_id": ctx.run_id,
                "plan_id": plan.plan_id,
                "akasha_event_id": event.event_id,
                "sequences_count": sequences_count,
            },
        )
