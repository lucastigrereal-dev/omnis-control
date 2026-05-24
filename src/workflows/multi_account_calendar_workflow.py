"""MultiAccountCalendarWorkflow — calendário para múltiplas contas → akasha.

Onda 21 — opera ContentCalendarWorkflow para N contas em sequência:
  - RunContext              → run_id único do batch
  - ContentCalendarWorkflow → calendário por conta
  - AkashaSinkAdapter       → persiste resultado consolidado

Pipeline:
  1. validate  → garante lista não-vazia de contas
  2. batch     → ContentCalendarWorkflow.run() para cada conta
  3. akasha    → evento "multi_account_calendar_generated" com totais
  4. retorna   → MultiAccountCalendarResult com todos os calendários

Config padrão OMNIS (6 contas Lucas Tigre):
  MultiAccountCalendarWorkflow.default_accounts() retorna as 6 contas padrão

Uso (batch de 6 contas — zero LLM):
  wf = MultiAccountCalendarWorkflow()
  result = wf.run(
      accounts=MultiAccountCalendarWorkflow.default_accounts(),
      num_days=7,
      dry_run=True,
  )
  print(result.total_items)   # 42 QueueItems (6 contas × 7 dias)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from src.workflows.content_calendar_workflow import (
    ContentCalendarWorkflow,
    ContentCalendarResult,
)
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink, MockAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.multi_account_calendar")

_COST_LOCAL_PCT = 100

# Contas padrão OMNIS (Lucas Tigre)
_DEFAULT_ACCOUNTS = [
    {"handle": "@lucastigrereal",      "topics": ["lifestyle", "viagem", "bastidores"]},
    {"handle": "@oinatalrn",           "topics": ["praias", "hoteis", "gastronomia", "turismo"]},
    {"handle": "@agenteviajabrasil",   "topics": ["destinos", "dicas", "roteiros", "hospedagem"]},
    {"handle": "@afamiliatigrereal",   "topics": ["familia", "viagem", "experiencias"]},
    {"handle": "@oquecomernatalrn",    "topics": ["restaurantes", "gastronomia", "drinks"]},
    {"handle": "@natalaivoueu",        "topics": ["praias", "guia", "turismo local"]},
]


@dataclass
class AccountCalendar:
    """Calendário de uma conta com resultado do workflow."""
    account_handle: str
    topics: list[str]
    result: ContentCalendarResult

    @property
    def items_count(self) -> int:
        return self.result.items_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_handle": self.account_handle,
            "topics": self.topics,
            "items_count": self.items_count,
            "success": self.result.success,
            "format_distribution": self.result.format_distribution,
            "akasha_event_id": self.result.akasha_event_id,
        }


@dataclass
class MultiAccountCalendarResult:
    """Resultado consolidado do batch de calendários."""

    run_id: str
    success: bool
    accounts_total: int = 0
    accounts_ok: int = 0
    calendars: list[AccountCalendar] = field(default_factory=list)
    akasha_event_id: str = ""
    dry_run: bool = True
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def total_items(self) -> int:
        return sum(c.items_count for c in self.calendars)

    @property
    def accounts_failed(self) -> int:
        return self.accounts_total - self.accounts_ok

    @property
    def format_distribution_all(self) -> dict[str, int]:
        dist: dict[str, int] = {}
        for cal in self.calendars:
            for fmt, count in cal.result.format_distribution.items():
                dist[fmt] = dist.get(fmt, 0) + count
        return dist

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "accounts_total": self.accounts_total,
            "accounts_ok": self.accounts_ok,
            "accounts_failed": self.accounts_failed,
            "total_items": self.total_items,
            "format_distribution_all": self.format_distribution_all,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
            "calendars": [c.to_dict() for c in self.calendars],
        }


class MultiAccountCalendarWorkflow:
    """Batch de calendários: lista de contas → ContentCalendar por conta → akasha."""

    def __init__(
        self,
        calendar_workflow: ContentCalendarWorkflow | None = None,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/multi_calendar/",
        budget_usd: float = 0.0,
    ) -> None:
        self._calendar = calendar_workflow or ContentCalendarWorkflow()
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)
        self._budget_usd = budget_usd

    def run(
        self,
        accounts: list[dict[str, Any]],
        num_days: int = 7,
        start_date: date | None = None,
        post_time: str = "09:00",
        dry_run: bool = True,
    ) -> MultiAccountCalendarResult:
        """Gera calendários para múltiplas contas.

        Args:
            accounts:   Lista de {handle: str, topics: list[str]}.
            num_days:   Número de dias do calendário (default: 7).
            start_date: Data de início (default: hoje).
            post_time:  Horário padrão dos posts (HH:MM).
            dry_run:    True → processa sem persistir arquivos.
        """
        ctx = RunContext.new(budget_usd=self._budget_usd)
        _logger.info(
            "%s MultiAccountCalendarWorkflow.run: %d accounts, %d days, dry_run=%s",
            ctx.log_prefix(), len(accounts), num_days, dry_run,
        )

        if not accounts:
            return MultiAccountCalendarResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="empty_accounts_list",
            )

        calendars: list[AccountCalendar] = []
        accounts_ok = 0

        for acc in accounts:
            handle = acc.get("handle", "")
            topics = acc.get("topics", [])

            try:
                result = self._calendar.run(
                    account_handle=handle,
                    topics=topics,
                    num_days=num_days,
                    start_date=start_date,
                    post_time=post_time,
                    dry_run=dry_run,
                )
                if result.success:
                    accounts_ok += 1
                calendars.append(AccountCalendar(
                    account_handle=handle,
                    topics=topics,
                    result=result,
                ))
            except Exception as exc:
                _logger.warning(
                    "%s calendar failed for %s: %s", ctx.log_prefix(), handle, exc
                )

        total_items = sum(c.items_count for c in calendars)
        fmt_dist: dict[str, int] = {}
        for cal in calendars:
            for fmt, count in cal.result.format_distribution.items():
                fmt_dist[fmt] = fmt_dist.get(fmt, 0) + count

        _logger.info(
            "%s batch done: %d/%d accounts ok, %d total items",
            ctx.log_prefix(), accounts_ok, len(accounts), total_items,
        )

        event = SinkEvent(
            event_type="multi_account_calendar_generated",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "accounts_total": len(accounts),
                "accounts_ok": accounts_ok,
                "total_items": total_items,
                "num_days": num_days,
                "format_distribution_all": fmt_dist,
                "cost_local_pct": _COST_LOCAL_PCT,
                "dry_run": dry_run,
            },
        )
        written = self._sink.write_event(event)
        _logger.info(
            "%s akasha write: event_id=%s, ok=%s", ctx.log_prefix(), event.event_id, written
        )

        return MultiAccountCalendarResult(
            run_id=ctx.run_id,
            success=True,
            accounts_total=len(accounts),
            accounts_ok=accounts_ok,
            calendars=calendars,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
            cost_local_pct=_COST_LOCAL_PCT,
            artifacts={
                "run_id": ctx.run_id,
                "akasha_event_id": event.event_id,
                "total_items": total_items,
                "accounts_ok": accounts_ok,
            },
        )

    @staticmethod
    def default_accounts() -> list[dict[str, Any]]:
        """Retorna as 6 contas padrão OMNIS (Lucas Tigre)."""
        return list(_DEFAULT_ACCOUNTS)
