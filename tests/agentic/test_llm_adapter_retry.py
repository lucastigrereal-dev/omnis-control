"""Testes de retry + budget guard do LiteLLMAdapter (Onda 7)."""
from __future__ import annotations

import pytest

from src.agentic.llm_adapter import CaptionPromptInput, LiteLLMAdapter
from src.utils.run_context import BudgetExceededError, RunContext


def _prompt() -> CaptionPromptInput:
    return CaptionPromptInput(
        account_handle="@oinatalrn",
        objective="alcance",
        format="feed",
        context_md="ctx",
    )


# ── RunContext propagation ────────────────────────────────────────────────────

def test_litellm_accepts_run_context():
    ctx = RunContext.new(budget_usd=1.0)
    adapter = LiteLLMAdapter(run_context=ctx)
    assert adapter._ctx is ctx


def test_litellm_default_no_context():
    adapter = LiteLLMAdapter()
    assert adapter._ctx is None


# ── budget guard ──────────────────────────────────────────────────────────────

def test_budget_exceeded_before_call(monkeypatch):
    import src.agentic.llm_adapter as mod
    monkeypatch.setattr(mod, "_COST_PER_1K_TOKENS", 1.0)

    ctx = RunContext(budget_usd=0.001)
    ctx.add_cost(0.001)  # already at limit

    adapter = LiteLLMAdapter(run_context=ctx)
    with pytest.raises(BudgetExceededError):
        adapter.generate_caption(_prompt())


def test_budget_zero_never_raises_before_call(monkeypatch):
    import src.agentic.llm_adapter as mod
    monkeypatch.setattr(mod, "_COST_PER_1K_TOKENS", 1.0)

    ctx = RunContext(budget_usd=0)  # unlimited
    adapter = LiteLLMAdapter(run_context=ctx)

    call_count = []

    def _fake_call(self, prompt):
        call_count.append(1)
        from src.agentic.llm_adapter import CaptionLLMOutput
        return CaptionLLMOutput("h", "b", "c", [], "h\n\nb\n\nc", "mock", 100)

    monkeypatch.setattr(LiteLLMAdapter, "_call_with_retry", _fake_call)
    adapter.generate_caption(_prompt())
    assert call_count == [1]


def test_cost_accumulated_after_call(monkeypatch):
    import src.agentic.llm_adapter as mod
    monkeypatch.setattr(mod, "_COST_PER_1K_TOKENS", 1.0)

    ctx = RunContext(budget_usd=10.0)
    adapter = LiteLLMAdapter(run_context=ctx)

    from src.agentic.llm_adapter import CaptionLLMOutput

    def _fake_call(self, prompt):
        return CaptionLLMOutput("h", "b", "c", [], "raw", "mock", tokens_used=500)

    monkeypatch.setattr(LiteLLMAdapter, "_call_with_retry", _fake_call)
    adapter.generate_caption(_prompt())

    assert abs(ctx.cost_accumulated - 0.5) < 1e-9


def test_no_cost_tracking_when_rate_zero(monkeypatch):
    import src.agentic.llm_adapter as mod
    monkeypatch.setattr(mod, "_COST_PER_1K_TOKENS", 0.0)

    ctx = RunContext(budget_usd=10.0)
    adapter = LiteLLMAdapter(run_context=ctx)

    from src.agentic.llm_adapter import CaptionLLMOutput

    def _fake_call(self, prompt):
        return CaptionLLMOutput("h", "b", "c", [], "raw", "mock", tokens_used=9999)

    monkeypatch.setattr(LiteLLMAdapter, "_call_with_retry", _fake_call)
    adapter.generate_caption(_prompt())
    assert ctx.cost_accumulated == 0.0


# ── retry logic ───────────────────────────────────────────────────────────────

def test_retry_on_oserror_succeeds_on_second_attempt(monkeypatch):
    """Testa retry real: urlopen falha 1x, sucede na 2ª tentativa."""
    import json
    import io
    import urllib.request

    attempts = []
    good_response = json.dumps({
        "choices": [{"message": {"content": json.dumps({"hook": "h", "body": "b", "cta": "c", "hashtags": []})}}],
        "usage": {"total_tokens": 10},
    }).encode()

    class _FakeResp:
        def read(self): return good_response
        def __enter__(self): return self
        def __exit__(self, *_): pass

    def _flaky_urlopen(req, timeout=None):
        attempts.append(1)
        if len(attempts) < 2:
            raise OSError("network blip")
        return _FakeResp()

    monkeypatch.setattr(urllib.request, "urlopen", _flaky_urlopen)
    adapter = LiteLLMAdapter()
    result = adapter._call_with_retry(_prompt())
    assert len(attempts) == 2
    assert result.hook == "h"


def test_retry_exhausted_raises_oserror(monkeypatch):
    """Após 3 tentativas, OSError propaga para o caller."""
    import urllib.request

    attempts = []

    def _always_fail(req, timeout=None):
        attempts.append(1)
        raise OSError("always down")

    monkeypatch.setattr(urllib.request, "urlopen", _always_fail)
    adapter = LiteLLMAdapter()
    with pytest.raises(OSError):
        adapter._call_with_retry(_prompt())
    assert len(attempts) == 3


def test_no_context_no_budget_check(monkeypatch):
    from src.agentic.llm_adapter import CaptionLLMOutput

    def _ok(self, prompt):
        return CaptionLLMOutput("h", "b", "c", [], "raw", "mock", 100)

    monkeypatch.setattr(LiteLLMAdapter, "_call_with_retry", _ok)
    adapter = LiteLLMAdapter(run_context=None)
    result = adapter.generate_caption(_prompt())
    assert result.hook == "h"
