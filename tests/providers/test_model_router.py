"""Tests for ModelRouterProvider — MockModelProvider + Claude/OpenRouter fallback."""
import pytest
from src.providers.model_router import MockModelProvider, ClaudeProvider, OpenRouterProvider, ModelRequest, ModelResponse
from src.providers.base import ProviderStatus


class TestMockModelProvider:
    def test_health_ok(self):
        assert MockModelProvider().health_check().ok

    def test_complete_returns_response(self):
        p = MockModelProvider(response="hello world")
        r = p.complete(ModelRequest(prompt="test"))
        assert isinstance(r, ModelResponse)
        assert r.content == "hello world"

    def test_ask_returns_string(self):
        p = MockModelProvider(response="42")
        assert p.ask("question") == "42"

    def test_to_dict(self):
        p = MockModelProvider()
        r = p.complete(ModelRequest(prompt="test"))
        d = r.to_dict()
        assert "content" in d
        assert "model" in d

    def test_backend(self):
        assert MockModelProvider().backend == "mock"

    def test_name(self):
        assert MockModelProvider().name == "model"

    def test_token_count(self):
        p = MockModelProvider(response="one two three")
        r = p.complete(ModelRequest(prompt="hello world"))
        assert r.input_tokens == 2
        assert r.output_tokens == 3


class TestClaudeProviderFallback:
    def test_health_degraded_without_key(self):
        p = ClaudeProvider(api_key="", fallback=MockModelProvider())
        h = p.health_check()
        assert h.status == ProviderStatus.DEGRADED

    def test_complete_falls_back_to_mock(self):
        p = ClaudeProvider(api_key="", fallback=MockModelProvider(response="fallback"))
        r = p.complete(ModelRequest(prompt="test"))
        assert r.content == "fallback"
        assert r.provider == "mock"

    def test_backend_indicates_unavailable(self):
        p = ClaudeProvider(api_key="")
        assert "unavailable" in p.backend or p.backend.startswith("claude")

    def test_name(self):
        assert ClaudeProvider(api_key="").name == "model"


class TestOpenRouterProviderFallback:
    def test_health_degraded_without_key(self):
        p = OpenRouterProvider(api_key="", fallback=MockModelProvider())
        assert p.health_check().status == ProviderStatus.DEGRADED

    def test_complete_falls_back(self):
        p = OpenRouterProvider(api_key="", fallback=MockModelProvider(response="or_fallback"))
        r = p.complete(ModelRequest(prompt="test"))
        assert r.content == "or_fallback"

    def test_name(self):
        assert OpenRouterProvider(api_key="").name == "model"
