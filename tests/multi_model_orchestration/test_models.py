"""Tests for P25 Multi-Model Orchestration — models."""
import pytest

from src.multi_model_orchestration.models import (
    COMPLEXITY_HIGH,
    COMPLEXITY_LOW,
    COMPLEXITY_MEDIUM,
    PROVIDER_ANTHROPIC,
    PROVIDER_GROQ,
    PROVIDER_MOCK,
    STRATEGY_COST_OPTIMAL,
    STRATEGY_FALLBACK,
    ModelConfig,
    RoutingDecision,
    RoutingRequest,
    TaskClass,
)
from src.multi_model_orchestration.errors import InvalidModelConfigError


class TestModelConfig:
    def test_new_creates_valid_model(self):
        m = ModelConfig.new("claude-haiku", PROVIDER_ANTHROPIC, cost_per_1k_tokens=0.001, avg_latency_ms=200)
        assert m.model_id.startswith("mm_")
        assert m.name == "claude-haiku"
        assert m.provider == PROVIDER_ANTHROPIC
        assert m.enabled is True
        assert m.priority == 1

    def test_new_defaults(self):
        m = ModelConfig.new("test-model", PROVIDER_MOCK)
        assert m.capabilities == []
        assert m.cost_per_1k_tokens == 0.0
        assert m.max_tokens == 4096

    def test_new_rejects_invalid_provider(self):
        with pytest.raises(ValueError, match="Invalid provider"):
            ModelConfig.new("bad", "invalid_provider")

    def test_to_dict_and_from_dict_roundtrip(self):
        m = ModelConfig.new("claude-opus", PROVIDER_ANTHROPIC, capabilities=["code", "analysis"], cost_per_1k_tokens=0.015)
        d = m.to_dict()
        m2 = ModelConfig.from_dict(d)
        assert m2.model_id == m.model_id
        assert m2.name == m.name
        assert m2.capabilities == m.capabilities
        assert m2.cost_per_1k_tokens == m.cost_per_1k_tokens

    def test_is_cheap_true(self):
        m = ModelConfig.new("cheap-model", PROVIDER_GROQ, cost_per_1k_tokens=0.001)
        assert m.is_cheap is True

    def test_is_cheap_false(self):
        m = ModelConfig.new("expensive", PROVIDER_ANTHROPIC, cost_per_1k_tokens=0.015)
        assert m.is_cheap is False

    def test_is_fast_true(self):
        m = ModelConfig.new("fast-model", PROVIDER_GROQ, avg_latency_ms=200)
        assert m.is_fast is True

    def test_is_fast_false(self):
        m = ModelConfig.new("slow-model", PROVIDER_ANTHROPIC, avg_latency_ms=2000)
        assert m.is_fast is False

    def test_disabled_model(self):
        m = ModelConfig.new("disabled-model", PROVIDER_MOCK, enabled=False)
        assert m.enabled is False

    def test_custom_priority(self):
        m = ModelConfig.new("fallback-model", PROVIDER_GROQ, priority=3)
        assert m.priority == 3


class TestTaskClass:
    def test_new_defaults(self):
        tc = TaskClass.new("classify_intent")
        assert tc.task_id.startswith("tc_")
        assert tc.task_type == "classify_intent"
        assert tc.complexity == COMPLEXITY_MEDIUM
        assert tc.risk_level == "low"

    def test_new_custom_complexity(self):
        tc = TaskClass.new("plan_mission", complexity=COMPLEXITY_HIGH, risk_level="high")
        assert tc.complexity == COMPLEXITY_HIGH
        assert tc.risk_level == "high"

    def test_new_rejects_invalid_complexity(self):
        with pytest.raises(ValueError, match="Invalid complexity"):
            TaskClass.new("test", complexity="impossible")

    def test_new_with_capabilities(self):
        tc = TaskClass.new("generate_code", min_capabilities=["code", "analysis"])
        assert "code" in tc.min_capabilities
        assert "analysis" in tc.min_capabilities

    def test_new_creativity_flags(self):
        tc = TaskClass.new("generate_hook", requires_creativity=True, requires_precision=True)
        assert tc.requires_creativity is True
        assert tc.requires_precision is True

    def test_to_dict_and_from_dict_roundtrip(self):
        tc = TaskClass.new("analyze_lead", complexity=COMPLEXITY_MEDIUM, max_cost_usd=0.05)
        d = tc.to_dict()
        tc2 = TaskClass.from_dict(d)
        assert tc2.task_id == tc.task_id
        assert tc2.task_type == tc.task_type
        assert tc2.max_cost_usd == tc.max_cost_usd

    def test_max_latency_default(self):
        tc = TaskClass.new("summarize_mission")
        assert tc.max_latency_ms == 5000

    def test_max_cost_default(self):
        tc = TaskClass.new("classify_intent")
        assert tc.max_cost_usd == 0.10


class TestRoutingRequest:
    def test_new_creates_request(self):
        tc = TaskClass.new("classify_intent", complexity=COMPLEXITY_LOW)
        req = RoutingRequest.new(tc, prompt="classify this", dry_run=True)
        assert req.request_id.startswith("mrr_")
        assert req.task.task_type == "classify_intent"
        assert req.dry_run is True

    def test_new_default_dry_run(self):
        tc = TaskClass.new("classify_intent")
        req = RoutingRequest.new(tc)
        assert req.dry_run is True

    def test_new_with_context(self):
        tc = TaskClass.new("analyze_lead")
        req = RoutingRequest.new(tc, context={"lead_id": "L001"})
        assert req.context["lead_id"] == "L001"

    def test_new_with_preferred_provider(self):
        tc = TaskClass.new("generate_code")
        req = RoutingRequest.new(tc, preferred_provider=PROVIDER_ANTHROPIC)
        assert req.preferred_provider == PROVIDER_ANTHROPIC

    def test_to_dict_and_from_dict_roundtrip(self):
        tc = TaskClass.new("summarize_mission")
        req = RoutingRequest.new(tc, prompt="summarize this")
        d = req.to_dict()
        req2 = RoutingRequest.from_dict(d)
        assert req2.request_id == req.request_id
        assert req2.task.task_type == req.task.task_type

    def test_from_dict_with_missing_task(self):
        d = {"request_id": "mrr_test"}
        req = RoutingRequest.from_dict(d)
        assert req.task.task_type == "unknown"


class TestRoutingDecision:
    def test_new_creates_decision(self):
        model = ModelConfig.new("claude-haiku", PROVIDER_ANTHROPIC, cost_per_1k_tokens=0.001)
        dec = RoutingDecision.new("mrr_test", model, reason="cheapest capable model")
        assert dec.decision_id.startswith("mrd_")
        assert dec.selected_model.name == "claude-haiku"
        assert dec.reason == "cheapest capable model"
        assert dec.is_dry_run is True

    def test_new_with_fallback_chain(self):
        model = ModelConfig.new("claude-opus", PROVIDER_ANTHROPIC)
        dec = RoutingDecision.new("mrr_test", model, fallback_chain=["gpt-4o", "llama-3-70b"])
        assert len(dec.fallback_chain) == 2
        assert dec.has_fallback is True

    def test_has_fallback_false_when_empty(self):
        model = ModelConfig.new("claude-opus", PROVIDER_ANTHROPIC)
        dec = RoutingDecision.new("mrr_test", model)
        assert dec.has_fallback is False

    def test_to_dict_and_from_dict_roundtrip(self):
        model = ModelConfig.new("claude-opus", PROVIDER_ANTHROPIC, capabilities=["code", "analysis"])
        dec = RoutingDecision.new("mrr_test", model, reason="test", strategy=STRATEGY_FALLBACK)
        d = dec.to_dict()
        dec2 = RoutingDecision.from_dict(d)
        assert dec2.decision_id == dec.decision_id
        assert dec2.selected_model.name == dec.selected_model.name
        assert dec2.strategy == STRATEGY_FALLBACK

    def test_from_dict_with_bad_model_data(self):
        d = {"decision_id": "mrd_test", "selected_model": "not_a_dict"}
        dec = RoutingDecision.from_dict(d)
        assert dec.selected_model.name == "unknown"
        assert dec.selected_model.provider == PROVIDER_MOCK

    def test_estimated_cost_tracked(self):
        model = ModelConfig.new("claude-haiku", PROVIDER_ANTHROPIC, cost_per_1k_tokens=0.001)
        dec = RoutingDecision.new("mrr_test", model, estimated_cost_usd=0.0005, estimated_tokens=500)
        assert dec.estimated_cost_usd == 0.0005
        assert dec.estimated_tokens == 500

    def test_default_strategy(self):
        model = ModelConfig.new("claude-haiku", PROVIDER_ANTHROPIC)
        dec = RoutingDecision.new("mrr_test", model)
        assert dec.strategy == STRATEGY_COST_OPTIMAL
