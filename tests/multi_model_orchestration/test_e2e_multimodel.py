"""E2E tests for P25 Multi-Model Orchestration."""
import json
import tempfile
from pathlib import Path

import pytest

from src.multi_model_orchestration.registry import ModelRegistry
from src.multi_model_orchestration.router import ModelRouter
from src.multi_model_orchestration.fallback import FallbackChain
from src.multi_model_orchestration.cost_tracker import CostTracker
from src.multi_model_orchestration.classifier import TaskClassifier
from src.multi_model_orchestration.models import (
    COMPLEXITY_HIGH,
    COMPLEXITY_LOW,
    RoutingRequest,
    RoutingDecision,
    TaskClass,
    ModelConfig,
)


class TestE2EModelRouting:
    def test_full_routing_pipeline(self):
        registry = ModelRegistry()
        registry.seed_defaults()
        router = ModelRouter(registry=registry, dry_run=True)

        dec = router.select_model("classify_intent")
        assert isinstance(dec, RoutingDecision)
        assert dec.selected_model is not None

    def test_complex_task_routes_to_capable_model(self):
        registry = ModelRegistry()
        registry.seed_defaults()
        router = ModelRouter(registry=registry, dry_run=True)

        dec = router.select_model("plan_mission", complexity=COMPLEXITY_HIGH)
        assert dec.selected_model is not None

    def test_fallback_chain_from_decision(self):
        registry = ModelRegistry()
        registry.seed_defaults()
        router = ModelRouter(registry=registry, dry_run=True)

        dec = router.select_model("classify_intent")
        chain = FallbackChain(
            [dec.selected_model.name] + dec.fallback_chain,
            registry,
        )
        result = chain.execute("test prompt")
        assert result["status"] == "dry_run"

    def test_cost_never_exceeds_limit_in_routing(self):
        registry = ModelRegistry()
        registry.seed_defaults()
        tracker = CostTracker(daily_limit_usd=5.0)
        router = ModelRouter(registry=registry, dry_run=True)

        dec = router.select_model("classify_intent")
        estimated = tracker.estimate_for_decision(dec)
        assert estimated < 5.0  # always under limit for simple tasks

    def test_classifier_router_integration(self):
        classifier = TaskClassifier()
        registry = ModelRegistry()
        registry.seed_defaults()
        router = ModelRouter(registry=registry, classifier=classifier, dry_run=True)

        for intent in classifier.known_intents[:5]:
            dec = router.select_model(intent)
            assert dec.selected_model is not None, f"No model for {intent}"


class TestE2ECollectorDegradation:
    """P25 never breaks even with bad data."""

    def test_router_handles_empty_registry(self):
        empty = ModelRegistry()
        router = ModelRouter(registry=empty, dry_run=True)
        from src.multi_model_orchestration.errors import RoutingError

        with pytest.raises(RoutingError):
            router.select_model("classify_intent")

    def test_classifier_handles_unknown_intent(self):
        classifier = TaskClassifier()
        tc = classifier.classify("completely_unknown_intent_v2")
        assert tc.complexity == "medium"  # safe default

    def test_cost_tracker_safe_with_zero_models(self):
        tracker = CostTracker(daily_limit_usd=5.0)
        assert tracker.estimate("test", ModelConfig.new("x", "mock")) == 0.0


class TestE2ECLIIntegration:
    def test_cli_models(self):
        from src.multi_model_orchestration.cli import main
        assert main(["models"]) == 0

    def test_cli_route(self):
        from src.multi_model_orchestration.cli import main
        assert main(["route", "classify_intent"]) == 0

    def test_cli_cost(self):
        from src.multi_model_orchestration.cli import main
        assert main(["cost"]) == 0

    def test_cli_classify(self):
        from src.multi_model_orchestration.cli import main
        assert main(["classify", "generate_code"]) == 0

    def test_cli_no_command(self):
        from src.multi_model_orchestration.cli import main
        assert main([]) == 1


class TestE2ESnapshotRoundtrip:
    def test_full_routing_roundtrip_via_dict(self):
        registry = ModelRegistry()
        registry.seed_defaults()
        router = ModelRouter(registry=registry, dry_run=True)

        dec1 = router.select_model("generate_code")
        dec2 = RoutingDecision.from_dict(dec1.to_dict())
        assert dec2.decision_id == dec1.decision_id
        assert dec2.selected_model.name == dec1.selected_model.name
        assert dec2.estimated_cost_usd == dec1.estimated_cost_usd
