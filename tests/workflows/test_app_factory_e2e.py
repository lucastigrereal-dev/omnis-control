"""E2E tests — AppFactoryWorkflow: ideia → plano → artefato → akasha → run_id.

Cobertura:
  - dry_run plan (sem escrita em disco)
  - propagação do run_id ponta a ponta
  - evento akasha com run_id, artifact_id, prd_chars
  - approval gate (blocked se approved=False e dry_run=False)
  - pipeline completo (dry_run=False, approved=True, escrita em disco)
  - recuperação do evento via query_events
  - modelo AppFactoryResult (to_dict, properties)
  - tratamento de erros (planner falha, approval gate)
  - cost_local_pct sempre 100
"""
from __future__ import annotations

import pytest

from src.app_factory.models import AppArtifact, AppIdea
from src.app_factory.planner import AppFactoryPlanner
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.app_factory_workflow import (
    AppFactoryWorkflow,
    AppFactoryResult,
    _COST_LOCAL_PCT,
)


# ── helpers ───────────────────────────────────────────────────────────────────

_IDEA_TEXT = "Sistema de gerenciamento de hotéis com reservas, perfis e relatórios financeiros"

_FAKE_PRD = (
    "# PRD — Sistema Hotel\n\n"
    "## Visão\nGerenciar reservas, perfis de hóspedes e relatórios financeiros.\n\n"
    "## Módulos\n- Reservas\n- Hóspedes\n- Relatórios\n"
)


def _fake_artifact(blueprint_id: str = "bp_test0001") -> AppArtifact:
    return AppArtifact(
        artifact_id="art_test0001",
        blueprint_id=blueprint_id,
        prd_markdown=_FAKE_PRD,
        project_structure={"modules": ["reservas", "hospedes", "relatorios"], "type": "web"},
        tech_stack_summary={"backend": "FastAPI", "frontend": "React", "db": "PostgreSQL"},
        generated_at="2026-05-24T00:00:00+00:00",
    )


def _make_workflow(planner_ok: bool = True, fail_msg: str = "planner_error") -> tuple[AppFactoryWorkflow, MockAkashaSink]:
    planner = AppFactoryPlanner()
    sink = MockAkashaSink()
    wf = AppFactoryWorkflow(planner=planner, akasha_sink=sink)
    if planner_ok:
        planner.plan = lambda idea, dry_run=True: _fake_artifact()
    else:
        def _fail(idea, dry_run=True):
            raise RuntimeError(fail_msg)
        planner.plan = _fail
    return wf, sink


# ── dry_run ───────────────────────────────────────────────────────────────────

def test_dry_run_succeeds():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert result.success is True
    assert result.dry_run is True


def test_dry_run_creates_run_id():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert result.run_id
    assert len(result.run_id) == 12


def test_dry_run_cost_local_pct_is_100():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert result.cost_local_pct == 100


def test_dry_run_has_artifact_id():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert result.artifact_id == "art_test0001"


def test_dry_run_has_prd_markdown():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert len(result.prd_markdown) > 20


def test_dry_run_no_files_written():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert result.files_written == []


def test_dry_run_writes_akasha_event():
    wf, sink = _make_workflow()
    wf.run(_IDEA_TEXT, dry_run=True)
    events = sink.query_events("app_factory_completed")
    assert len(events) == 1


def test_dry_run_akasha_event_source_is_run_id():
    wf, sink = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    events = sink.query_events("app_factory_completed")
    assert events[0].source == result.run_id


def test_dry_run_event_payload_has_run_id():
    wf, sink = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    events = sink.query_events("app_factory_completed")
    assert events[0].payload["run_id"] == result.run_id


def test_dry_run_event_payload_has_artifact_id():
    wf, sink = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    events = sink.query_events("app_factory_completed")
    assert events[0].payload["artifact_id"] == result.artifact_id


def test_dry_run_event_payload_has_cost_local_pct():
    wf, sink = _make_workflow()
    wf.run(_IDEA_TEXT, dry_run=True)
    events = sink.query_events("app_factory_completed")
    assert events[0].payload["cost_local_pct"] == 100


def test_dry_run_akasha_event_id_nonempty():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert result.akasha_event_id
    assert result.akasha_event_id.startswith("ske_")


def test_dry_run_approved_flag_false():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert result.approved is False


# ── approval gate ─────────────────────────────────────────────────────────────

def test_approval_gate_blocks_when_not_approved():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=False, approved=False)
    assert result.success is False
    assert result.error == "approval_required"


def test_approval_gate_blocked_has_run_id():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=False, approved=False)
    assert result.run_id
    assert len(result.run_id) == 12


def test_approval_gate_blocked_has_artifact_id():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=False, approved=False)
    assert result.artifact_id == "art_test0001"


def test_approval_gate_blocked_has_plan_summary():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=False, approved=False)
    assert "plan_summary" in result.artifacts
    assert result.artifacts["approval_required"] is True


def test_approval_gate_blocked_writes_no_akasha():
    wf, sink = _make_workflow()
    wf.run(_IDEA_TEXT, dry_run=False, approved=False)
    events = sink.query_events("app_factory_completed")
    assert len(events) == 0


# ── full pipeline (dry_run=False, approved=True) ──────────────────────────────

def test_full_pipeline_succeeds(tmp_path):
    planner = AppFactoryPlanner()
    planner.plan = lambda idea, dry_run=True: _fake_artifact()
    sink = MockAkashaSink()
    wf = AppFactoryWorkflow(planner=planner, akasha_sink=sink, output_dir=str(tmp_path / "af"))
    result = wf.run(_IDEA_TEXT, dry_run=False, approved=True)
    assert result.success is True
    assert result.dry_run is False
    assert result.approved is True


def test_full_pipeline_files_written(tmp_path):
    planner = AppFactoryPlanner()
    planner.plan = lambda idea, dry_run=True: _fake_artifact()
    sink = MockAkashaSink()
    wf = AppFactoryWorkflow(planner=planner, akasha_sink=sink, output_dir=str(tmp_path / "af"))
    result = wf.run(_IDEA_TEXT, dry_run=False, approved=True)
    assert len(result.files_written) == 4
    for f in result.files_written:
        from pathlib import Path
        assert Path(f).exists()


def test_full_pipeline_prd_file_content(tmp_path):
    planner = AppFactoryPlanner()
    planner.plan = lambda idea, dry_run=True: _fake_artifact()
    sink = MockAkashaSink()
    wf = AppFactoryWorkflow(planner=planner, akasha_sink=sink, output_dir=str(tmp_path / "af"))
    result = wf.run(_IDEA_TEXT, dry_run=False, approved=True)
    prd_path = next(f for f in result.files_written if f.endswith("prd.md"))
    from pathlib import Path
    assert "Hotel" in Path(prd_path).read_text()


def test_full_pipeline_event_has_files_written(tmp_path):
    planner = AppFactoryPlanner()
    planner.plan = lambda idea, dry_run=True: _fake_artifact()
    sink = MockAkashaSink()
    wf = AppFactoryWorkflow(planner=planner, akasha_sink=sink, output_dir=str(tmp_path / "af"))
    result = wf.run(_IDEA_TEXT, dry_run=False, approved=True)
    events = sink.query_events("app_factory_completed")
    assert len(events[0].payload["files_written"]) == 4


def test_full_pipeline_run_id_in_artifacts(tmp_path):
    planner = AppFactoryPlanner()
    planner.plan = lambda idea, dry_run=True: _fake_artifact()
    sink = MockAkashaSink()
    wf = AppFactoryWorkflow(planner=planner, akasha_sink=sink, output_dir=str(tmp_path / "af"))
    result = wf.run(_IDEA_TEXT, dry_run=False, approved=True)
    assert result.artifacts["run_id"] == result.run_id


# ── akasha recovery ───────────────────────────────────────────────────────────

def test_akasha_query_recovers_event_by_type():
    wf, sink = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    recovered = sink.query_events("app_factory_completed")
    assert len(recovered) == 1
    assert recovered[0].payload["run_id"] == result.run_id


def test_akasha_event_status_is_written():
    wf, sink = _make_workflow()
    wf.run(_IDEA_TEXT, dry_run=True)
    events = sink.query_events("app_factory_completed")
    assert events[0].status == SinkStatus.WRITTEN


def test_multiple_runs_produce_separate_events():
    wf, sink = _make_workflow()
    r1 = wf.run("App de tarefas kanban", dry_run=True)
    r2 = wf.run("App de blog com CMS", dry_run=True)
    assert r1.run_id != r2.run_id
    events = sink.query_events("app_factory_completed")
    assert len(events) == 2
    run_ids = {e.payload["run_id"] for e in events}
    assert r1.run_id in run_ids and r2.run_id in run_ids


# ── AppFactoryResult model ────────────────────────────────────────────────────

def test_result_to_dict_has_run_id():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert result.to_dict()["run_id"] == result.run_id


def test_result_to_dict_has_success():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert result.to_dict()["success"] is True


def test_result_to_dict_has_cost_local_pct():
    wf, _ = _make_workflow()
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert result.to_dict()["cost_local_pct"] == _COST_LOCAL_PCT


def test_result_prd_chars_property():
    r = AppFactoryResult(run_id="abc", success=True, prd_markdown=_FAKE_PRD)
    assert r.prd_chars == len(_FAKE_PRD)


def test_result_module_count_property():
    r = AppFactoryResult(run_id="abc", success=True, artifacts={"module_count": 5})
    assert r.module_count == 5


def test_result_module_count_default_zero():
    r = AppFactoryResult(run_id="abc", success=True)
    assert r.module_count == 0


# ── error handling ────────────────────────────────────────────────────────────

def test_planner_error_returns_failure():
    wf, _ = _make_workflow(planner_ok=False, fail_msg="forced_error")
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert result.success is False
    assert "planner_error" in result.error


def test_planner_error_has_run_id():
    wf, _ = _make_workflow(planner_ok=False)
    result = wf.run(_IDEA_TEXT, dry_run=True)
    assert result.run_id
    assert len(result.run_id) == 12


def test_planner_error_writes_no_akasha():
    wf, sink = _make_workflow(planner_ok=False)
    wf.run(_IDEA_TEXT, dry_run=True)
    events = sink.query_events("app_factory_completed")
    assert len(events) == 0
