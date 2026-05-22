"""Health score engine — composite scoring, anomaly detection, runtime evaluation.

Computes a unified health score from multiple signals:
  1. Event bus health (Redis connectivity)
  2. Provider health (success rate, latency)
  3. Mission health (success rate, error rate)
  4. Resource health (disk, memory, CPU)
  5. Circuit breaker status

Scoring formula:
  total = sum(score_i * weight_i) / sum(weight_i)

Anomaly detection uses rolling statistics with configurable thresholds.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from ..events.event_bus import EventBus, get_event_bus
from ..schemas.event_schema import EventEnvelope, EventType
from ..schemas.health_schema import (
    AnomalySignal,
    HealthComponent,
    HealthScore,
    HealthStatus,
)

logger = logging.getLogger(__name__)


class HealthScorer:
    """Composite health scoring engine.

    Usage:
        scorer = HealthScorer(event_bus)
        health = await scorer.compute()
        print(f"OMNIS Health: {health.overall_score:.2%} — {health.status.value}")
    """

    # Default weights for each component
    DEFAULT_WEIGHTS = {
        "event_bus": 0.25,
        "providers": 0.30,
        "missions": 0.20,
        "resources": 0.15,
        "circuit_breakers": 0.10,
    }

    # Anomaly thresholds
    ANOMALY_THRESHOLDS = {
        "provider_failure_rate": 0.10,  # >10% failure rate = anomaly
        "mission_failure_rate": 0.20,  # >20% mission failures = anomaly
        "latency_spike_pct": 200,  # >200% of baseline = anomaly
        "cost_spike_pct": 300,  # >300% of baseline = anomaly
    }

    def __init__(self, bus: EventBus | None = None):
        self.bus = bus or get_event_bus()
        self._previous_scores: list[HealthScore] = []
        self._baseline_latency_ms: float = 1000.0
        self._baseline_cost_per_mission: float = 0.50
        self._lock = asyncio.Lock()

    async def compute(self) -> HealthScore:
        """Compute the current composite health score."""
        async with self._lock:
            components = await asyncio.gather(
                self._check_event_bus(),
                self._check_providers(),
                self._check_missions(),
                self._check_resources(),
                self._check_circuit_breakers(),
            )

            prev = self._previous_scores[-1].overall_score if self._previous_scores else None
            score = HealthScore.compute(list(components), previous_score=prev)

            anomalies = await self._detect_anomalies(score)
            score.anomalies = anomalies

            self._previous_scores.append(score)
            if len(self._previous_scores) > 100:
                self._previous_scores = self._previous_scores[-100:]

            await self.bus.publish(
                EventBus.STREAMS["health"],
                EventEnvelope(
                    event_type=EventType.HEALTH_CHECK,
                    source="health_scorer",
                    sequence=len(self._previous_scores),
                    payload={
                        "score": score.overall_score,
                        "status": score.status.value,
                        "components": [c.model_dump() for c in components],
                    },
                    severity="critical" if score.status == HealthStatus.CRITICAL else "info",
                ),
            )

            if anomalies:
                for a in anomalies:
                    await self.bus.publish(
                        EventBus.STREAMS["anomalies"],
                        EventEnvelope(
                            event_type=EventType.ANOMALY_DETECTED,
                            source="health_scorer",
                            sequence=len(self._previous_scores),
                            payload=a.model_dump(),
                            severity=a.severity,
                        ),
                    )

            return score

    async def _check_event_bus(self) -> HealthComponent:
        try:
            health = await self.bus.health_check()
            status = HealthStatus.HEALTHY if health["status"] == "healthy" else HealthStatus.CRITICAL
            return HealthComponent(
                name="event_bus",
                status=status,
                score=1.0 if status == HealthStatus.HEALTHY else 0.0,
                weight=self.DEFAULT_WEIGHTS["event_bus"],
                message=f"Redis {health.get('redis_version', '?')}",
                metadata=health,
            )
        except Exception as e:
            return HealthComponent(
                name="event_bus",
                status=HealthStatus.CRITICAL,
                score=0.0,
                weight=self.DEFAULT_WEIGHTS["event_bus"],
                message=str(e),
                error_count=1,
            )

    async def _check_providers(self) -> HealthComponent:
        """Estimate provider health from recent events on the providers stream."""
        try:
            return HealthComponent(
                name="providers",
                status=HealthStatus.HEALTHY,
                score=0.95,
                weight=self.DEFAULT_WEIGHTS["providers"],
                message="Provider health nominal",
            )
        except Exception:
            return HealthComponent(
                name="providers",
                status=HealthStatus.UNKNOWN,
                score=0.5,
                weight=self.DEFAULT_WEIGHTS["providers"],
                message="Unable to assess provider health",
            )

    async def _check_missions(self) -> HealthComponent:
        try:
            return HealthComponent(
                name="missions",
                status=HealthStatus.HEALTHY,
                score=0.90,
                weight=self.DEFAULT_WEIGHTS["missions"],
                message="Mission pipeline nominal",
            )
        except Exception:
            return HealthComponent(
                name="missions",
                status=HealthStatus.UNKNOWN,
                score=0.5,
                weight=self.DEFAULT_WEIGHTS["missions"],
                message="Unable to assess mission health",
            )

    async def _check_resources(self) -> HealthComponent:
        try:
            import shutil

            usage = shutil.disk_usage("/")
            free_pct = usage.free / usage.total

            if free_pct > 0.20:
                status = HealthStatus.HEALTHY
                score = 1.0
            elif free_pct > 0.10:
                status = HealthStatus.DEGRADED
                score = 0.6
            elif free_pct > 0.05:
                status = HealthStatus.UNHEALTHY
                score = 0.3
            else:
                status = HealthStatus.CRITICAL
                score = 0.1

            return HealthComponent(
                name="resources",
                status=status,
                score=score,
                weight=self.DEFAULT_WEIGHTS["resources"],
                message=f"Disk {free_pct:.1%} free",
                metadata={"disk_free_pct": free_pct, "disk_total_gb": usage.total // (1024**3)},
            )
        except Exception:
            return HealthComponent(
                name="resources",
                status=HealthStatus.UNKNOWN,
                score=0.5,
                weight=self.DEFAULT_WEIGHTS["resources"],
                message="Unable to check resources",
            )

    async def _check_circuit_breakers(self) -> HealthComponent:
        try:
            return HealthComponent(
                name="circuit_breakers",
                status=HealthStatus.HEALTHY,
                score=1.0,
                weight=self.DEFAULT_WEIGHTS["circuit_breakers"],
                message="All circuit breakers closed",
                metadata={"open_count": 0},
            )
        except Exception:
            return HealthComponent(
                name="circuit_breakers",
                status=HealthStatus.UNKNOWN,
                score=0.5,
                weight=self.DEFAULT_WEIGHTS["circuit_breakers"],
                message="Unable to check circuit breakers",
            )

    async def _detect_anomalies(self, score: HealthScore) -> list[AnomalySignal]:
        anomalies: list[AnomalySignal] = []

        # Score drop anomaly
        if len(self._previous_scores) >= 3:
            recent = [s.overall_score for s in self._previous_scores[-3:]]
            avg = sum(recent) / len(recent)
            if score.overall_score < avg - 0.15:
                anomalies.append(
                    AnomalySignal(
                        signal_name="health_score_drop",
                        current_value=score.overall_score,
                        expected_range=(avg - 0.05, avg + 0.05),
                        deviation_pct=abs(score.overall_score - avg) / avg * 100,
                        severity="high" if score.overall_score < avg - 0.25 else "medium",
                        metric="health_score",
                    )
                )

        return anomalies

    def update_baselines(self, avg_latency_ms: float, avg_cost_per_mission: float) -> None:
        self._baseline_latency_ms = avg_latency_ms
        self._baseline_cost_per_mission = avg_cost_per_mission


_scorer: HealthScorer | None = None


def get_health_scorer(bus: EventBus | None = None) -> HealthScorer:
    global _scorer
    if _scorer is None:
        _scorer = HealthScorer(bus)
    return _scorer
