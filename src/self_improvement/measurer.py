"""P28 ImpactMeasurer — measures impact of implemented improvements."""
from typing import Optional

from src.self_improvement.models import (
    ImprovementProposal, ImpactMeasurement, ExecutionFeedback,
    VERDICT_IMPROVED, VERDICT_DEGRADED, VERDICT_NEUTRAL, VERDICT_INSUFFICIENT_DATA,
    PROPOSAL_MEASURED,
)
from src.self_improvement.errors import InsufficientDataError


class ImpactMeasurer:
    """Measures before/after impact of improvements."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._measurements: list[ImpactMeasurement] = []

    def measure(self, proposal: ImprovementProposal,
                before_feedbacks: list[ExecutionFeedback],
                after_feedbacks: list[ExecutionFeedback]) -> ImpactMeasurement:
        """Measure impact by comparing before/after feedback data."""

        metric = self._choose_metric(proposal)

        if not before_feedbacks or not after_feedbacks:
            m = ImpactMeasurement.new(proposal.proposal_id, metric=metric,
                                      verdict=VERDICT_INSUFFICIENT_DATA, sample_size=0)
            self._measurements.append(m)
            return m

        before_value = self._aggregate(before_feedbacks, metric)
        after_value = self._aggregate(after_feedbacks, metric)

        delta = after_value - before_value
        verdict = self._verdict_for(proposal, before_value, after_value, delta)

        m = ImpactMeasurement.new(
            proposal.proposal_id,
            metric=metric,
            value_before=before_value,
            value_after=after_value,
            verdict=verdict,
            sample_size=len(after_feedbacks),
        )
        proposal.status = PROPOSAL_MEASURED
        self._measurements.append(m)
        return m

    # ── Helpers ───────────────────────────────────────────────────

    def _choose_metric(self, proposal: ImprovementProposal) -> str:
        category_metrics = {
            "performance": "avg_latency_ms",
            "reliability": "failure_rate",
            "cost": "cost_per_mission",
            "capability_gap": "mission_success_rate",
            "security": "policy_violations",
        }
        return category_metrics.get(proposal.category, "mission_success_rate")

    def _aggregate(self, feedbacks: list[ExecutionFeedback], metric: str) -> float:
        if metric == "avg_latency_ms":
            vals = [f.latency_ms for f in feedbacks if f.latency_ms > 0]
            return sum(vals) / len(vals) if vals else 0.0
        if metric == "failure_rate":
            failures = sum(1 for f in feedbacks if f.is_failure)
            return failures / len(feedbacks) if feedbacks else 0.0
        if metric == "mission_success_rate":
            successes = sum(1 for f in feedbacks if f.status == "success")
            return successes / len(feedbacks) if feedbacks else 0.0
        if metric == "cost_per_mission":
            return 0.01  # Mock
        if metric == "policy_violations":
            return sum(len(f.errors) for f in feedbacks) / max(len(feedbacks), 1)
        return 0.0

    def _verdict_for(self, proposal: ImprovementProposal,
                     before: float, after: float, delta: float) -> str:
        """Determine if the change was an improvement or degradation."""
        if abs(delta) < 0.01:
            return VERDICT_NEUTRAL

        # For metrics where lower is better (latency, failure_rate, cost, violations)
        lower_better = {"avg_latency_ms", "failure_rate", "cost_per_mission", "policy_violations"}
        metric = self._choose_metric(proposal)

        if metric in lower_better:
            return VERDICT_IMPROVED if delta < 0 else VERDICT_DEGRADED
        else:
            return VERDICT_IMPROVED if delta > 0 else VERDICT_DEGRADED

    # ── Comparison ────────────────────────────────────────────────

    def compare_metrics(self, metric: str, before: list[float], after: list[float]) -> dict:
        """Compare metric distributions before vs after."""
        if not before or not after:
            return {"verdict": VERDICT_INSUFFICIENT_DATA, "reason": "Empty data"}

        avg_before = sum(before) / len(before)
        avg_after = sum(after) / len(after)
        delta = avg_after - avg_before

        return {
            "avg_before": avg_before,
            "avg_after": avg_after,
            "delta": delta,
            "change_pct": (delta / avg_before * 100) if avg_before != 0 else 0.0,
            "sample_before": len(before),
            "sample_after": len(after),
        }

    def is_significant(self, measurement: ImpactMeasurement) -> bool:
        """Check if the measured impact is statistically meaningful."""
        return measurement.sample_size >= 5 and abs(measurement.delta) > 0.01

    # ── Query ─────────────────────────────────────────────────────

    def get_measurements(self) -> list[ImpactMeasurement]:
        return list(self._measurements)

    @property
    def count(self) -> int:
        return len(self._measurements)
