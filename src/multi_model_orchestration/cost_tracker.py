"""P25 CostTracker — track and limit model API costs."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.multi_model_orchestration.errors import CostLimitError
from src.multi_model_orchestration.models import ModelConfig, RoutingDecision


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class CostEntry:
    """Single cost record."""
    model_name: str
    provider: str
    task_type: str
    tokens_used: int
    cost_usd: float
    timestamp: str = field(default_factory=_now_iso)


class CostTracker:
    """Tracks cumulative API costs with configurable daily limit."""

    def __init__(
        self,
        daily_limit_usd: float = 5.0,
        dry_run: bool = True,
    ) -> None:
        self.daily_limit_usd = daily_limit_usd
        self.dry_run = dry_run
        self._entries: list[CostEntry] = []

    # ── Estimate ────────────────────────────────────────────────────────────

    def estimate(self, prompt: str, model: ModelConfig) -> float:
        """Estimate cost for a prompt without executing."""
        estimated_tokens = max(1, len(prompt) // 4)
        return (estimated_tokens / 1000) * model.cost_per_1k_tokens

    def estimate_for_decision(self, decision: RoutingDecision) -> float:
        """Estimate cost from a routing decision."""
        return decision.estimated_cost_usd

    # ── Record ──────────────────────────────────────────────────────────────

    def record(self, model: ModelConfig, task_type: str, tokens_used: int) -> float:
        """Record actual usage. Returns cost."""
        cost = (tokens_used / 1000) * model.cost_per_1k_tokens
        entry = CostEntry(
            model_name=model.name,
            provider=model.provider,
            task_type=task_type,
            tokens_used=tokens_used,
            cost_usd=cost,
        )
        self._entries.append(entry)
        return cost

    # ── Limits ──────────────────────────────────────────────────────────────

    def check_limit(self, estimated_cost: float = 0.0) -> bool:
        """Check if an estimated cost would exceed the daily limit."""
        if self.dry_run:
            return True
        return self.daily_total + estimated_cost <= self.daily_limit_usd

    def assert_within_limit(self, estimated_cost: float = 0.0) -> None:
        """Raise CostLimitError if estimated cost exceeds daily limit."""
        if not self.check_limit(estimated_cost):
            raise CostLimitError(
                f"Estimated cost ${estimated_cost:.4f} would exceed daily limit ${self.daily_limit_usd:.2f}. "
                f"Current spend: ${self.daily_total:.4f}"
            )

    # ── Totals ──────────────────────────────────────────────────────────────

    @property
    def daily_total(self) -> float:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return sum(e.cost_usd for e in self._entries if e.timestamp.startswith(today))

    def by_model(self) -> dict[str, float]:
        """Cost breakdown by model name."""
        breakdown: dict[str, float] = {}
        for e in self._entries:
            breakdown[e.model_name] = breakdown.get(e.model_name, 0.0) + e.cost_usd
        return breakdown

    def by_provider(self) -> dict[str, float]:
        """Cost breakdown by provider."""
        breakdown: dict[str, float] = {}
        for e in self._entries:
            breakdown[e.provider] = breakdown.get(e.provider, 0.0) + e.cost_usd
        return breakdown

    def by_task_type(self) -> dict[str, float]:
        """Cost breakdown by task type."""
        breakdown: dict[str, float] = {}
        for e in self._entries:
            breakdown[e.task_type] = breakdown.get(e.task_type, 0.0) + e.cost_usd
        return breakdown

    # ── Info ────────────────────────────────────────────────────────────────

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    @property
    def remaining_budget(self) -> float:
        return max(0.0, self.daily_limit_usd - self.daily_total)

    def entries_today(self) -> list[CostEntry]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return [e for e in self._entries if e.timestamp.startswith(today)]

    def reset(self) -> None:
        """Clear all entries (for testing)."""
        self._entries.clear()

    def to_dict(self) -> dict:
        return {
            "daily_limit_usd": self.daily_limit_usd,
            "daily_total": self.daily_total,
            "remaining_budget": self.remaining_budget,
            "entry_count": self.entry_count,
            "by_model": self.by_model(),
            "by_provider": self.by_provider(),
            "by_task_type": self.by_task_type(),
        }
