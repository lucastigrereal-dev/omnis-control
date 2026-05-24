"""Testes do ResearchConductorLego — OMNIS STORM-adapted wide research."""
from __future__ import annotations

import asyncio
import json

import pytest

from src.interfaces.research_conductor import (
    ResearchSpec, ResearchResult, ResearchCitation, ResearchPerspective,
)
from src.legos.research_conductor_lego import (
    ResearchConductorLego,
    NullSearchBackend,
    SearXNGBackend,
    _StormPipeline,
    _LLMClient,
    _requires_publish_approval,
    _cost_local_pct,
)


# ── helpers ───────────────────────────────────────────────────────────────────

class _FakeLLM:
    """LLM que retorna respostas pré-definidas para cada estágio do pipeline."""

    def chat(self, messages: list[dict], max_tokens: int = 800) -> str:
        content = messages[0]["content"]
        if "Generate" in content and "perspectives" in content:
            return json.dumps([
                {"name": "Historical Context", "questions": ["How did it begin?", "What changed?"]},
                {"name": "Economic Impact", "questions": ["What is the cost?", "Who benefits?"]},
            ])
        if "Synthesize" in content or "Perspective:" in content:
            return "Key insight: this perspective reveals important patterns in the field."
        if "outline" in content.lower():
            return "## Introduction\n- Background\n## Analysis\n- Key points\n## Conclusion\n- Summary"
        if "Write a comprehensive" in content:
            return (
                "# Article\n\nIntroduction paragraph.\n\n"
                "## Analysis\n\nMain content with citation [1].\n\n"
                "## Conclusion\n\nFinal thoughts."
            )
        if "Polish" in content:
            return content.split("\n\n", 2)[-1] + "\n\n[Polished]"
        return "LLM response"


# ── _requires_publish_approval ────────────────────────────────────────────────

def test_publish_keyword_blocked():
    assert _requires_publish_approval("publicar relatório") is True

def test_share_keyword_blocked():
    assert _requires_publish_approval("share the research") is True

def test_safe_topic_not_blocked():
    assert _requires_publish_approval("tendências do mercado de IA") is False


# ── _cost_local_pct ───────────────────────────────────────────────────────────

def test_cost_local_pct_ollama(monkeypatch):
    monkeypatch.setattr("src.legos.research_conductor_lego.STORM_LLM_MODEL", "ollama/qwen2.5:7b")
    assert _cost_local_pct() == 100

def test_cost_local_pct_openai(monkeypatch):
    monkeypatch.setattr("src.legos.research_conductor_lego.STORM_LLM_MODEL", "gpt-4o")
    assert _cost_local_pct() == 0


# ── approval gate ─────────────────────────────────────────────────────────────

def test_publish_topic_blocked_real_run():
    lego = ResearchConductorLego(search_backend=NullSearchBackend(), llm_client=_FakeLLM())
    spec = ResearchSpec(topic="publicar relatório final", dry_run=False)
    result = lego.execute(spec)
    assert result.success is False
    assert result.error == "approval_required"
    assert result.artifacts.get("approval_required") is True


def test_publish_topic_not_blocked_dry_run():
    lego = ResearchConductorLego(search_backend=NullSearchBackend(), llm_client=_FakeLLM())
    spec = ResearchSpec(topic="publicar dados abertos", dry_run=True)
    result = lego.execute(spec)
    assert result.error != "approval_required"
    assert result.success is True


# ── health_check ──────────────────────────────────────────────────────────────

def test_health_check_returns_bool():
    assert isinstance(ResearchConductorLego().health_check(), bool)


def test_health_check_true_when_litellm_available():
    assert ResearchConductorLego().health_check() is True


def test_health_check_false_when_litellm_missing(monkeypatch):
    import builtins
    _real_import = builtins.__import__

    def _block_litellm(name, *args, **kwargs):
        if name == "litellm":
            raise ImportError("blocked")
        return _real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_litellm)
    lego = ResearchConductorLego()
    assert lego.health_check() is False


# ── dry_run plan ──────────────────────────────────────────────────────────────

def test_dry_run_returns_plan():
    lego = ResearchConductorLego()
    spec = ResearchSpec(topic="inteligência artificial", dry_run=True)
    result = lego.execute(spec)
    assert result.success is True
    assert result.dry_run is True
    assert "STORM" in result.report or "Plano" in result.report


def test_dry_run_no_citations():
    lego = ResearchConductorLego()
    result = lego.execute(ResearchSpec(topic="qualquer tópico", dry_run=True))
    assert result.citations == []


def test_dry_run_has_mock_perspectives():
    lego = ResearchConductorLego()
    spec = ResearchSpec(topic="clima", max_perspectives=3, dry_run=True)
    result = lego.execute(spec)
    assert len(result.perspectives) == 3


def test_dry_run_artifacts_has_mode():
    lego = ResearchConductorLego()
    result = lego.execute(ResearchSpec(topic="teste", dry_run=True))
    assert result.artifacts.get("mode") == "dry_run_plan"


def test_dry_run_artifacts_has_cost_local_pct():
    lego = ResearchConductorLego()
    result = lego.execute(ResearchSpec(topic="teste", dry_run=True))
    assert "cost_local_pct" in result.artifacts


# ── full pipeline (monkeypatched LLM + NullSearch) ───────────────────────────

def test_full_pipeline_produces_report():
    """Research real simples: tópico → relatório citado (LLM monkeypatched)."""
    lego = ResearchConductorLego(
        search_backend=NullSearchBackend(),
        llm_client=_FakeLLM(),
    )
    spec = ResearchSpec(
        topic="machine learning in healthcare",
        max_perspectives=2,
        max_search_queries_per_perspective=1,
        dry_run=False,
        output_dir="",
        store_in_akasha=False,
    )
    result = lego.execute(spec)
    assert result.success is True
    assert result.dry_run is False
    assert len(result.report) > 50
    assert result.topic == spec.topic


def test_full_pipeline_has_perspectives():
    lego = ResearchConductorLego(
        search_backend=NullSearchBackend(),
        llm_client=_FakeLLM(),
    )
    result = lego.execute(ResearchSpec(
        topic="sustainable energy",
        max_perspectives=2,
        dry_run=False, output_dir="", store_in_akasha=False,
    ))
    assert result.perspective_count >= 1


def test_full_pipeline_artifacts_cost_local():
    lego = ResearchConductorLego(
        search_backend=NullSearchBackend(),
        llm_client=_FakeLLM(),
    )
    result = lego.execute(ResearchSpec(
        topic="renewable energy",
        max_perspectives=2,
        dry_run=False, output_dir="", store_in_akasha=False,
    ))
    assert "cost_local_pct" in result.artifacts
    assert result.artifacts["search_backend"] == "null"


# ── pipeline persists files ───────────────────────────────────────────────────

def test_pipeline_creates_report_and_citations(tmp_path):
    lego = ResearchConductorLego(
        search_backend=NullSearchBackend(),
        llm_client=_FakeLLM(),
    )
    spec = ResearchSpec(
        topic="quantum computing",
        max_perspectives=2,
        dry_run=False,
        output_dir=str(tmp_path),
        store_in_akasha=False,
    )
    result = lego.execute(spec)
    assert result.success is True
    assert any(f.endswith("report.md") for f in result.files_created)
    assert any(f.endswith("citations.json") for f in result.files_created)


# ── execute unhappy paths ─────────────────────────────────────────────────────

def test_execute_returns_timeout_when_research_semaphore_busy(monkeypatch):
    import src.legos.research_conductor_lego as mod

    class _BusySemaphore:
        def acquire(self, timeout=5):
            return False

        def release(self):
            return None

    monkeypatch.setattr(mod, "_RESEARCH_SEMAPHORE", _BusySemaphore())
    lego = ResearchConductorLego(search_backend=NullSearchBackend(), llm_client=_FakeLLM())
    result = lego.execute(ResearchSpec(topic="mercado de viagens", dry_run=False))
    assert result.success is False
    assert result.error == "research_semaphore_timeout"


def test_execute_returns_error_when_pipeline_raises(monkeypatch):
    import src.legos.research_conductor_lego as mod

    class _GoodSemaphore:
        def acquire(self, timeout=5):
            return True

        def release(self):
            return None

    class _BrokenPipeline:
        def __init__(self, llm, search):
            pass

        def run(self, spec):
            raise RuntimeError("pipeline explode")

    monkeypatch.setattr(mod, "_RESEARCH_SEMAPHORE", _GoodSemaphore())
    monkeypatch.setattr(mod, "_StormPipeline", _BrokenPipeline)
    lego = ResearchConductorLego(search_backend=NullSearchBackend(), llm_client=_FakeLLM())
    result = lego.execute(ResearchSpec(topic="energia", dry_run=False))
    assert result.success is False
    assert "pipeline explode" in (result.error or "")


# ── search backends ───────────────────────────────────────────────────────────

def test_null_backend_returns_empty():
    backend = NullSearchBackend()
    assert backend.search("qualquer coisa") == []
    assert backend.name() == "null"


def test_searxng_backend_handles_connection_error():
    backend = SearXNGBackend("http://localhost:9999")
    results = backend.search("test query")
    assert results == []


def test_storm_pipeline_generates_perspectives_fallback():
    """Quando LLM retorna JSON inválido, pipeline usa fallback de perspectivas."""
    class _BadLLM:
        def chat(self, messages, max_tokens=800):
            raise ValueError("LLM offline")

    pipeline = _StormPipeline(llm=_BadLLM(), search=NullSearchBackend())
    perspectives = pipeline._generate_perspectives("some topic", n=2)
    assert len(perspectives) == 2


# ── async wrapper ─────────────────────────────────────────────────────────────

def test_execute_async_returns_result():
    lego = ResearchConductorLego(
        search_backend=NullSearchBackend(),
        llm_client=_FakeLLM(),
    )
    spec = ResearchSpec(topic="async test topic", dry_run=True)
    result = asyncio.get_event_loop().run_until_complete(lego.execute_async(spec))
    assert isinstance(result, ResearchResult)
    assert result.success is True


# ── ResearchResult properties ─────────────────────────────────────────────────

def test_result_citation_count():
    result = ResearchResult(
        success=True, topic="t", report="r",
        citations=[ResearchCitation(url="http://a.com", title="A"), ResearchCitation(url="http://b.com", title="B")],
    )
    assert result.citation_count == 2


def test_result_perspective_count():
    result = ResearchResult(
        success=True, topic="t", report="r",
        perspectives=[ResearchPerspective(name="P1"), ResearchPerspective(name="P2")],
    )
    assert result.perspective_count == 2


# ── Protocol compliance ───────────────────────────────────────────────────────

def test_lego_satisfies_research_conductor_protocol():
    from src.interfaces.research_conductor import ResearchConductor
    lego: ResearchConductor = ResearchConductorLego()
    assert hasattr(lego, "execute")
    assert hasattr(lego, "health_check")
