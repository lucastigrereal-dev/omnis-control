"""Tests for orchestrator service — plan, run, persist, list."""
import json
import pytest
from pathlib import Path
from src.mission_orchestrator import service as svc
from src.mission_orchestrator.models import RUN_STATUS_PLANNED, RUN_STATUS_DRY_RUN


def test_service_plan_returns_run():
    run = svc.plan("carrossel hotel Natal")
    assert run.run_id.startswith("run_")
    assert run.status == RUN_STATUS_PLANNED


def test_service_run_persists_log(tmp_path):
    log = tmp_path / "runs.jsonl"
    runs_root = tmp_path / "runs"
    orch_run = svc.run(
        "reels praia Natal",
        runs_root=runs_root,
        runs_log=log,
        packages_root=tmp_path / "pkg",
    )
    assert orch_run.status == RUN_STATUS_DRY_RUN
    assert log.exists()
    lines = [l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["run_id"] == orch_run.run_id


def test_service_run_creates_run_folder(tmp_path):
    log = tmp_path / "runs.jsonl"
    runs_root = tmp_path / "runs"
    orch_run = svc.run(
        "carrossel hotel",
        runs_root=runs_root,
        runs_log=log,
        packages_root=tmp_path / "pkg",
    )
    run_dir = runs_root / orch_run.run_id
    assert run_dir.exists()
    assert (run_dir / "run_manifest.json").exists()
    assert (run_dir / "01_request.md").exists()
    assert (run_dir / "05_next_action.md").exists()


def test_service_get_run(tmp_path):
    log = tmp_path / "runs.jsonl"
    runs_root = tmp_path / "runs"
    orch_run = svc.run(
        "stories praia",
        runs_root=runs_root,
        runs_log=log,
        packages_root=tmp_path / "pkg",
        allow_unknown=True,
    )
    found = svc.get_run(orch_run.run_id, runs_log=log)
    assert found is not None
    assert found.run_id == orch_run.run_id


def test_service_get_run_not_found(tmp_path):
    log = tmp_path / "empty.jsonl"
    assert svc.get_run("run_ghost", runs_log=log) is None


def test_service_list_runs(tmp_path):
    log = tmp_path / "runs.jsonl"
    runs_root = tmp_path / "runs"
    pkgs = tmp_path / "pkg"
    svc.run("reels hotel", runs_root=runs_root, runs_log=log, packages_root=pkgs)
    svc.run("carrossel Natal", runs_root=runs_root, runs_log=log, packages_root=pkgs)
    all_runs = svc.list_runs(runs_log=log)
    assert len(all_runs) == 2


def test_service_list_runs_empty(tmp_path):
    log = tmp_path / "empty.jsonl"
    assert svc.list_runs(runs_log=log) == []


def test_service_run_has_mission_id(tmp_path):
    log = tmp_path / "runs.jsonl"
    runs_root = tmp_path / "runs"
    orch_run = svc.run(
        "carrossel hotel",
        runs_root=runs_root,
        runs_log=log,
        packages_root=tmp_path / "pkg",
    )
    assert orch_run.mission_id is not None
