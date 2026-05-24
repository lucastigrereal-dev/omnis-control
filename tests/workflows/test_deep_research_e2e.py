"""E2E tests — DeepResearchWorkflow: tópico → STORM → akasha → run_id.

Cobertura:
  - dry_run plan (sem LLM real)
  - full pipeline com _FakeLLM + NullSearch
  - propagação do run_id ponta a ponta
  - evento akasha com run_id, tópico, custo
  - recuperação do evento via query_events
  - modelo DeepResearchResult (to_dict, properties)
  - tratamento de erro na pesquisa
"""
from __future__ import annotations

import json

import pytest

from src.legos.research_conductor_lego import NullSearchBackend
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.deep_research_workflow import DeepResearchWorkflow, DeepResearchResult


# ── _FakeLLM idêntico ao usado nos testes do lego ────────────────────────────

class _FakeLLM:
    def chat(self, messages: list[dict], max_tokens: int = 800) -> str:
        content = messages[0]["content"]
        if "Generate" in content and "perspectives" in content:
            return json.dumps([
                {"name": "Histórico", "questions": ["Como surgiu?", "O que mudou?"]},
                {"name": "Impacto Econômico", "questions": ["Qual o custo?", "Quem se beneficia?"]},
            ])
        if "Synthesize" in content or "Perspective:" in content:
            return "Insight chave: padrões importantes emergem desta perspectiva."
        if "outline" in content.lower():
            return "## Introdução\n- Contexto\n## Análise\n- Pontos-chave\n## Conclusão\n- Resumo"
        if "Write a comprehensive" in content:
            return (
                "# Artigo\n\nParágrafo introdutório.\n\n"
                "## Análise\n\nConteúdo principal com citação [1].\n\n"
                "## Conclusão\n\nConsiderações finais."
            )
        if "Polish" in content:
            return content.split("\n\n", 2)[-1] + "\n\n[Polido]"
        return "Resposta LLM"


def _make_workflow(dry_run_sink: bool = True) -> tuple[DeepResearchWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    wf = DeepResearchWorkflow(
        research_lego=__import__(
            "src.legos.research_conductor_lego", fromlist=["ResearchConductorLego"]
        ).ResearchConductorLego(
            search_backend=NullSearchBackend(),
            llm_client=_FakeLLM(),
        ),
        akasha_sink=sink,
    )
    return wf, sink


# ── dry_run ───────────────────────────────────────────────────────────────────

def test_dry_run_succeeds():
    wf, _ = _make_workflow()
    result = wf.run("inteligência artificial em saúde", dry_run=True)
    assert result.success is True
    assert result.dry_run is True


def test_dry_run_creates_run_id():
    wf, _ = _make_workflow()
    result = wf.run("turismo sustentável", dry_run=True)
    assert result.run_id
    assert len(result.run_id) == 12


def test_dry_run_report_contains_plan():
    wf, _ = _make_workflow()
    result = wf.run("mercado de energia renovável", dry_run=True)
    assert "STORM" in result.report or "Plano" in result.report or "dry_run" in result.report


def test_dry_run_no_citations():
    wf, _ = _make_workflow()
    result = wf.run("qualquer tópico", dry_run=True)
    assert result.citation_count == 0
    assert result.citations == []


def test_dry_run_writes_event_to_akasha():
    wf, sink = _make_workflow()
    result = wf.run("blockchain nas finanças", dry_run=True)
    assert result.success is True
    events = sink.query_events("deep_research_completed")
    assert len(events) == 1


def test_dry_run_event_source_is_run_id():
    wf, sink = _make_workflow()
    result = wf.run("cidades inteligentes", dry_run=True)
    events = sink.query_events("deep_research_completed")
    assert events[0].source == result.run_id


def test_dry_run_event_payload_has_topic():
    wf, sink = _make_workflow()
    result = wf.run("impacto da automação no trabalho", dry_run=True)
    events = sink.query_events("deep_research_completed")
    assert events[0].payload["topic"] == "impacto da automação no trabalho"


def test_dry_run_event_payload_has_run_id():
    wf, sink = _make_workflow()
    result = wf.run("saúde digital", dry_run=True)
    events = sink.query_events("deep_research_completed")
    assert events[0].payload["run_id"] == result.run_id


def test_dry_run_akasha_event_id_nonempty():
    wf, _ = _make_workflow()
    result = wf.run("educação online", dry_run=True)
    assert result.akasha_event_id
    assert result.akasha_event_id.startswith("ske_")


def test_dry_run_cost_local_pct_present():
    wf, _ = _make_workflow()
    result = wf.run("inteligência artificial", dry_run=True)
    assert isinstance(result.cost_local_pct, int)
    assert 0 <= result.cost_local_pct <= 100


# ── full pipeline (FakeLLM + NullSearch) ─────────────────────────────────────

def test_full_pipeline_succeeds():
    """E2E principal: tópico entra, relatório citado sai, guardado no akasha."""
    wf, sink = _make_workflow()
    result = wf.run("machine learning em saúde", max_perspectives=2, dry_run=False)
    assert result.success is True
    assert result.dry_run is False
    assert len(result.report) > 50


def test_full_pipeline_run_id_propagates_to_artifacts():
    wf, _ = _make_workflow()
    result = wf.run("energia solar", max_perspectives=2, dry_run=False)
    assert result.artifacts.get("run_id") == result.run_id


def test_full_pipeline_akasha_event_id_in_artifacts():
    wf, _ = _make_workflow()
    result = wf.run("computação quântica", max_perspectives=2, dry_run=False)
    assert result.artifacts.get("akasha_event_id") == result.akasha_event_id


def test_full_pipeline_has_perspectives():
    wf, _ = _make_workflow()
    result = wf.run("impacto das redes sociais", max_perspectives=2, dry_run=False)
    assert result.perspective_count >= 1


def test_full_pipeline_event_written_to_akasha():
    wf, sink = _make_workflow()
    result = wf.run("futuro do trabalho remoto", max_perspectives=2, dry_run=False)
    assert result.success is True
    events = sink.query_events("deep_research_completed")
    assert len(events) == 1
    assert events[0].payload["run_id"] == result.run_id


def test_full_pipeline_event_has_report_content():
    wf, sink = _make_workflow()
    result = wf.run("microbioma humano", max_perspectives=2, dry_run=False)
    events = sink.query_events("deep_research_completed")
    payload = events[0].payload
    assert len(payload["report"]) > 50
    assert payload["topic"] == "microbioma humano"


def test_full_pipeline_cost_local_pct_in_event():
    wf, sink = _make_workflow()
    wf.run("fintech e inclusão financeira", max_perspectives=2, dry_run=False)
    events = sink.query_events("deep_research_completed")
    assert "cost_local_pct" in events[0].payload


def test_full_pipeline_search_backend_null_in_event():
    wf, sink = _make_workflow()
    wf.run("nanotecnologia", max_perspectives=2, dry_run=False)
    events = sink.query_events("deep_research_completed")
    assert events[0].payload["search_backend"] == "null"


# ── akasha recovery ───────────────────────────────────────────────────────────

def test_akasha_query_recovers_event_by_type():
    wf, sink = _make_workflow()
    result = wf.run("turismo pós-pandemia", dry_run=True)
    recovered = sink.query_events("deep_research_completed")
    assert len(recovered) == 1
    assert recovered[0].payload["run_id"] == result.run_id


def test_akasha_event_status_is_written():
    wf, sink = _make_workflow()
    wf.run("biodiversidade amazônica", dry_run=True)
    events = sink.query_events("deep_research_completed")
    assert events[0].status == SinkStatus.WRITTEN


def test_multiple_runs_produce_separate_events():
    wf, sink = _make_workflow()
    r1 = wf.run("tópico A", dry_run=True)
    r2 = wf.run("tópico B", dry_run=True)
    assert r1.run_id != r2.run_id
    events = sink.query_events("deep_research_completed")
    assert len(events) == 2
    run_ids = {e.payload["run_id"] for e in events}
    assert r1.run_id in run_ids
    assert r2.run_id in run_ids


# ── DeepResearchResult model ──────────────────────────────────────────────────

def test_result_to_dict_has_run_id():
    wf, _ = _make_workflow()
    result = wf.run("inteligência artificial", dry_run=True)
    d = result.to_dict()
    assert d["run_id"] == result.run_id


def test_result_to_dict_has_success():
    wf, _ = _make_workflow()
    result = wf.run("qualquer tópico", dry_run=True)
    d = result.to_dict()
    assert d["success"] is True


def test_result_to_dict_has_citation_count():
    wf, _ = _make_workflow()
    result = wf.run("qualquer tópico", dry_run=True)
    d = result.to_dict()
    assert "citation_count" in d
    assert isinstance(d["citation_count"], int)


def test_result_to_dict_has_perspective_count():
    wf, _ = _make_workflow()
    result = wf.run("clima e sustentabilidade", max_perspectives=2, dry_run=True)
    d = result.to_dict()
    assert "perspective_count" in d
    assert d["perspective_count"] >= 0


def test_result_to_dict_has_akasha_event_id():
    wf, _ = _make_workflow()
    result = wf.run("saúde mental", dry_run=True)
    d = result.to_dict()
    assert d["akasha_event_id"] == result.akasha_event_id


def test_result_to_dict_has_cost_local_pct():
    wf, _ = _make_workflow()
    result = wf.run("inovação", dry_run=True)
    d = result.to_dict()
    assert "cost_local_pct" in d


def test_result_citation_count_property():
    from src.interfaces.research_conductor import ResearchCitation
    r = DeepResearchResult(
        run_id="abc", success=True,
        citations=[ResearchCitation(url="http://a.com", title="A"), ResearchCitation(url="http://b.com", title="B")],
    )
    assert r.citation_count == 2


def test_result_perspective_count_property():
    from src.interfaces.research_conductor import ResearchPerspective
    r = DeepResearchResult(
        run_id="abc", success=True,
        perspectives=[ResearchPerspective(name="P1"), ResearchPerspective(name="P2")],
    )
    assert r.perspective_count == 2


# ── error handling ────────────────────────────────────────────────────────────

def test_approval_required_topic_returns_error():
    wf, sink = _make_workflow()
    result = wf.run("publicar relatório final", dry_run=False)
    assert result.success is False
    assert result.error == "approval_required"


def test_error_result_has_run_id():
    wf, _ = _make_workflow()
    result = wf.run("publicar relatório final", dry_run=False)
    assert result.run_id
    assert len(result.run_id) == 12


def test_error_result_writes_no_akasha_event():
    wf, sink = _make_workflow()
    wf.run("publicar relatório final", dry_run=False)
    events = sink.query_events("deep_research_completed")
    assert len(events) == 0
