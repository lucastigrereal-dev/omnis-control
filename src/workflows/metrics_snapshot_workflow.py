"""MetricsSnapshotWorkflow — agrega MetricEvents + RunSummaries → snapshot → akasha.

Onda 24: envolve as funções puras de src.metrics.aggregations para produzir
um snapshot consolidado de métricas de execução sem IO de disco.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.metrics.models import MetricEvent, RunSummary
from src.metrics.aggregations import (
    aggregate_metrics_by_event_type,
    aggregate_tool_usage,
    compute_run_stats,
    compute_mission_summary,
)
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.metrics_snapshot")

_COST_LOCAL_PCT = 100


@dataclass
class MetricsSnapshotResult:
    run_id: str
    success: bool
    metrics_count: int
    runs_count: int
    unique_tools: int
    succeeded_runs: int
    failed_runs: int
    total_tokens: int
    total_cost_usd: float
    snapshot: dict[str, Any]
    akasha_event_id: str
    dry_run: bool
    cost_local_pct: int = _COST_LOCAL_PCT

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "metrics_count": self.metrics_count,
            "runs_count": self.runs_count,
            "unique_tools": self.unique_tools,
            "succeeded_runs": self.succeeded_runs,
            "failed_runs": self.failed_runs,
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "akasha_event_id": self.akasha_event_id,
            "cost_local_pct": self.cost_local_pct,
        }


class MetricsSnapshotWorkflow:
    """Agrega listas de MetricEvent e RunSummary em snapshot consolidado."""

    def __init__(
        self,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/metrics_snapshot/",
    ) -> None:
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)

    def run(
        self,
        metrics: list[MetricEvent],
        runs: list[RunSummary],
        dry_run: bool = True,
    ) -> MetricsSnapshotResult:
        """Computa snapshot agregado e persiste evento akasha.

        Args:
            metrics: lista de MetricEvent a agregar.
            runs: lista de RunSummary a agregar.
            dry_run: se True, marca resultado como simulação.

        Returns:
            MetricsSnapshotResult com dados agregados.
        """
        ctx = RunContext.new(budget_usd=0.0)

        snapshot = compute_mission_summary(metrics, runs)
        run_stats = snapshot.get("run_stats", {})
        by_tool = snapshot.get("by_tool", {})

        unique_tools = len([k for k in by_tool if k != "__no_tool__"])
        succeeded = run_stats.get("succeeded", 0)
        failed = run_stats.get("failed", 0)
        total_tokens = run_stats.get("total_tokens", 0)
        total_cost = run_stats.get("total_cost_usd", 0.0)

        _logger.info(
            "metrics_snapshot[%s]: %d metrics, %d runs, %d tools, %d succeeded",
            ctx.run_id, len(metrics), len(runs), unique_tools, succeeded,
        )

        event = SinkEvent(
            event_type="metrics_snapshot_generated",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "metrics_count": len(metrics),
                "runs_count": len(runs),
                "unique_tools": unique_tools,
                "succeeded_runs": succeeded,
                "failed_runs": failed,
                "total_tokens": total_tokens,
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return MetricsSnapshotResult(
            run_id=ctx.run_id,
            success=True,
            metrics_count=len(metrics),
            runs_count=len(runs),
            unique_tools=unique_tools,
            succeeded_runs=succeeded,
            failed_runs=failed,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            snapshot=snapshot,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
        )
