"""CostTrackingWorkflow — Onda 31.

Wraps CostTracker for batch cost recording and reporting:
  usage entries → CostTracker.record() → breakdown → Akasha
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass

from src.multi_model_orchestration.cost_tracker import CostTracker
from src.multi_model_orchestration.models import ModelConfig
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkEvent


def _run_id() -> str:
    return secrets.token_hex(6)


@dataclass
class CostTrackingResult:
    run_id: str
    success: bool
    entries_recorded: int
    daily_total_usd: float
    remaining_budget_usd: float
    by_model: dict[str, float]
    by_provider: dict[str, float]
    by_task_type: dict[str, float]
    within_limit: bool
    akasha_event_id: str
    dry_run: bool
    cost_local_pct: int = 100
    error: str | None = None

    @property
    def unique_models(self) -> int:
        return len(self.by_model)

    @property
    def unique_providers(self) -> int:
        return len(self.by_provider)

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "entries_recorded": self.entries_recorded,
            "daily_total_usd": self.daily_total_usd,
            "remaining_budget_usd": self.remaining_budget_usd,
            "unique_models": self.unique_models,
            "unique_providers": self.unique_providers,
            "by_model": self.by_model,
            "by_provider": self.by_provider,
            "by_task_type": self.by_task_type,
            "within_limit": self.within_limit,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
        }


class CostTrackingWorkflow:
    """Registra e agrega custos de uso de modelos via CostTracker."""

    def __init__(
        self,
        daily_limit_usd: float = 5.0,
        akasha_sink=None,
    ) -> None:
        self.daily_limit_usd = daily_limit_usd
        self._sink = akasha_sink or MockAkashaSink()

    def run(
        self,
        entries: list[dict],
        dry_run: bool = True,
    ) -> CostTrackingResult:
        run_id = _run_id()

        if not entries:
            event = SinkEvent(
                event_type="cost_tracking_report",
                source=run_id,
                payload={"error": "empty_entries", "entries_count": 0},
            )
            self._sink.write_event(event)
            return CostTrackingResult(
                run_id=run_id,
                success=False,
                entries_recorded=0,
                daily_total_usd=0.0,
                remaining_budget_usd=self.daily_limit_usd,
                by_model={},
                by_provider={},
                by_task_type={},
                within_limit=True,
                akasha_event_id=event.event_id,
                dry_run=dry_run,
                error="empty_entries",
            )

        tracker = CostTracker(daily_limit_usd=self.daily_limit_usd, dry_run=dry_run)

        for item in entries:
            model = ModelConfig(
                model_id=item.get("model_id", item.get("model_name", "unknown")),
                name=item.get("model_name", "unknown"),
                provider=item.get("provider", "unknown"),
                cost_per_1k_tokens=float(item.get("cost_per_1k_tokens", 0.002)),
            )
            task_type = item.get("task_type", "general")
            tokens_used = int(item.get("tokens_used", 0))
            tracker.record(model, task_type, tokens_used)

        event = SinkEvent(
            event_type="cost_tracking_report",
            source=run_id,
            payload={
                "entries_recorded": tracker.entry_count,
                "daily_total_usd": tracker.daily_total,
                "within_limit": tracker.check_limit(),
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return CostTrackingResult(
            run_id=run_id,
            success=True,
            entries_recorded=tracker.entry_count,
            daily_total_usd=tracker.daily_total,
            remaining_budget_usd=tracker.remaining_budget,
            by_model=tracker.by_model(),
            by_provider=tracker.by_provider(),
            by_task_type=tracker.by_task_type(),
            within_limit=tracker.check_limit(),
            akasha_event_id=event.event_id,
            dry_run=dry_run,
        )
