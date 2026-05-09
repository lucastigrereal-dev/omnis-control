"""P5.3 — Execution Plan Manifest tests."""
import json
import pytest
from src.mission_orchestrator.planner import build_plan
from src.mission_orchestrator.executor import execute
from src.mission_orchestrator.execution_manifest import build_manifest, write_manifest, no_secrets_in_manifest
from src.mission_orchestrator.models import RUN_STATUS_DRY_RUN
from src.approval_center import service as svc_mod


def test_manifest_created_from_run():
    run = build_plan("carrossel campanha instagram")
    manifest = build_manifest(run)
    assert manifest["run_id"] == run.run_id
    assert manifest["request"] == run.request_text
    assert "capabilities" in manifest
    assert "gaps" in manifest
    assert "approval_required" in manifest
    assert "status" in manifest


def test_manifest_no_secrets():
    run = build_plan("carrossel instagram campanha")
    manifest = build_manifest(run)
    assert no_secrets_in_manifest(manifest) is True


def test_manifest_reflects_approval_required():
    run = build_plan("cria app sistema api software", allow_unknown=True)
    manifest = build_manifest(run)
    assert manifest["approval_required"] is True
    assert "approval_required" in manifest["risks"]


def test_manifest_blocked_status_without_approval(tmp_path):
    run = build_plan("cria app sistema api software", allow_unknown=True)
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    manifest = build_manifest(result)
    assert manifest["status"] == "blocked_pending_approval"
    assert manifest["approval_id"] is not None


def test_manifest_dry_run_status_with_approval(tmp_path):
    run = build_plan("cria app sistema api software", allow_unknown=True)
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    approval_id = result.approval_id
    svc_mod.approve(approval_id, approvals_log=tmp_path / "approvals.jsonl")
    result.approval_id = approval_id
    result2 = execute(result, approvals_log=tmp_path / "approvals.jsonl")
    manifest = build_manifest(result2)
    assert manifest["status"] == RUN_STATUS_DRY_RUN


def test_manifest_written_to_disk(tmp_path):
    run = build_plan("carrossel campanha instagram")
    result = execute(run)
    path = write_manifest(result, tmp_path / "run_dir")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["run_id"] == run.run_id


def test_manifest_next_actions_blocked(tmp_path):
    run = build_plan("cria app sistema api software", allow_unknown=True)
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    manifest = build_manifest(result)
    actions = manifest["next_actions"]
    assert any("approvals-center" in a for a in actions)


def test_manifest_next_actions_planned():
    run = build_plan("carrossel campanha instagram")
    result = execute(run)
    manifest = build_manifest(result)
    assert isinstance(manifest["next_actions"], list)
