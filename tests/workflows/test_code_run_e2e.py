"""E2E tests — CodeRunWorkflow: goal → sandbox → output → akasha → run_id.

Cobertura:
  - dry_run plan (sem execução real)
  - full pipeline com CodeExecutorLego monkeypatched
  - propagação do run_id ponta a ponta
  - evento akasha com run_id, output_lines, tests_passed
  - recuperação do evento via query_events
  - modelo CodeRunResult (to_dict, properties)
  - tratamento de erros (lego falha, deploy bloqueado)
"""
from __future__ import annotations

import pytest

from src.interfaces.code_executor import CodeResult
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.code_run_workflow import (
    CodeRunWorkflow,
    CodeRunResult,
    _COST_LOCAL_PCT,
)


# ── helpers ───────────────────────────────────────────────────────────────────

_FAKE_OUTPUT = (
    "Analisando código Python...\n"
    "Módulos encontrados: 3\n"
    "Funções detectadas: 7\n"
    "Sem erros de sintaxe.\n"
    "Cobertura estimada: 85%\n"
)

_FAKE_OUTPUT_DRY = "[dry_run] Plano de execução: analisar módulo principal"


def _mock_lego_success(dry_run: bool = True):
    def _execute(spec):
        if dry_run or spec.dry_run:
            return CodeResult(
                success=True,
                output=_FAKE_OUTPUT_DRY,
                files_created=[],
                tests_passed=False,
                dry_run=True,
                artifacts={"plan": "dry_run_plan", "language": spec.language},
            )
        return CodeResult(
            success=True,
            output=_FAKE_OUTPUT,
            files_created=["output/code/analysis_report.md"],
            tests_passed=True,
            dry_run=False,
            artifacts={"lines_analyzed": 150, "language": spec.language},
        )
    return _execute


def _mock_lego_failure():
    def _execute(spec):
        return CodeResult(
            success=False, output="", files_created=[],
            tests_passed=False, dry_run=spec.dry_run,
            error="execution_error: syntax error in line 5",
        )
    return _execute


def _make_workflow(dry_run_mode: bool = True) -> tuple[CodeRunWorkflow, MockAkashaSink]:
    from src.legos.code_executor_lego import CodeExecutorLego
    lego = CodeExecutorLego()
    sink = MockAkashaSink()
    wf = CodeRunWorkflow(lego=lego, akasha_sink=sink)
    lego.execute = _mock_lego_success(dry_run=dry_run_mode)
    return wf, sink


# ── dry_run ───────────────────────────────────────────────────────────────────

def test_dry_run_succeeds():
    wf, _ = _make_workflow(dry_run_mode=True)
    result = wf.run("analisar módulo de pagamentos", dry_run=True)
    assert result.success is True
    assert result.dry_run is True


def test_dry_run_creates_run_id():
    wf, _ = _make_workflow()
    result = wf.run("analisar código", dry_run=True)
    assert result.run_id
    assert len(result.run_id) == 12


def test_dry_run_cost_local_pct_is_100():
    wf, _ = _make_workflow()
    result = wf.run("analisar código", dry_run=True)
    assert result.cost_local_pct == 100


def test_dry_run_no_files_created():
    wf, _ = _make_workflow()
    result = wf.run("analisar código", dry_run=True)
    assert result.files_created == []


def test_dry_run_writes_akasha_event():
    wf, sink = _make_workflow()
    wf.run("analisar código", dry_run=True)
    events = sink.query_events("code_run_completed")
    assert len(events) == 1


def test_dry_run_event_source_is_run_id():
    wf, sink = _make_workflow()
    result = wf.run("analisar código", dry_run=True)
    events = sink.query_events("code_run_completed")
    assert events[0].source == result.run_id


def test_dry_run_event_payload_has_run_id():
    wf, sink = _make_workflow()
    result = wf.run("analisar código", dry_run=True)
    events = sink.query_events("code_run_completed")
    assert events[0].payload["run_id"] == result.run_id


def test_dry_run_event_payload_has_goal():
    wf, sink = _make_workflow()
    wf.run("analisar módulo CRM", dry_run=True)
    events = sink.query_events("code_run_completed")
    assert events[0].payload["goal"] == "analisar módulo CRM"


def test_dry_run_akasha_event_id_nonempty():
    wf, _ = _make_workflow()
    result = wf.run("analisar código", dry_run=True)
    assert result.akasha_event_id.startswith("ske_")


# ── full pipeline ─────────────────────────────────────────────────────────────

def test_full_pipeline_succeeds():
    wf, _ = _make_workflow(dry_run_mode=False)
    result = wf.run("analisar módulo de pagamentos", dry_run=False)
    assert result.success is True
    assert result.dry_run is False


def test_full_pipeline_has_output():
    wf, _ = _make_workflow(dry_run_mode=False)
    result = wf.run("analisar código", dry_run=False)
    assert len(result.output) > 20


def test_full_pipeline_tests_passed():
    wf, _ = _make_workflow(dry_run_mode=False)
    result = wf.run("analisar código", dry_run=False)
    assert result.tests_passed is True


def test_full_pipeline_files_created():
    wf, _ = _make_workflow(dry_run_mode=False)
    result = wf.run("analisar código", dry_run=False)
    assert len(result.files_created) > 0


def test_full_pipeline_run_id_in_artifacts():
    wf, _ = _make_workflow(dry_run_mode=False)
    result = wf.run("analisar código", dry_run=False)
    assert result.artifacts["run_id"] == result.run_id


def test_full_pipeline_cost_local_pct_always_100():
    wf, sink = _make_workflow(dry_run_mode=False)
    wf.run("analisar código", dry_run=False)
    events = sink.query_events("code_run_completed")
    assert events[0].payload["cost_local_pct"] == 100


def test_full_pipeline_event_has_tests_passed():
    wf, sink = _make_workflow(dry_run_mode=False)
    wf.run("analisar código", dry_run=False)
    events = sink.query_events("code_run_completed")
    assert events[0].payload["tests_passed"] is True


# ── akasha recovery ───────────────────────────────────────────────────────────

def test_akasha_event_status_is_written():
    wf, sink = _make_workflow()
    wf.run("analisar código", dry_run=True)
    events = sink.query_events("code_run_completed")
    assert events[0].status == SinkStatus.WRITTEN


def test_multiple_runs_produce_separate_events():
    wf, sink = _make_workflow()
    r1 = wf.run("analisar módulo A", dry_run=True)
    r2 = wf.run("analisar módulo B", dry_run=True)
    assert r1.run_id != r2.run_id
    events = sink.query_events("code_run_completed")
    assert len(events) == 2


# ── CodeRunResult model ───────────────────────────────────────────────────────

def test_result_to_dict_has_run_id():
    wf, _ = _make_workflow()
    result = wf.run("analisar código", dry_run=True)
    assert result.to_dict()["run_id"] == result.run_id


def test_result_to_dict_has_cost_local_pct():
    wf, _ = _make_workflow()
    result = wf.run("analisar código", dry_run=True)
    assert result.to_dict()["cost_local_pct"] == _COST_LOCAL_PCT


def test_result_output_lines_property():
    r = CodeRunResult(run_id="abc", success=True, output="linha 1\nlinha 2\nlinha 3")
    assert r.output_lines == 3


def test_result_output_lines_empty():
    r = CodeRunResult(run_id="abc", success=True, output="")
    assert r.output_lines == 0


# ── error handling ────────────────────────────────────────────────────────────

def test_lego_failure_returns_error():
    from src.legos.code_executor_lego import CodeExecutorLego
    lego = CodeExecutorLego()
    lego.execute = _mock_lego_failure()
    sink = MockAkashaSink()
    wf = CodeRunWorkflow(lego=lego, akasha_sink=sink)
    result = wf.run("analisar código", dry_run=True)
    assert result.success is False
    assert result.error is not None


def test_lego_failure_has_run_id():
    from src.legos.code_executor_lego import CodeExecutorLego
    lego = CodeExecutorLego()
    lego.execute = _mock_lego_failure()
    sink = MockAkashaSink()
    wf = CodeRunWorkflow(lego=lego, akasha_sink=sink)
    result = wf.run("analisar código", dry_run=True)
    assert result.run_id
    assert len(result.run_id) == 12


def test_lego_failure_writes_no_akasha():
    from src.legos.code_executor_lego import CodeExecutorLego
    lego = CodeExecutorLego()
    lego.execute = _mock_lego_failure()
    sink = MockAkashaSink()
    wf = CodeRunWorkflow(lego=lego, akasha_sink=sink)
    wf.run("analisar código", dry_run=True)
    events = sink.query_events("code_run_completed")
    assert len(events) == 0
