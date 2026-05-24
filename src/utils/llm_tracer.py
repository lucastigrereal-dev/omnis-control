"""llm_tracer — rastreamento OpenTelemetry por chamada LLM.

Instrumenta cada chamada ao LiteLLM com um span que carrega:
  - model        — modelo usado
  - tokens       — total de tokens consumidos
  - latency_ms   — latência em ms
  - cost_usd     — custo estimado em USD

Exporters configuráveis via env:
  OMNIS_OTEL_EXPORTER  — "console" (default) | "none"
  OMNIS_OTEL_OTLP_URL  — endpoint OTLP (opcional; ativa exporter OTLP)

Uso interno:
    tracer = get_llm_tracer()
    with tracer.start_as_current_span("llm.generate_caption") as span:
        # ... chamada HTTP ...
        set_llm_span_attrs(span, model="...", tokens=100, latency_ms=350, cost_usd=0.001)
"""
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Generator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_TRACER_NAME = "omnis.llm"

# ── provider singleton ────────────────────────────────────────────────────────

_provider: TracerProvider | None = None
_in_memory_exporter: InMemorySpanExporter | None = None


def _build_provider() -> TracerProvider:
    """Constrói TracerProvider lendo env vars em runtime (não em import time)."""
    global _in_memory_exporter
    exporter_type = os.getenv("OMNIS_OTEL_EXPORTER", "console")
    otlp_url = os.getenv("OMNIS_OTEL_OTLP_URL", "")

    provider = TracerProvider()

    if otlp_url:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            provider.add_span_processor(
                SimpleSpanProcessor(OTLPSpanExporter(endpoint=otlp_url))
            )
        except ImportError:
            pass  # OTLP exporter não instalado — ignora silenciosamente

    if exporter_type == "console":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    elif exporter_type == "memory":
        _in_memory_exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(_in_memory_exporter))
    # "none" → sem exporter (útil em testes de integração sem ruído)

    return provider


def get_llm_tracer() -> trace.Tracer:
    """Retorna o tracer OMNIS LLM (inicializa provider na primeira chamada).

    Usa o provider do módulo diretamente — não altera o provider global do
    OpenTelemetry, o que permite reset em testes sem conflito.
    """
    global _provider
    if _provider is None:
        _provider = _build_provider()
    return _provider.get_tracer(_TRACER_NAME)


def get_in_memory_exporter() -> InMemorySpanExporter | None:
    """Retorna o exporter em memória se OMNIS_OTEL_EXPORTER=memory (uso em testes)."""
    return _in_memory_exporter


def reset_tracer() -> None:
    """Reseta o provider — usado em testes para isolar estado."""
    global _provider, _in_memory_exporter
    _provider = None
    _in_memory_exporter = None


def set_llm_span_attrs(
    span: trace.Span,
    *,
    model: str,
    tokens: int,
    latency_ms: float,
    cost_usd: float,
    run_id: str = "",
) -> None:
    """Define os 4 atributos padrão + run_id opcional em um span LLM."""
    span.set_attribute("llm.model", model)
    span.set_attribute("llm.tokens", tokens)
    span.set_attribute("llm.latency_ms", round(latency_ms, 2))
    span.set_attribute("llm.cost_usd", round(cost_usd, 6))
    if run_id:
        span.set_attribute("omnis.run_id", run_id)


@contextmanager
def llm_span(
    operation: str,
    model: str,
    run_id: str = "",
) -> Generator[tuple[trace.Span, float], None, None]:
    """Context manager que cria span + mede latência automaticamente.

    Uso:
        with llm_span("llm.generate_caption", model=self.model, run_id=...) as (span, t0):
            result = _http_call(...)
            set_llm_span_attrs(span, model=model, tokens=result.tokens_used,
                               latency_ms=(time.time()-t0)*1000, cost_usd=...)
    """
    tracer = get_llm_tracer()
    t0 = time.time()
    with tracer.start_as_current_span(operation) as span:
        span.set_attribute("llm.model", model)
        if run_id:
            span.set_attribute("omnis.run_id", run_id)
        yield span, t0
