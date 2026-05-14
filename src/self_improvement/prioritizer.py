"""P28 GapPrioritizer — ranks gaps by impact, frequency, urgency."""
from src.self_improvement.models import (
    Pattern, PrioritizedGap,
    SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL,
    CATEGORY_PERFORMANCE, CATEGORY_RELIABILITY, CATEGORY_COST, CATEGORY_SECURITY,
)


class GapPrioritizer:
    """Ranks detected gaps by composite score (impact × frequency × urgency)."""

    _IMPACT_BY_CATEGORY = {
        CATEGORY_SECURITY: 10.0,
        CATEGORY_RELIABILITY: 8.0,
        CATEGORY_PERFORMANCE: 5.0,
        CATEGORY_COST: 4.0,
        "capability_gap": 6.0,
    }

    _URGENCY_WEIGHT = {
        SEVERITY_CRITICAL: 10.0,
        SEVERITY_HIGH: 7.0,
        SEVERITY_MEDIUM: 4.0,
        SEVERITY_LOW: 2.0,
    }

    def __init__(self):
        self._gaps: list[PrioritizedGap] = []

    def prioritize(self, patterns: list[Pattern]) -> list[PrioritizedGap]:
        """Create prioritized gaps from patterns and rank them."""
        gaps = []
        for pattern in patterns:
            gap = PrioritizedGap.new(
                pattern,
                score=self._score(pattern),
                impact_estimate=self._impact_estimate(pattern),
                urgency=self._derived_urgency(pattern),
            )
            gaps.append(gap)

        # Sort descending by score, assign ranks
        gaps.sort(key=lambda g: g.score, reverse=True)
        for i, g in enumerate(gaps, 1):
            g.rank = i

        self._gaps = gaps
        return gaps

    def _score(self, pattern: Pattern) -> float:
        impact = self._IMPACT_BY_CATEGORY.get(pattern.category, 3.0)
        occurrence_bonus = min(pattern.occurrences, 10) * 0.5
        confidence_factor = 0.5 + pattern.confidence * 0.5
        return (impact + occurrence_bonus) * confidence_factor

    def _impact_estimate(self, pattern: Pattern) -> str:
        impact = self._IMPACT_BY_CATEGORY.get(pattern.category, 3.0)
        if impact >= 8:
            return "High impact — affects system reliability or security"
        if impact >= 5:
            return "Medium impact — affects performance or capability"
        return "Low impact — optimization or minor improvement"

    def _derived_urgency(self, pattern: Pattern) -> str:
        if pattern.occurrences >= 5:
            return SEVERITY_CRITICAL
        if pattern.occurrences >= 3:
            return SEVERITY_HIGH
        if pattern.occurrences >= 2:
            return SEVERITY_MEDIUM
        return SEVERITY_LOW

    # ── Query ─────────────────────────────────────────────────────

    def top_n(self, n: int = 10) -> list[PrioritizedGap]:
        return self._gaps[:n]

    def get_gaps(self) -> list[PrioritizedGap]:
        return list(self._gaps)

    @property
    def count(self) -> int:
        return len(self._gaps)
