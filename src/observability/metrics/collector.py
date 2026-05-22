"""Runtime metrics — SLO tracking, metric collection, aggregation.

Extends the existing metrics module with real-time aggregation and SLO compliance.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from ..schemas.metric_schema import (
    CANONICAL_SLOS,
    MetricType,
    RuntimeMetric,
    SLIDefinition,
    SLOStatus,
)

logger = logging.getLogger(__name__)


class RuntimeMetricsCollector:
    """Collects runtime metrics with SLO tracking.

    Usage:
        collector = RuntimeMetricsCollector()
        collector.record("mission_success_rate", 98.5, tags={"mission": "m1"})
        slo_status = collector.check_slo("mission_success_rate")
    """

    def __init__(self, slos: list[SLIDefinition] | None = None):
        self.slos: dict[str, SLIDefinition] = {s.name: s for s in (slos or CANONICAL_SLOS)}
        self._metrics: defaultdict[str, list[RuntimeMetric]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._counters: defaultdict[str, int] = defaultdict(int)

    async def record(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: dict[str, str] | None = None,
        unit: str = "",
        mission_id: str | None = None,
        trace_id: str | None = None,
    ) -> RuntimeMetric:
        metric = RuntimeMetric(
            name=name,
            type=metric_type,
            value=value,
            tags=tags or {},
            unit=unit,
            mission_id=mission_id,
            trace_id=trace_id,
        )

        async with self._lock:
            self._metrics[name].append(metric)
            if metric_type == MetricType.COUNTER:
                self._counters[name] += int(value)

            # Prune old metrics outside SLI window
            max_window = max((s.window_minutes for s in self.slos.values()), default=60)
            cutoff = datetime.now(timezone.utc).timestamp() - (max_window * 60)
            self._metrics[name] = [
                m for m in self._metrics[name] if m.timestamp.timestamp() > cutoff
            ]

        return metric

    def check_slo(self, sli_name: str) -> SLOStatus | None:
        sli = self.slos.get(sli_name)
        if not sli:
            return None

        metrics = self._metrics.get(sli_name, [])
        if not metrics:
            return SLOStatus(
                sli=sli,
                current_value=0,
                compliant=True,
                budget_remaining_pct=100.0,
            )

        if sli.metric_type == MetricType.GAUGE:
            current = sum(m.value for m in metrics) / len(metrics)
        elif sli.metric_type == MetricType.HISTOGRAM:
            sorted_vals = sorted(m.value for m in metrics)
            idx = int(len(sorted_vals) * 0.95)
            current = sorted_vals[min(idx, len(sorted_vals) - 1)]
        elif sli.metric_type == MetricType.COUNTER:
            current = float(self._counters.get(sli_name, 0))
        else:
            current = sum(m.value for m in metrics) / len(metrics) if metrics else 0

        compliant = current >= sli.target_value
        budget = max(0, min(100, (current / sli.target_value) * 100))
        return SLOStatus(
            sli=sli,
            current_value=round(current, 4),
            compliant=compliant,
            budget_remaining_pct=round(budget, 2),
        )

    async def get_all_slo_status(self) -> dict[str, SLOStatus]:
        return {
            name: self.check_slo(name) for name in self.slos if self.check_slo(name) is not None
        }

    async def get_snapshot(self) -> dict[str, Any]:
        slo_status = await self.get_all_slo_status()
        return {
            "slos": {name: status.model_dump() for name, status in slo_status.items()},
            "metric_counts": {name: len(metrics) for name, metrics in self._metrics.items()},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


_collector: RuntimeMetricsCollector | None = None


def get_runtime_metrics(slos: list[SLIDefinition] | None = None) -> RuntimeMetricsCollector:
    global _collector
    if _collector is None:
        _collector = RuntimeMetricsCollector(slos)
    return _collector
