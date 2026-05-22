"""Telemetry module — provider observability.

Tracks every call to external providers (Anthropic, OpenAI, Gemini, etc.).
Records token usage, latency, cost, and hallucination signals.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from ..events.event_bus import EventBus, get_event_bus
from ..schemas.event_schema import EventEnvelope, EventType
from ..schemas.telemetry_schema import (
    LatencyRecord,
    ProviderMetric,
    TelemetryPayload,
    TokenUsage,
)

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """Collects and aggregates provider telemetry.

    Usage:
        collector = TelemetryCollector(event_bus)

        # Record a call
        collector.record_call(
            provider="anthropic",
            model="claude-opus-4-7",
            success=True,
            input_tokens=1500,
            output_tokens=800,
            duration_ms=3200,
            cost_usd=0.023,
        )
    """

    def __init__(self, bus: EventBus | None = None):
        self.bus = bus or get_event_bus()
        self._calls: list[ProviderMetric] = []
        self._lock = asyncio.Lock()

    async def record_call(
        self,
        provider: str,
        model: str,
        success: bool,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        duration_ms: float = 0,
        ttfb_ms: float | None = None,
        cost_usd: float = 0.0,
        error_type: str | None = None,
        error_message: str | None = None,
        hallucination_score: float | None = None,
        mission_id: str | None = None,
        trace_id: str | None = None,
    ) -> ProviderMetric:
        total = input_tokens + output_tokens + cache_read_tokens
        metric = ProviderMetric(
            provider=provider,
            model=model,
            success=success,
            status_code=200 if success else None,
            error_type=error_type,
            error_message=error_message,
            retry_count=0,
            tokens=TokenUsage(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read_tokens,
                cache_write_tokens=cache_write_tokens,
                total_tokens=total,
                cost_usd=cost_usd,
            ),
            latency=LatencyRecord(
                operation=f"{provider}/{model}",
                duration_ms=duration_ms,
                ttfb_ms=ttfb_ms,
                phase="total",
            ),
            hallucination_score=hallucination_score,
            mission_id=mission_id,
            trace_id=trace_id,
        )

        async with self._lock:
            self._calls.append(metric)

        event_type = EventType.PROVIDER_CALLED if success else EventType.PROVIDER_FAILED
        await self.bus.publish(
            EventBus.STREAMS["providers"],
            EventEnvelope(
                event_type=event_type,
                source="telemetry_collector",
                sequence=len(self._calls),
                mission_id=mission_id,
                trace_id=trace_id,
                payload=metric.model_dump(),
                delta_tokens=total,
                delta_cost_usd=cost_usd,
                latency_ms=duration_ms,
                severity="error" if not success else "info",
                tags={"provider": provider, "model": model},
            ),
        )

        if hallucination_score is not None and hallucination_score > 0.5:
            await self.bus.publish(
                EventBus.STREAMS["anomalies"],
                EventEnvelope(
                    event_type=EventType.HALLUCINATION_DETECTED,
                    source="telemetry_collector",
                    sequence=len(self._calls),
                    mission_id=mission_id,
                    trace_id=trace_id,
                    payload={
                        "provider": provider,
                        "model": model,
                        "hallucination_score": hallucination_score,
                    },
                    severity="warning",
                ),
            )

        return metric

    async def get_snapshot(self) -> TelemetryPayload:
        """Get aggregated telemetry for all calls since last snapshot."""
        async with self._lock:
            if not self._calls:
                return TelemetryPayload(
                    window_start=datetime.now(timezone.utc),
                    window_end=datetime.now(timezone.utc),
                )

            calls = list(self._calls)
            self._calls.clear()

        success = [c for c in calls if c.success]
        failures = [c for c in calls if not c.success]
        latencies = sorted(
            [c.latency.duration_ms for c in calls if c.latency], reverse=True
        )
        hallucinations = [
            c for c in calls if c.hallucination_score and c.hallucination_score > 0.5
        ]

        total_input = sum(c.tokens.input_tokens for c in calls if c.tokens)
        total_output = sum(c.tokens.output_tokens for c in calls if c.tokens)
        total_cost = sum(c.tokens.cost_usd for c in calls if c.tokens)

        return TelemetryPayload(
            window_start=min(c.timestamp for c in calls),
            window_end=max(c.timestamp for c in calls),
            total_calls=len(calls),
            success_count=len(success),
            failure_count=len(failures),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_cost_usd=round(total_cost, 6),
            avg_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else 0,
            p95_latency_ms=self._percentile(latencies, 95) if latencies else 0,
            p99_latency_ms=self._percentile(latencies, 99) if latencies else 0,
            hallucination_rate=len(hallucinations) / len(calls) if calls else 0,
            retry_rate=sum(1 for c in calls if c.retry_count > 0) / len(calls) if calls else 0,
        )

    @staticmethod
    def _percentile(sorted_values: list[float], p: float) -> float:
        if not sorted_values:
            return 0.0
        idx = int(len(sorted_values) * p / 100)
        return sorted_values[min(idx, len(sorted_values) - 1)]


_collector: TelemetryCollector | None = None


def get_telemetry_collector(bus: EventBus | None = None) -> TelemetryCollector:
    global _collector
    if _collector is None:
        _collector = TelemetryCollector(bus)
    return _collector
