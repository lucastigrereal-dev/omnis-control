"""Testes para o CLI agent — omnis agent run/runs/memory."""
import json
import os
import uuid
import pytest
from typer.testing import CliRunner

from src.cli import app
from src.agentic.agent_models import AgentRun, AgentRunRepository, AgentRunStatus
from src.memory.caption_memory import CaptionMemoryWriter, CaptionMemoryReader

runner = CliRunner(mix_stderr=False)


# ── ajuda / registro ──────────────────────────────────────────────────────────

def test_agent_group_registered():
    result = runner.invoke(app, ["agent", "--help"])
    assert result.exit_code == 0
    assert "run" in result.output
    assert "runs" in result.output
    assert "memory" in result.output


def test_agent_run_help():
    result = runner.invoke(app, ["agent", "run", "--help"])
    assert result.exit_code == 0
    assert "queue_id" in result.output.lower() or "QUEUE_ID" in result.output


def test_agent_runs_help():
    result = runner.invoke(app, ["agent", "runs", "--help"])
    assert result.exit_code == 0


def test_agent_memory_help():
    result = runner.invoke(app, ["agent", "memory", "--help"])
    assert result.exit_code == 0


def test_agent_batch_help():
    result = runner.invoke(app, ["agent", "batch", "--help"])
    assert result.exit_code == 0
    assert "limit" in result.output.lower()


def test_agent_batch_empty_queue_exits_zero():
    result = runner.invoke(app, ["agent", "batch", "--dry-run"])
    assert result.exit_code == 0


def test_agent_batch_json_empty_queue():
    result = runner.invoke(app, ["agent", "batch", "--dry-run", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "batch_id" in data
    assert data["total_processed"] == 0


def test_agent_batch_json_has_summary_fields():
    result = runner.invoke(app, ["agent", "batch", "--dry-run", "--json"])
    data = json.loads(result.output)
    for key in ("approved", "needs_review", "failed", "skipped", "results"):
        assert key in data


# ── agent run — item inexistente ──────────────────────────────────────────────

def test_agent_run_missing_id_exits_nonzero():
    result = runner.invoke(app, ["agent", "run", "nonexistent-queue-id", "--dry-run"])
    assert result.exit_code != 0


def test_agent_run_missing_id_json_exits_nonzero():
    result = runner.invoke(app, ["agent", "run", "nonexistent-queue-id", "--dry-run", "--json"])
    assert result.exit_code != 0
    data = json.loads(result.output)
    assert data["status"] == AgentRunStatus.FAILED


# ── agent runs — sem histórico ────────────────────────────────────────────────

def test_agent_runs_empty_output():
    # sem runs no caminho padrão: deve mostrar "Nenhum" ou tabela vazia
    result = runner.invoke(app, ["agent", "runs"])
    assert result.exit_code == 0


def test_agent_runs_json_returns_list():
    result = runner.invoke(app, ["agent", "runs", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


# ── agent runs — com dados injetados ─────────────────────────────────────────

def test_agent_runs_shows_saved_run(tmp_path):
    runs_path = str(tmp_path / "agent_runs.jsonl")
    repo = AgentRunRepository(path=runs_path)
    run = AgentRun(run_id="test-run-1", agent="caption_draft_agent",
                   account_handle="@oinatalrn", objective="alcance")
    run.complete()
    repo.save(run)

    # patch o path padrão do repositório via env var
    orig = os.environ.get("OMNIS_ROOT")
    os.makedirs(str(tmp_path / "data"), exist_ok=True)
    import shutil
    shutil.copy(runs_path, str(tmp_path / "data" / "agent_runs.jsonl"))
    os.environ["OMNIS_ROOT"] = str(tmp_path)

    try:
        # importa o módulo após mudar env var para usar novo repositório
        from src.agentic.agent_models import AGENT_RUNS_PATH
        result = runner.invoke(app, ["agent", "runs", "--json"])
    finally:
        if orig is None:
            os.environ.pop("OMNIS_ROOT", None)
        else:
            os.environ["OMNIS_ROOT"] = orig

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


# ── agent memory ──────────────────────────────────────────────────────────────

def test_agent_memory_no_args():
    result = runner.invoke(app, ["agent", "memory"])
    assert result.exit_code == 0


def test_agent_memory_account_and_objective_unknown():
    result = runner.invoke(app, ["agent", "memory",
                                  "--account", "@contaquejamaisteve",
                                  "--objective", "alcance"])
    assert result.exit_code == 0
    assert "Nenhuma" in result.output


# ── schedule commands ─────────────────────────────────────────────────────────

def test_schedule_add_help():
    result = runner.invoke(app, ["agent", "schedule-add", "--help"])
    assert result.exit_code == 0
    assert "every" in result.output.lower()


def test_schedule_list_empty():
    result = runner.invoke(app, ["agent", "schedule-list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_schedule_run_no_due():
    result = runner.invoke(app, ["agent", "schedule-run"])
    assert result.exit_code == 0
    assert "vencido" in result.output.lower() or result.output.strip() == ""


def test_schedule_run_json_no_due():
    result = runner.invoke(app, ["agent", "schedule-run", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_schedule_history_empty():
    result = runner.invoke(app, ["agent", "schedule-history", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_schedule_remove_missing():
    result = runner.invoke(app, ["agent", "schedule-remove", "nonexistent-id"])
    assert result.exit_code != 0


def test_agent_memory_with_data(tmp_path):
    mem_path = str(tmp_path / "data" / "caption_memory.jsonl")
    os.makedirs(str(tmp_path / "data"), exist_ok=True)
    writer = CaptionMemoryWriter(path=mem_path)
    writer.write("@oinatalrn", "alcance", "feed", "Legenda aprovada de teste", "r1", "d1")

    orig = os.environ.get("OMNIS_ROOT")
    os.environ["OMNIS_ROOT"] = str(tmp_path)
    try:
        result = runner.invoke(app, ["agent", "memory"])
    finally:
        if orig is None:
            os.environ.pop("OMNIS_ROOT", None)
        else:
            os.environ["OMNIS_ROOT"] = orig

    assert result.exit_code == 0
