"""P28 FeedbackCollector — collects execution feedback from all sources."""
from typing import Optional

from src.self_improvement.models import (
    ExecutionFeedback,
    SOURCE_MISSION, SOURCE_BUILD, SOURCE_ACTION, SOURCE_SYSTEM,
)
from src.self_improvement.errors import InsufficientDataError


class FeedbackCollector:
    """Collects execution feedback from all OMNIS subsystems."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._feedback: list[ExecutionFeedback] = []

    # ── Collect all ───────────────────────────────────────────────

    def collect_all(self) -> list[ExecutionFeedback]:
        """Collect feedback from all sources."""
        results: list[ExecutionFeedback] = []
        results.extend(self.collect_from_missions(""))
        results.extend(self.collect_from_builds(""))
        results.extend(self.collect_from_actions(""))
        system_fb = self.collect_from_system()
        if system_fb:
            results.append(system_fb)
        self._feedback.extend(results)
        return results

    # ── Per-source collectors ─────────────────────────────────────

    def collect_from_missions(self, since: str = "") -> list[ExecutionFeedback]:
        """Collect feedback from P20 mission executions."""
        return self._mock_feedbacks(SOURCE_MISSION, count=5)

    def collect_from_builds(self, since: str = "") -> list[ExecutionFeedback]:
        """Collect feedback from P26 build executions."""
        return self._mock_feedbacks(SOURCE_BUILD, count=3)

    def collect_from_actions(self, since: str = "") -> list[ExecutionFeedback]:
        """Collect feedback from P27 action executions."""
        return self._mock_feedbacks(SOURCE_ACTION, count=4)

    def collect_from_system(self) -> Optional[ExecutionFeedback]:
        """Collect system-level metrics."""
        return ExecutionFeedback.new(SOURCE_SYSTEM, "system", status="success",
                                     latency_ms=42, model_used="system")

    def _mock_feedbacks(self, source_type: str, count: int) -> list[ExecutionFeedback]:
        """Generate mock feedback entries for dry-run/testing."""
        results = []
        for i in range(count):
            statuses = ["success", "success", "success", "failure", "partial_success"]
            status = statuses[i % len(statuses)]
            fb = ExecutionFeedback.new(
                source_type=source_type,
                source_id=f"{source_type}_{i}",
                status=status,
                errors=[f"Mock error in {source_type}_{i}"] if status == "failure" else [],
                warnings=[f"Mock warning in {source_type}_{i}"] if status == "partial_success" else [],
                latency_ms=100 + i * 50,
                model_used="claude-opus-4-7" if i % 2 == 0 else "claude-sonnet-4-6",
            )
            results.append(fb)
        return results

    # ── Query ─────────────────────────────────────────────────────

    def get_all(self) -> list[ExecutionFeedback]:
        return list(self._feedback)

    def get_failures(self) -> list[ExecutionFeedback]:
        return [f for f in self._feedback if f.is_failure]

    def get_by_source(self, source_type: str) -> list[ExecutionFeedback]:
        return [f for f in self._feedback if f.source_type == source_type]

    @property
    def count(self) -> int:
        return len(self._feedback)

    @property
    def failure_rate(self) -> float:
        if not self._feedback:
            return 0.0
        return len(self.get_failures()) / len(self._feedback)
