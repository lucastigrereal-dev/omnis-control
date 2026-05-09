"""CLI tests for mission-report close, list, get commands."""
import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from src.cli import app
from src.mission_report import service as svc_mod

runner = CliRunner()


def _make_package(packages_root: Path, mission_id: str) -> None:
    pkg = packages_root / mission_id
    pkg.mkdir(parents=True, exist_ok=True)
    manifest = {
        "mission_id": mission_id,
        "request_text": "cria um carrossel",
        "intent": "carousel",
        "deliverable": "carousel_package",
        "account_handle": "oinatalrn",
        "package_dir": str(pkg),
        "files": [],
        "dry_run": True,
        "created_at": "2026-05-09T00:00:00Z",
    }
    (pkg / "mission_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )


def test_cli_close_completed(tmp_path, monkeypatch):
    pkgs_root = tmp_path / "mission_packages"
    _make_package(pkgs_root, "mb_cli001")
    monkeypatch.setattr(svc_mod, "PACKAGES_ROOT", pkgs_root)
    monkeypatch.setattr(svc_mod, "REPORTS_LOG", tmp_path / "reports.jsonl")
    result = runner.invoke(app, ["mission-report", "close", "mb_cli001", "--outcome", "completed"])
    assert result.exit_code == 0, result.output
    assert "mb_cli001" in result.output


def test_cli_close_json_output(tmp_path, monkeypatch):
    pkgs_root = tmp_path / "mission_packages"
    _make_package(pkgs_root, "mb_cli002")
    monkeypatch.setattr(svc_mod, "PACKAGES_ROOT", pkgs_root)
    monkeypatch.setattr(svc_mod, "REPORTS_LOG", tmp_path / "reports.jsonl")
    result = runner.invoke(
        app, ["mission-report", "close", "mb_cli002", "--outcome", "completed", "--json"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["mission_id"] == "mb_cli002"
    assert data["outcome"] == "completed"


def test_cli_close_invalid_outcome(tmp_path, monkeypatch):
    pkgs_root = tmp_path / "mission_packages"
    _make_package(pkgs_root, "mb_cli003")
    monkeypatch.setattr(svc_mod, "PACKAGES_ROOT", pkgs_root)
    monkeypatch.setattr(svc_mod, "REPORTS_LOG", tmp_path / "reports.jsonl")
    result = runner.invoke(
        app, ["mission-report", "close", "mb_cli003", "--outcome", "published"]
    )
    assert result.exit_code != 0


def test_cli_close_missing_mission(tmp_path, monkeypatch):
    pkgs_root = tmp_path / "mission_packages"
    pkgs_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(svc_mod, "PACKAGES_ROOT", pkgs_root)
    monkeypatch.setattr(svc_mod, "REPORTS_LOG", tmp_path / "reports.jsonl")
    result = runner.invoke(
        app, ["mission-report", "close", "mb_nonexistent", "--outcome", "completed"]
    )
    assert result.exit_code != 0


def test_cli_list_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(svc_mod, "REPORTS_LOG", tmp_path / "reports.jsonl")
    result = runner.invoke(app, ["mission-report", "list"])
    assert result.exit_code == 0, result.output


def test_cli_list_json(tmp_path, monkeypatch):
    pkgs_root = tmp_path / "mission_packages"
    reports_log = tmp_path / "reports.jsonl"
    _make_package(pkgs_root, "mb_list001")
    monkeypatch.setattr(svc_mod, "PACKAGES_ROOT", pkgs_root)
    monkeypatch.setattr(svc_mod, "REPORTS_LOG", reports_log)
    runner.invoke(app, ["mission-report", "close", "mb_list001", "--outcome", "completed"])
    result = runner.invoke(app, ["mission-report", "list", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 1


def test_cli_get_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(svc_mod, "REPORTS_LOG", tmp_path / "reports.jsonl")
    result = runner.invoke(app, ["mission-report", "get", "mb_nonexistent"])
    assert result.exit_code != 0
