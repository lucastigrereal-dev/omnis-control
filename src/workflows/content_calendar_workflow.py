"""ContentCalendarWorkflow — molde: brief → calendário editorial → queue items → akasha.

Onda 17 — wires existing pieces without adding new algorithms:
  - RunContext        → run_id único
  - QueueItem        → modelo de item editorial (content_queue)
  - QueueStatus      → status inicial = PLANNED
  - AkashaSinkAdapter → persiste resultado com run_id

Pipeline:
  1. distribute → distribui tópicos nos dias do calendário (round-robin)
  2. format     → alterna formatos (FEED, REELS, CAROUSEL) por padrão
  3. objective  → distribui objetivos (autoridade, alcance, conversão)
  4. build      → cria QueueItem para cada slot
  5. akasha     → evento com run_id, account, num_days, item_count
  6. retorna    → ContentCalendarResult com calendar completo

Uso (zero LLM — geração determinística):
  wf = ContentCalendarWorkflow()
  result = wf.run(
      account_handle="@oinatalrn",
      topics=["praias", "gastronomia", "hotéis"],
      num_days=7,
      dry_run=True,
  )
  print(result.items_count)   # 7 QueueItems planejados
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from src.content_queue.models import (
    QueueFormat,
    QueueItem,
    QueueObjective,
    QueueStatus,
    Priority,
)
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.content_calendar")

# Geração determinística — zero LLM, zero cloud
_COST_LOCAL_PCT = 100

# Rotação de formatos e objetivos por dia (day index % len)
_FORMAT_ROTATION = [
    QueueFormat.FEED,
    QueueFormat.REELS,
    QueueFormat.CAROUSEL,
    QueueFormat.STORIES,
    QueueFormat.FEED,
    QueueFormat.REELS,
    QueueFormat.FEED,
]

_OBJECTIVE_ROTATION = [
    QueueObjective.AUTHORITY,
    QueueObjective.REACH,
    QueueObjective.RELATIONSHIP,
    QueueObjective.CONVERSION,
    QueueObjective.AUTHORITY,
    QueueObjective.REACH,
    QueueObjective.RELATIONSHIP,
]

_DEFAULT_TIME = "09:00"


@dataclass
class ContentCalendarResult:
    """Resultado consolidado do workflow de calendário editorial."""

    run_id: str
    success: bool
    account_handle: str = ""
    num_days: int = 0
    items: list[QueueItem] = field(default_factory=list)
    akasha_event_id: str = ""
    dry_run: bool = True
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def items_count(self) -> int:
        return len(self.items)

    @property
    def format_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {}
        for item in self.items:
            dist[item.format] = dist.get(item.format, 0) + 1
        return dist

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "account_handle": self.account_handle,
            "num_days": self.num_days,
            "items_count": self.items_count,
            "format_distribution": self.format_distribution,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
            "items": [i.to_dict() for i in self.items],
        }


class ContentCalendarWorkflow:
    """Workflow de calendário editorial: brief → QueueItems → akasha."""

    def __init__(
        self,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/calendar/",
        budget_usd: float = 0.0,
    ) -> None:
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)
        self._budget_usd = budget_usd

    def run(
        self,
        account_handle: str,
        topics: list[str],
        num_days: int = 7,
        start_date: date | None = None,
        post_time: str = _DEFAULT_TIME,
        dry_run: bool = True,
    ) -> ContentCalendarResult:
        """Gera calendário editorial para um perfil.

        Args:
            account_handle: Handle do perfil Instagram (ex: "@oinatalrn").
            topics:         Lista de tópicos para distribuir nos dias.
            num_days:       Número de dias do calendário (default: 7).
            start_date:     Data de início (default: hoje).
            post_time:      Horário padrão dos posts (HH:MM).
            dry_run:        True → gera plano sem persistir arquivos.
        """
        ctx = RunContext.new(budget_usd=self._budget_usd)
        _logger.info(
            "%s ContentCalendarWorkflow.run: account=%s, %d tópicos, %d dias",
            ctx.log_prefix(), account_handle, len(topics), num_days,
        )

        if not account_handle:
            return ContentCalendarResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="empty_account_handle",
            )
        if not topics:
            return ContentCalendarResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="empty_topics",
            )
        if num_days < 1 or num_days > 365:
            return ContentCalendarResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="invalid_num_days",
            )

        base_date = start_date or date.today()
        items: list[QueueItem] = []

        for day_idx in range(num_days):
            slot_date = base_date + timedelta(days=day_idx)
            topic = topics[day_idx % len(topics)]
            fmt = _FORMAT_ROTATION[day_idx % len(_FORMAT_ROTATION)]
            obj = _OBJECTIVE_ROTATION[day_idx % len(_OBJECTIVE_ROTATION)]

            item = QueueItem(
                queue_id=f"{ctx.run_id[:8]}-d{day_idx:03d}",
                account_handle=account_handle,
                date=slot_date.isoformat(),
                time=post_time,
                format=fmt,
                objective=obj,
                status=QueueStatus.PLANNED,
                priority=Priority.MEDIUM,
                notes=f"Tópico: {topic}",
            )
            items.append(item)

        _logger.info("%s calendar: %d items gerados para %s", ctx.log_prefix(), len(items), account_handle)

        # Gravar no akasha
        fmt_dist = {}
        for item in items:
            fmt_dist[item.format] = fmt_dist.get(item.format, 0) + 1

        event = SinkEvent(
            event_type="content_calendar_generated",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "account_handle": account_handle,
                "num_days": num_days,
                "items_count": len(items),
                "topics": topics[:10],
                "format_distribution": fmt_dist,
                "start_date": base_date.isoformat(),
                "cost_local_pct": _COST_LOCAL_PCT,
                "dry_run": dry_run,
            },
        )
        written = self._sink.write_event(event)
        _logger.info("%s akasha write: event_id=%s, ok=%s", ctx.log_prefix(), event.event_id, written)

        return ContentCalendarResult(
            run_id=ctx.run_id,
            success=True,
            account_handle=account_handle,
            num_days=num_days,
            items=items,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
            cost_local_pct=_COST_LOCAL_PCT,
            artifacts={
                "run_id": ctx.run_id,
                "akasha_event_id": event.event_id,
                "format_distribution": fmt_dist,
            },
        )
