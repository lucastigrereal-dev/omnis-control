"""P28 PatternAnalyzer — detects recurring patterns in execution feedback."""
from collections import Counter
from typing import Optional

from src.self_improvement.models import (
    ExecutionFeedback, Pattern,
    CATEGORY_PERFORMANCE, CATEGORY_RELIABILITY, CATEGORY_CAPABILITY_GAP,
)
from src.self_improvement.errors import InsufficientDataError


class PatternAnalyzer:
    """Analyzes execution feedback to find recurring patterns."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._patterns: list[Pattern] = []

    def analyze(self, feedbacks: list[ExecutionFeedback]) -> list[Pattern]:
        """Run all pattern detectors against feedback."""
        if not feedbacks:
            raise InsufficientDataError("No feedback data to analyze")

        patterns: list[Pattern] = []
        patterns.extend(self.detect_failure_patterns(feedbacks))
        patterns.extend(self.detect_performance_patterns(feedbacks))
        patterns.extend(self.detect_gap_patterns(feedbacks))
        self._patterns = patterns
        return patterns

    # ── Pattern detectors ─────────────────────────────────────────

    def detect_failure_patterns(self, feedbacks: list[ExecutionFeedback]) -> list[Pattern]:
        """Detect recurring failure patterns."""
        failures = [f for f in feedbacks if f.is_failure]
        if not failures:
            return []

        error_counter: Counter[str] = Counter()
        error_feedback_map: dict[str, list[str]] = {}
        for f in failures:
            for err in f.errors:
                key = err[:60]  # Use first 60 chars as key
                error_counter[key] += 1
                if key not in error_feedback_map:
                    error_feedback_map[key] = []
                error_feedback_map[key].append(f.feedback_id)

        patterns = []
        for error_key, count in error_counter.most_common():
            if count < 2:
                break  # Only report patterns with >= 2 occurrences
            patterns.append(Pattern.new(
                name=f"Failure: {error_key[:40]}",
                category=CATEGORY_RELIABILITY,
                description=f"Recurring error occurred {count} times",
                occurrences=count,
                related_feedback_ids=error_feedback_map.get(error_key, []),
                confidence=min(0.9, 0.3 + count * 0.15),
            ))
        return patterns

    def detect_performance_patterns(self, feedbacks: list[ExecutionFeedback]) -> list[Pattern]:
        """Detect performance anomalies."""
        latencies = [f.latency_ms for f in feedbacks if f.latency_ms > 0]
        if not latencies:
            return []

        avg_latency = sum(latencies) / len(latencies)
        slow_threshold = avg_latency * 1.5
        slow_feedbacks = [f for f in feedbacks if f.latency_ms > slow_threshold]

        if len(slow_feedbacks) >= 2:
            ids = [f.feedback_id for f in slow_feedbacks]
            return [Pattern.new(
                name="High latency detected",
                category=CATEGORY_PERFORMANCE,
                description=f"{len(slow_feedbacks)} executions exceeded {slow_threshold:.0f}ms (avg: {avg_latency:.0f}ms)",
                occurrences=len(slow_feedbacks),
                related_feedback_ids=ids,
                confidence=0.6,
            )]
        return []

    def detect_gap_patterns(self, feedbacks: list[ExecutionFeedback]) -> list[Pattern]:
        """Detect missing capability gaps from errors/warnings."""
        gaps: Counter[str] = Counter()
        gap_feedback_map: dict[str, list[str]] = {}

        for f in feedbacks:
            for warn in f.warnings:
                if "missing" in warn.lower() or "gap" in warn.lower() or "not found" in warn.lower():
                    key = warn[:60]
                    gaps[key] += 1
                    if key not in gap_feedback_map:
                        gap_feedback_map[key] = []
                    gap_feedback_map[key].append(f.feedback_id)

        patterns = []
        for gap_key, count in gaps.most_common():
            patterns.append(Pattern.new(
                name=f"Gap: {gap_key[:40]}",
                category=CATEGORY_CAPABILITY_GAP,
                description=f"Capability gap detected {count} times",
                occurrences=count,
                related_feedback_ids=gap_feedback_map.get(gap_key, []),
                confidence=min(0.8, 0.3 + count * 0.2),
            ))
        return patterns

    # ── Query ─────────────────────────────────────────────────────

    def get_patterns(self) -> list[Pattern]:
        return list(self._patterns)

    @property
    def pattern_count(self) -> int:
        return len(self._patterns)

    def compare_with_history(self, pattern: Pattern, historical: Optional[list[Pattern]] = None) -> list[Pattern]:
        """Find similar patterns in historical data."""
        if not historical:
            return []
        return [h for h in historical if h.category == pattern.category]
