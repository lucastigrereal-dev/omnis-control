"""Metrics Recorder — camada de gravacao de metricas. P0.9."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.metrics.models import MetricEvent, RunSummary
from src.metrics.store import MetricsStore
from src.metrics.aggregations import (
    compute_daily_summary,
    compute_mission_summary,
    aggregate_tool_usage,
)


class MetricsRecorder:
    """Grava e consulta metricas de execucao do OMNIS."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        self.store = MetricsStore(base_dir)

    # ── Recording ─────────────────────────────────────────────────────

    def record_metric(
        self,
        name: str,
        value: float = 1.0,
        *,
        mission_id: str = "",
        run_id: str = "",
        tool_id: str = "",
        event_type: str = "",
        unit: str = "",
        status: str = "",
        duration_ms: float = 0.0,
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost_usd: float = 0.0,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MetricEvent:
        """Grava um MetricEvent generico."""
        event = MetricEvent(
            name=name,
            value=value,
            mission_id=mission_id,
            run_id=run_id,
            tool_id=tool_id,
            event_type=event_type,
            unit=unit,
            status=status,
            duration_ms=duration_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            tags=tags or {},
            metadata=metadata or {},
        )
        return self.store.write_metric(event)

    def start_run(self, mission_id: str = "", run_id: Optional[str] = None) -> RunSummary:
        """Inicia um RunSummary (status=running). Tambem emite metrica de inicio."""
        if run_id is None:
            run_id = uuid.uuid4().hex[:12]

        summary = RunSummary(run_id=run_id, mission_id=mission_id)
        written = self.store.write_run(summary)

        self.record_metric(
            name="run_started",
            value=1.0,
            mission_id=mission_id,
            run_id=run_id,
            event_type="run_started",
            unit="count",
        )
        return written

    def finish_run(
        self,
        run_id: str,
        status: str,
        *,
        duration_ms: float = 0.0,
        warnings_count: int = 0,
        retries_count: int = 0,
        checkpoints_count: int = 0,
        tools_used: Optional[List[str]] = None,
        artifacts_count: int = 0,
        events_count: int = 0,
        total_tokens: int = 0,
        total_cost_usd: float = 0.0,
    ) -> Optional[RunSummary]:
        """Finaliza um RunSummary. Atualiza status + metricas agregadas."""
        existing = self.store.get_run(run_id)
        if existing is None:
            return None

        finished_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Compute duration from started_at
        if duration_ms == 0.0 and existing.started_at:
            try:
                start = datetime.fromisoformat(existing.started_at.replace("Z", "+00:00"))
                end = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
                duration_ms = (end - start).total_seconds() * 1000
            except (ValueError, Exception):
                duration_ms = 0.0

        updated = self.store.update_run(
            run_id,
            status=status,
            finished_at=finished_at,
            duration_ms=duration_ms,
            warnings_count=warnings_count,
            retries_count=retries_count,
            checkpoints_count=checkpoints_count,
            tools_used=tools_used or existing.tools_used,
            artifacts_count=artifacts_count,
            events_count=events_count,
            total_tokens=total_tokens,
            total_cost_usd=total_cost_usd,
        )

        self.record_metric(
            name="run_completed",
            value=1.0,
            mission_id=existing.mission_id,
            run_id=run_id,
            event_type="run_completed",
            unit="count",
            status=status,
            duration_ms=duration_ms,
        )
        return updated

    def record_tool_use(
        self,
        tool_id: str,
        mission_id: str = "",
        run_id: str = "",
        status: str = "",
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MetricEvent:
        """Registra uso de ferramenta como MetricEvent."""
        return self.record_metric(
            name="tool_use",
            value=1.0,
            tool_id=tool_id,
            mission_id=mission_id,
            run_id=run_id,
            event_type="tool_use",
            unit="count",
            status=status,
            duration_ms=duration_ms,
            metadata=metadata,
        )

    def record_mission_event(
        self,
        mission_id: str,
        event_type: str,
        status: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MetricEvent:
        """Registra evento de missao (checkpoint/pause/resume/retry)."""
        return self.record_metric(
            name=event_type,
            value=1.0,
            mission_id=mission_id,
            event_type=event_type,
            unit="count",
            status=status,
            metadata=metadata,
        )

    # ── Querying ──────────────────────────────────────────────────────

    def get_metrics(self, **filters) -> List[MetricEvent]:
        """Consulta MetricEvents com filtros."""
        return self.store.get_metrics(**filters)

    def summarize_mission(self, mission_id: str) -> Dict[str, Any]:
        """Resumo completo de uma missao."""
        metrics = self.store.get_metrics(mission_id=mission_id, limit=0)
        runs = self.store.get_runs(mission_id=mission_id, limit=0)
        return compute_mission_summary(metrics, runs)

    def summarize_tools(self, days: int = 30) -> Dict[str, Any]:
        """Resumo de uso de ferramentas (todos os dados disponiveis)."""
        metrics = self.store.get_metrics(limit=0)
        by_tool = aggregate_tool_usage(metrics)
        return {
            "total_metrics_with_tool": sum(1 for m in metrics if m.tool_id),
            "unique_tools": len([k for k in by_tool if k != "__no_tool__"]),
            "by_tool": by_tool,
        }

    def summarize_today(self) -> Dict[str, Any]:
        """Resumo das runs de hoje."""
        runs = self.store.get_runs(limit=0)
        return compute_daily_summary(runs)
