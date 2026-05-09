"""Tests for Squad Execution Exporter."""
import json
import pytest
from src.squad_execution.planner import plan_squad_run
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad
from src.squad_execution.exporter import export_squad_run, no_secrets_in_manifest


def make_and_export(tmp_path, request="cria campanha de posts para hotel"):
    squad = compose_squad(request)
    task_plan = decompose_squad(squad)
    plan = plan_squad_run(request)
    run_dir = export_squad_run(plan, runs_root=tmp_path / "runs", squad_plan=squad, task_plan=task_plan)
    return plan, run_dir


def test_export_creates_run_dir(tmp_path):
    plan, run_dir = make_and_export(tmp_path)
    assert run_dir.is_dir()
    assert run_dir.name == plan.squad_run_id


def test_export_creates_all_six_files(tmp_path):
    _, run_dir = make_and_export(tmp_path)
    expected = [
        "squad_manifest.json", "01_request.md", "02_squad.md",
        "03_task_plan.md", "04_execution_plan.md", "05_approval.md", "06_next_actions.md",
    ]
    for fname in expected:
        assert (run_dir / fname).exists(), f"Missing: {fname}"


def test_manifest_no_secrets(tmp_path):
    plan, run_dir = make_and_export(tmp_path)
    manifest = json.loads((run_dir / "squad_manifest.json").read_text(encoding="utf-8"))
    assert no_secrets_in_manifest(manifest) is True


def test_app_approval_file_contains_blocked(tmp_path):
    _, run_dir = make_and_export(tmp_path, request="cria app CRM com dashboard")
    approval = (run_dir / "05_approval.md").read_text(encoding="utf-8")
    assert "blocked" in approval.lower() or "required" in approval.lower()


def test_marketing_approval_file_not_required(tmp_path):
    _, run_dir = make_and_export(tmp_path, request="cria campanha de posts para hotel")
    approval = (run_dir / "05_approval.md").read_text(encoding="utf-8")
    assert "planned_ready" in approval.lower() or "not required" in approval.lower()
