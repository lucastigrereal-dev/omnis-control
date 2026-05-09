"""CLI tests for asset-inbox scan command."""
import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()


def make_file(parent: Path, name: str, content: bytes = b"fake") -> Path:
    p = parent / name
    p.write_bytes(content)
    return p


def test_cli_scan_nonexistent_path():
    result = runner.invoke(app, ["asset-inbox", "scan", "/nonexistent/path/xyz"])
    assert result.exit_code != 0


def test_cli_scan_supported_files(tmp_path):
    make_file(tmp_path, "photo.jpg")
    make_file(tmp_path, "clip.mp4")
    result = runner.invoke(app, ["asset-inbox", "scan", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "Asset Inbox Scan" in result.output or "Supported" in result.output


def test_cli_scan_json_output(tmp_path):
    make_file(tmp_path, "photo.jpg")
    result = runner.invoke(app, ["asset-inbox", "scan", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "scan_id" in data
    assert data["total_supported"] == 1
    assert data["next_actions"] == ["B8B Safe Import Registry"]


def test_cli_scan_limit(tmp_path):
    for i in range(10):
        make_file(tmp_path, f"img_{i}.jpg")
    result = runner.invoke(app, ["asset-inbox", "scan", str(tmp_path), "--limit", "3", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["total_supported"] <= 3


def test_cli_scan_exclude(tmp_path):
    sub = tmp_path / "skip_this"
    sub.mkdir()
    make_file(sub, "hidden.jpg")
    make_file(tmp_path, "visible.jpg")
    result = runner.invoke(
        app, ["asset-inbox", "scan", str(tmp_path), "--exclude", "skip_this", "--json"]
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["total_supported"] == 1
    assert all(i["file_name"] != "hidden.jpg" for i in data["items"])


def test_cli_scan_path_traversal_blocked():
    result = runner.invoke(app, ["asset-inbox", "scan", "../../../etc"])
    assert result.exit_code != 0


def test_cli_scan_does_not_modify_files(tmp_path):
    f = make_file(tmp_path, "photo.jpg", b"original")
    runner.invoke(app, ["asset-inbox", "scan", str(tmp_path)])
    assert f.read_bytes() == b"original"
    assert len(list(tmp_path.iterdir())) == 1


def test_cli_scan_no_secrets_in_output(tmp_path):
    make_file(tmp_path, "photo.jpg")
    result = runner.invoke(app, ["asset-inbox", "scan", str(tmp_path), "--json"])
    output = result.output.lower()
    assert "meta_app_secret" not in output
    assert "instagram_token" not in output
    assert "password" not in output
