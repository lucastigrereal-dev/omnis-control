"""Tests for P25 ModelRouter."""
import pytest

from src.multi_model_orchestration.models import (
    CAPABILITY_CODE,
    CAPABILITY_TEXT,
    COMPLEXITY_CRITICAL,
    COMPLEXITY_HIGH,
    COMPLEXITY_LOW,
    PROVIDER_MOCK,
    ModelConfig,
    RoutingRequest,
    TaskClass,
)
from src.multi_model_orchestration.cost_tracker import CostTracker
from src.multi_model_orchestration.registry import ModelRegistry
from src.multi_model_orchestration.router import ModelRouter
from src.multi_model_orchestration.errors import CostLimitError, RoutingError


class TestModelRouter:
    @pytest.fixture
    def registry(self):
        r = ModelRegistry()
        r.seed_defaults()
        return r

    @pytest.fixture
    def router(self, registry):
        return ModelRouter(registry=registry, dry_run=True)

    # ── select_model ──────────────────────────────────────────────────────

    def test_select_model_returns_decision(self, router):
        dec = router.select_model("classify_intent")
        assert dec.decision_id.startswith("mrd_")
        assert dec.is_dry_run is True

    def test_select_model_for_low_complexity(self, router):
        dec = router.select_model("classify_intent")
        assert dec.strategy == "cost_optimal"

    def test_select_model_for_high_complexity(self, router):
        dec = router.select_model("generate_code")
        assert dec.selected_model is not None

    def test_select_model_for_critical_task(self, router):
        dec = router.select_model("execute_financial", risk_level="critical")
        assert dec.selected_model is not None

    def test_select_model_with_preferred_provider(self, router):
        dec = router.select_model("classify_intent", preferred_provider="mock")
        assert dec.selected_model.provider == "mock"

    def test_select_model_with_explicit_complexity(self, router):
        dec = router.select_model("some_task", complexity=COMPLEXITY_HIGH)
        assert dec.selected_model is not None

    def test_select_model_for_task(self, router):
        tc = TaskClass.new("analyze_lead", complexity=COMPLEXITY_LOW)
        dec = router.select_model_for_task(tc)
        assert dec.selected_model is not None

    # ── dry-run execution ─────────────────────────────────────────────────

    def test_execute_dry_run(self, router, registry):
        tc = TaskClass.new("classify_intent", complexity=COMPLEXITY_LOW)
        req = RoutingRequest.new(tc, prompt="test prompt")
        result = router.execute(req)
        assert result["status"] == "dry_run"
        assert "decision" in result

    def test_execute_enforces_cost_limit_before_provider_call(self):
        from src.multi_model_orchestration.adapters.mock_adapter import register as register_mock

        register_mock()
        registry = ModelRegistry()
        registry.register(ModelConfig.new(
            "expensive-mock",
            PROVIDER_MOCK,
            capabilities=[CAPABILITY_TEXT],
            cost_per_1k_tokens=0.05,
        ))
        tracker = CostTracker(daily_limit_usd=0.01, dry_run=False)
        router = ModelRouter(registry=registry, cost_tracker=tracker, dry_run=False)
        task = TaskClass.new(
            "classify_intent",
            complexity=COMPLEXITY_LOW,
            min_capabilities=[CAPABILITY_TEXT],
            max_cost_usd=0.10,
        )
        req = RoutingRequest.new(task, prompt="x" * 5000, dry_run=False)

        with pytest.raises(CostLimitError):
            router.execute(req)

        assert tracker.entry_count == 0

    def test_execute_records_cost_after_provider_result(self):
        from src.multi_model_orchestration.adapters.mock_adapter import register as register_mock

        register_mock()
        registry = ModelRegistry()
        registry.register(ModelConfig.new(
            "metered-mock",
            PROVIDER_MOCK,
            capabilities=[CAPABILITY_TEXT],
            cost_per_1k_tokens=0.01,
        ))
        tracker = CostTracker(daily_limit_usd=1.0, dry_run=False)
        router = ModelRouter(registry=registry, cost_tracker=tracker, dry_run=False)
        task = TaskClass.new(
            "classify_intent",
            complexity=COMPLEXITY_LOW,
            min_capabilities=[CAPABILITY_TEXT],
            max_cost_usd=0.10,
        )
        req = RoutingRequest.new(task, prompt="x" * 4000, dry_run=False)

        result = router.execute(req)

        assert result["status"] == "dry_run"
        assert tracker.entry_count == 1
        assert tracker.by_provider()[PROVIDER_MOCK] == 0.01

    # ── error cases ───────────────────────────────────────────────────────

    def test_empty_registry_raises_routing_error(self):
        empty = ModelRegistry()
        # Disable mock model that seed_defaults would add
        router = ModelRouter(registry=empty, dry_run=True)
        with pytest.raises(RoutingError, match="No enabled model"):
            router.select_model("classify_intent")

    def test_select_model_for_unknown_intent(self, router):
        dec = router.select_model("completely_unknown_intent")
        assert dec.selected_model is not None  # sempre tem mock como fallback
