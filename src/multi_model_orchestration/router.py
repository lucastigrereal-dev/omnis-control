"""P25 ModelRouter — select best model for each task."""
from __future__ import annotations

from typing import Optional

from src.multi_model_orchestration.adapters import ADAPTER_REGISTRY, ModelAdapter, get_adapter
from src.multi_model_orchestration.classifier import TaskClassifier
from src.multi_model_orchestration.errors import AllModelsExhaustedError, RoutingError
from src.multi_model_orchestration.fallback import FallbackChain
from src.multi_model_orchestration.models import (
    COMPLEXITY_CRITICAL,
    COMPLEXITY_HIGH,
    PROVIDER_MOCK,
    STRATEGY_COST_OPTIMAL,
    STRATEGY_FALLBACK,
    STRATEGY_PERFORMANCE,
    ModelConfig,
    RoutingDecision,
    RoutingRequest,
    TaskClass,
)
from src.multi_model_orchestration.registry import ModelRegistry


class ModelRouter:
    """Routes tasks to the best available model based on cost, capability, and strategy."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        classifier: Optional[TaskClassifier] = None,
        dry_run: bool = True,
    ) -> None:
        self.registry = registry or ModelRegistry(dry_run=dry_run)
        self.classifier = classifier or TaskClassifier(dry_run=dry_run)
        self.dry_run = dry_run

    # ── Public API ─────────────────────────────────────────────────────────

    def select_model(
        self,
        task_type: str,
        complexity: Optional[str] = None,
        risk_level: str = "low",
        preferred_provider: str = "",
        prompt: str = "",
    ) -> RoutingDecision:
        """Select the best model for a task."""
        task = self.classifier.classify(task_type, risk_level=risk_level)
        if complexity and complexity != task.complexity:
            task.complexity = complexity

        request = RoutingRequest.new(task, prompt=prompt, preferred_provider=preferred_provider)
        return self._decide(request)

    def select_model_for_task(self, task: TaskClass, preferred_provider: str = "") -> RoutingDecision:
        """Select best model for a pre-classified task."""
        request = RoutingRequest.new(task, preferred_provider=preferred_provider)
        return self._decide(request)

    def execute(self, request: RoutingRequest) -> dict:
        """Full pipeline: route → execute → result."""
        decision = self._decide(request)

        if self.dry_run:
            return {
                "status": "dry_run",
                "decision": decision.to_dict(),
                "content": f"[DRY-RUN] Would execute on {decision.selected_model.name}",
            }

        adapter = get_adapter(decision.selected_model.provider)
        if adapter is None:
            raise RoutingError(f"No adapter for provider: {decision.selected_model.provider!r}")

        try:
            result = adapter.execute(request.prompt, decision.selected_model, context=request.context)
            result["decision"] = decision.to_dict()
            return result
        except Exception:
            if decision.has_fallback:
                chain = FallbackChain(decision.fallback_chain, self.registry)
                return chain.execute(request.prompt, request.context.to_dict() if hasattr(request.context, "to_dict") else request.context)
            raise

    # ── Internal ────────────────────────────────────────────────────────────

    def _decide(self, request: RoutingRequest) -> RoutingDecision:
        """Core decision logic."""
        candidates = self.registry.find_for_task(request.task)

        # Preferred provider filter
        if request.preferred_provider:
            preferred = [m for m in candidates if m.provider == request.preferred_provider]
            if preferred:
                candidates = preferred

        if not candidates:
            raise RoutingError(f"No enabled model found for task: {request.task.task_type!r}")

        selected, fallback_chain, reason, strategy = self._pick(candidates, request.task)

        return RoutingDecision.new(
            request_id=request.request_id,
            selected_model=selected,
            fallback_chain=fallback_chain,
            reason=reason,
            estimated_cost_usd=selected.cost_per_1k_tokens * max(1, len(request.prompt) // 1000),
            estimated_tokens=max(1, len(request.prompt) // 4),
            strategy=strategy,
            is_dry_run=self.dry_run,
        )

    @staticmethod
    @staticmethod
    def _pick(candidates: list[ModelConfig], task: TaskClass) -> tuple[ModelConfig, list[str], str, str]:
        """Pick the best model and build a fallback chain."""
        if task.complexity == COMPLEXITY_CRITICAL:
            # Critical: most capable first
            primary = candidates[0]
            fallback = [m.name for m in candidates[1:3]]
            return primary, fallback, f"Most capable model for critical task: {task.task_type}", STRATEGY_PERFORMANCE

        if task.complexity == COMPLEXITY_HIGH:
            # High: most capable within budget
            primary = candidates[0]
            fallback = [m.name for m in candidates[1:3]]
            return primary, fallback, f"Capable model within budget for: {task.task_type}", STRATEGY_COST_OPTIMAL

        # Low / Medium: cheapest capable
        primary = candidates[0]
        fallback = [m.name for m in candidates[1:3]] if len(candidates) > 1 else []
        return primary, fallback, f"Cost-optimal model for: {task.task_type}", STRATEGY_COST_OPTIMAL
