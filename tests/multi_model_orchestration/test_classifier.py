"""Tests for P25 TaskClassifier."""
import pytest

from src.multi_model_orchestration.classifier import TaskClassifier
from src.multi_model_orchestration.models import (
    CAPABILITY_ANALYSIS,
    CAPABILITY_CLASSIFICATION,
    CAPABILITY_CODE,
    CAPABILITY_PLANNING,
    CAPABILITY_SUMMARIZATION,
    COMPLEXITY_CRITICAL,
    COMPLEXITY_HIGH,
    COMPLEXITY_LOW,
    COMPLEXITY_MEDIUM,
)


class TestTaskClassifier:
    @pytest.fixture
    def classifier(self):
        return TaskClassifier()

    def test_classify_known_intent_low_complexity(self, classifier):
        tc = classifier.classify("classify_intent")
        assert tc.complexity == COMPLEXITY_LOW
        assert CAPABILITY_CLASSIFICATION in tc.min_capabilities
        assert tc.requires_precision is True

    def test_classify_known_intent_medium_complexity(self, classifier):
        tc = classifier.classify("generate_caption")
        assert tc.complexity == COMPLEXITY_MEDIUM
        assert tc.requires_creativity is True

    def test_classify_known_intent_high_complexity(self, classifier):
        tc = classifier.classify("plan_mission")
        assert tc.complexity == COMPLEXITY_HIGH
        assert CAPABILITY_PLANNING in tc.min_capabilities

    def test_classify_known_intent_critical_complexity(self, classifier):
        tc = classifier.classify("execute_financial", risk_level="critical")
        assert tc.complexity == COMPLEXITY_CRITICAL
        assert tc.risk_level == "critical"

    def test_classify_unknown_intent_uses_defaults(self, classifier):
        tc = classifier.classify("some_new_intent")
        assert tc.task_type == "some_new_intent"
        assert tc.complexity == COMPLEXITY_MEDIUM
        assert tc.min_capabilities == ["text"]

    def test_classify_code_generation(self, classifier):
        tc = classifier.classify("generate_code")
        assert CAPABILITY_CODE in tc.min_capabilities
        assert tc.complexity == COMPLEXITY_HIGH

    def test_classify_scaffold_skill(self, classifier):
        tc = classifier.classify("scaffold_skill")
        assert tc.complexity == COMPLEXITY_MEDIUM
        assert CAPABILITY_CODE in tc.min_capabilities

    def test_classify_batch(self, classifier):
        results = classifier.classify_batch(["classify_intent", "plan_mission", "generate_code"])
        assert len(results) == 3
        assert results[0].complexity == COMPLEXITY_LOW
        assert results[1].complexity == COMPLEXITY_HIGH
        assert results[2].complexity == COMPLEXITY_HIGH

    def test_get_complexity_quick_lookup(self, classifier):
        assert classifier.get_complexity("classify_intent") == COMPLEXITY_LOW
        assert classifier.get_complexity("generate_caption") == COMPLEXITY_MEDIUM
        assert classifier.get_complexity("plan_mission") == COMPLEXITY_HIGH

    def test_get_complexity_unknown(self, classifier):
        assert classifier.get_complexity("nonexistent") == COMPLEXITY_MEDIUM

    def test_get_capabilities_quick_lookup(self, classifier):
        caps = classifier.get_capabilities("analyze_metrics")
        assert CAPABILITY_ANALYSIS in caps

    def test_get_capabilities_unknown(self, classifier):
        assert classifier.get_capabilities("nonexistent") == ["text"]

    def test_known_intents_list(self, classifier):
        intents = classifier.known_intents
        assert "classify_intent" in intents
        assert "plan_mission" in intents
        assert "generate_code" in intents
        assert len(intents) >= 10

    def test_dry_run_default(self):
        c = TaskClassifier()
        assert c.dry_run is True

    def test_classify_preserves_risk_level(self, classifier):
        tc = classifier.classify("send_communication", risk_level="high")
        assert tc.risk_level == "high"
