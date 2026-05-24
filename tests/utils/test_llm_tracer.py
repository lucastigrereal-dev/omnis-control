"""Testes do llm_tracer — spans OpenTelemetry por chamada LLM."""
from __future__ import annotations

import json
import time

import pytest

from src.utils.llm_tracer import (
    get_llm_tracer,
    get_in_memory_exporter,
    llm_span,
    reset_tracer,
    set_llm_span_attrs,
)


@pytest.fixture(autouse=True)
def _isolate_tracer(monkeypatch):
    """Cada teste usa um provider em memória isolado."""
    monkeypatch.setenv("OMNIS_OTEL_EXPORTER", "memory")
    reset_tracer()
    yield
    reset_tracer()


def _finished_spans():
    exp = get_in_memory_exporter()
    return exp.get_finished_spans() if exp else []


# ── set_llm_span_attrs ────────────────────────────────────────────────────────

def test_set_llm_span_attrs_all_4():
    tracer = get_llm_tracer()
    with tracer.start_as_current_span("test.span") as span:
        set_llm_span_attrs(span, model="ollama/qwen2.5", tokens=500, latency_ms=350.5, cost_usd=0.00025)

    spans = _finished_spans()
    assert len(spans) == 1
    attrs = spans[0].attributes
    assert attrs["llm.model"] == "ollama/qwen2.5"
    assert attrs["llm.tokens"] == 500
    assert attrs["llm.latency_ms"] == 350.5
    assert attrs["llm.cost_usd"] == 0.00025


def test_set_llm_span_attrs_with_run_id():
    tracer = get_llm_tracer()
    with tracer.start_as_current_span("test.span") as span:
        set_llm_span_attrs(span, model="m", tokens=1, latency_ms=1.0, cost_usd=0.0, run_id="abc123")

    attrs = _finished_spans()[0].attributes
    assert attrs["omnis.run_id"] == "abc123"


def test_set_llm_span_attrs_no_run_id_omits_key():
    tracer = get_llm_tracer()
    with tracer.start_as_current_span("test.span") as span:
        set_llm_span_attrs(span, model="m", tokens=1, latency_ms=1.0, cost_usd=0.0)

    attrs = _finished_spans()[0].attributes
    assert "omnis.run_id" not in attrs


# ── llm_span context manager ──────────────────────────────────────────────────

def test_llm_span_creates_span_with_model():
    with llm_span("llm.generate_caption", model="ollama/qwen2.5") as (span, t0):
        pass

    spans = _finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "llm.generate_caption"
    assert spans[0].attributes["llm.model"] == "ollama/qwen2.5"


def test_llm_span_t0_is_float():
    with llm_span("llm.test", model="m") as (span, t0):
        elapsed = time.time() - t0
    assert elapsed >= 0.0
    assert isinstance(t0, float)


def test_llm_span_with_run_id():
    with llm_span("llm.test", model="m", run_id="run999") as (span, _):
        pass

    attrs = _finished_spans()[0].attributes
    assert attrs["omnis.run_id"] == "run999"


def test_llm_span_exception_still_finishes_span():
    with pytest.raises(ValueError):
        with llm_span("llm.test", model="m") as (span, _):
            raise ValueError("boom")

    spans = _finished_spans()
    assert len(spans) == 1  # span registrado mesmo com exceção


# ── integração com LiteLLMAdapter ─────────────────────────────────────────────

def test_llm_call_generates_span_with_4_attrs(monkeypatch):
    """Smoke test: chamada fake ao adapter gera span com model/tokens/latency/cost."""
    import src.agentic.llm_adapter as mod
    monkeypatch.setattr(mod, "_COST_PER_1K_TOKENS", 1.0)

    from src.agentic.llm_adapter import CaptionLLMOutput, CaptionPromptInput, LiteLLMAdapter
    from src.utils.run_context import RunContext

    ctx = RunContext(run_id="trace_test")
    adapter = LiteLLMAdapter(run_context=ctx)

    def _fake_urlopen(req, timeout=None):
        class _Resp:
            def read(self):
                return json.dumps({
                    "choices": [{"message": {"content": json.dumps(
                        {"hook": "h", "body": "b", "cta": "c", "hashtags": []}
                    )}}],
                    "usage": {"total_tokens": 200},
                }).encode()
            def __enter__(self): return self
            def __exit__(self, *_): pass
        return _Resp()

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    prompt = CaptionPromptInput(
        account_handle="@test",
        objective="alcance",
        format="feed",
        context_md="ctx",
    )
    result = adapter._call_with_retry(prompt)

    spans = _finished_spans()
    assert len(spans) >= 1
    span = spans[0]
    attrs = span.attributes

    assert attrs["llm.model"] == adapter.model
    assert attrs["llm.tokens"] == 200
    assert attrs["llm.latency_ms"] >= 0
    assert attrs["llm.cost_usd"] == pytest.approx(0.2, rel=1e-3)
    assert attrs["omnis.run_id"] == "trace_test"
