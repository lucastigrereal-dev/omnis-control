"""DailyBriefingWorkflow — briefing matinal: saúde + leads + calendário → akasha.

Onda 20 — compõe SystemHealthWorkflow + LeadScoringWorkflow + ContentCalendarWorkflow
sem adicionar novos algoritmos:
  - RunContext            → run_id único do briefing diário
  - SystemHealthWorkflow  → snapshot de saúde dos sistemas
  - LeadScoringWorkflow   → score dos prospects fornecidos
  - ContentCalendarWorkflow → calendário editorial da semana
  - AkashaSinkAdapter     → persiste briefing consolidado

Pipeline:
  1. health  → SystemHealthWorkflow.run() em seco
  2. leads   → LeadScoringWorkflow.run() se prospects fornecidos
  3. calendar → ContentCalendarWorkflow.run() se configurado
  4. compile → compila seções em texto markdown
  5. akasha  → evento "daily_briefing_generated" com run_id
  6. retorna → DailyBriefingResult com briefing completo

Uso (briefing matinal — zero LLM):
  wf = DailyBriefingWorkflow.default()
  result = wf.run(
      prospects=[...],
      account_handle="@oinatalrn",
      topics=["praias", "gastronomia"],
      dry_run=True,
  )
  print(result.briefing_text)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from src.workflows.system_health_workflow import SystemHealthWorkflow, SystemHealthResult
from src.workflows.lead_scoring_workflow import LeadScoringWorkflow, LeadScoringResult
from src.workflows.content_calendar_workflow import ContentCalendarWorkflow, ContentCalendarResult
from src.commercial_sdr.models import ProspectProfile
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.daily_briefing")

_COST_LOCAL_PCT = 100


@dataclass
class DailyBriefingResult:
    """Briefing matinal consolidado do sistema OMNIS."""

    run_id: str
    success: bool
    briefing_date: str = ""
    health: SystemHealthResult | None = None
    leads: LeadScoringResult | None = None
    calendar: ContentCalendarResult | None = None
    akasha_event_id: str = ""
    dry_run: bool = True
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def health_ok(self) -> bool:
        return self.health is not None and self.health.overall_ok

    @property
    def hot_leads_count(self) -> int:
        if self.leads is None:
            return 0
        return self.leads.hot_count

    @property
    def calendar_items(self) -> int:
        if self.calendar is None:
            return 0
        return self.calendar.items_count

    @property
    def briefing_text(self) -> str:
        lines: list[str] = [
            f"# Briefing Matinal OMNIS — {self.briefing_date}",
            f"run_id: {self.run_id}",
            "",
        ]

        if self.health:
            status = "OK" if self.health.overall_ok else "DEGRADED"
            lines += [
                "## Sistema",
                f"- Status: {status}",
                f"- Workflows: {self.health.workflows_importable}/{self.health.workflows_total}",
                f"- Agencias: {self.health.agencies_total} total, {self.health.agencies_active} ativas",
                "",
            ]

        if self.leads:
            lines += [
                "## Leads SDR",
                f"- Total qualificados: {self.leads.total_scored}",
                f"- HOT: {self.leads.hot_count}  WARM: {self.leads.warm_count}  COLD: {self.leads.cold_count}",
                "",
            ]

        if self.calendar:
            lines += [
                "## Calendario Editorial",
                f"- Conta: {self.calendar.account_handle}",
                f"- Itens: {self.calendar.items_count} posts planejados",
                "",
            ]

        lines.append(f"cost_local_pct: {self.cost_local_pct}%")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "briefing_date": self.briefing_date,
            "health_ok": self.health_ok,
            "hot_leads_count": self.hot_leads_count,
            "calendar_items": self.calendar_items,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
        }


class DailyBriefingWorkflow:
    """Briefing matinal: compõe SystemHealth + LeadScoring + ContentCalendar → akasha."""

    def __init__(
        self,
        health_workflow: SystemHealthWorkflow | None = None,
        lead_workflow: LeadScoringWorkflow | None = None,
        calendar_workflow: ContentCalendarWorkflow | None = None,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/briefing/",
        budget_usd: float = 0.0,
    ) -> None:
        self._health = health_workflow or SystemHealthWorkflow()
        self._leads = lead_workflow or LeadScoringWorkflow()
        self._calendar = calendar_workflow or ContentCalendarWorkflow()
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)
        self._budget_usd = budget_usd

    def run(
        self,
        prospects: list[ProspectProfile] | None = None,
        account_handle: str = "",
        topics: list[str] | None = None,
        num_days: int = 7,
        start_date: date | None = None,
        dry_run: bool = True,
    ) -> DailyBriefingResult:
        """Gera briefing matinal consolidado.

        Args:
            prospects:      Prospects para scoring SDR (opcional).
            account_handle: Handle Instagram para calendário editorial (opcional).
            topics:         Tópicos para o calendário (opcional).
            num_days:       Dias do calendário (default: 7).
            start_date:     Data de início do calendário.
            dry_run:        True → processa sem persistir arquivos.
        """
        ctx = RunContext.new(budget_usd=self._budget_usd)
        briefing_date = (start_date or date.today()).isoformat()

        _logger.info(
            "%s DailyBriefingWorkflow.run: %d prospects, account=%s, dry_run=%s",
            ctx.log_prefix(), len(prospects or []), account_handle or "(none)", dry_run,
        )

        # Section 1 — System Health
        health_result = self._health.run(dry_run=dry_run)
        _logger.info(
            "%s health: overall_ok=%s, workflows=%d/%d",
            ctx.log_prefix(), health_result.overall_ok,
            health_result.workflows_importable, health_result.workflows_total,
        )

        # Section 2 — Lead Scoring (optional)
        lead_result: LeadScoringResult | None = None
        if prospects:
            lead_result = self._leads.run(prospects, dry_run=dry_run)
            _logger.info(
                "%s leads: %d scored, HOT=%d WARM=%d",
                ctx.log_prefix(), lead_result.total_scored,
                lead_result.hot_count, lead_result.warm_count,
            )

        # Section 3 — Content Calendar (optional)
        calendar_result: ContentCalendarResult | None = None
        if account_handle and topics:
            calendar_result = self._calendar.run(
                account_handle=account_handle,
                topics=topics,
                num_days=num_days,
                start_date=start_date,
                dry_run=dry_run,
            )
            _logger.info(
                "%s calendar: %d items for %s",
                ctx.log_prefix(), calendar_result.items_count, account_handle,
            )

        # Section 4 — Compile & persist
        event = SinkEvent(
            event_type="daily_briefing_generated",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "briefing_date": briefing_date,
                "health_ok": health_result.overall_ok,
                "workflows_total": health_result.workflows_total,
                "hot_leads": lead_result.hot_count if lead_result else 0,
                "warm_leads": lead_result.warm_count if lead_result else 0,
                "calendar_items": calendar_result.items_count if calendar_result else 0,
                "sections_generated": sum([
                    1,
                    1 if lead_result else 0,
                    1 if calendar_result else 0,
                ]),
                "cost_local_pct": _COST_LOCAL_PCT,
                "dry_run": dry_run,
            },
        )
        written = self._sink.write_event(event)
        _logger.info(
            "%s akasha write: event_id=%s, ok=%s", ctx.log_prefix(), event.event_id, written
        )

        return DailyBriefingResult(
            run_id=ctx.run_id,
            success=True,
            briefing_date=briefing_date,
            health=health_result,
            leads=lead_result,
            calendar=calendar_result,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
            cost_local_pct=_COST_LOCAL_PCT,
            artifacts={
                "run_id": ctx.run_id,
                "akasha_event_id": event.event_id,
                "briefing_date": briefing_date,
            },
        )

    @classmethod
    def default(cls) -> "DailyBriefingWorkflow":
        """Instância padrão com SystemHealthWorkflow.default() pré-carregado."""
        from src.workflows.workflow_registry import WorkflowRegistry
        return cls(health_workflow=SystemHealthWorkflow(
            workflow_registry=WorkflowRegistry.default(),
        ))
