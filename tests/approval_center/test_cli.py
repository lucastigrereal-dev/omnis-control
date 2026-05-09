"""CLI tests for approval center."""
import json
import pytest
from typer.testing import CliRunner
from src.cli import app
from src.approval_center import store as store_mod

runner = CliRunner()


def test_cli_approvals_center_help():
    result = runner.invoke(app, ["approvals-center", "--help"])
    assert result.exit_code == 0
    assert "request" in result.output
    assert "list" in result.output
    assert "show" in result.output
    assert "approve" in result.output
    assert "reject" in result.output


def test_cli_request_json(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "approvals.jsonl")
    result = runner.invoke(app, [
        "approvals-center", "request", "publish reels hotel",
        "--capability", "campaign_package", "--json",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "pending"
    assert data["request_id"].startswith("req_")
    assert data["capability_id"] == "campaign_package"


def test_cli_list_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "empty.jsonl")
    result = runner.invoke(app, ["approvals-center", "list"])
    assert result.exit_code == 0


def test_cli_show_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "empty.jsonl")
    result = runner.invoke(app, ["approvals-center", "show", "req_ghost"])
    assert result.exit_code != 0


def test_cli_approve_json(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "approvals.jsonl")
    create = runner.invoke(app, [
        "approvals-center", "request", "test approve",
        "--capability", "campaign_package", "--json",
    ])
    req_id = json.loads(create.output)["request_id"]
    result = runner.invoke(app, [
        "approvals-center", "approve", req_id, "--note", "cleared", "--json",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "approved"


def test_cli_reject_json(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "approvals.jsonl")
    create = runner.invoke(app, [
        "approvals-center", "request", "test reject",
        "--capability", "campaign_package", "--json",
    ])
    req_id = json.loads(create.output)["request_id"]
    result = runner.invoke(app, [
        "approvals-center", "reject", req_id, "--note", "too risky", "--json",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "rejected"


def test_cli_approve_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "empty.jsonl")
    result = runner.invoke(app, ["approvals-center", "approve", "req_ghost"])
    assert result.exit_code != 0
