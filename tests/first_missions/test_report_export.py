"""W194+W195 — Tests for failure taxonomy + report export."""
import json
from pathlib import Path

import pytest
from src.first_missions.models import Mission, FailureCategory, MissionStatus
from src.first_missions.report_export import (
    classify_failure,
    export_mission_json,
    export_mission_markdown,
    write_export,
)


# ---------------------------------------------------------------------------
# Failure classification (W194)
# ---------------------------------------------------------------------------

def test_classify_none():
    assert classify_failure("") == FailureCategory.NONE


def test_classify_validation():
    assert classify_failure("ValidationError: invalid input") == FailureCategory.VALIDATION
    assert classify_failure("Missing required field") == FailureCategory.VALIDATION


def test_classify_timeout():
    assert classify_failure("TimeoutError: deadline exceeded") == FailureCategory.TIMEOUT
    assert classify_failure("Connection timed out") == FailureCategory.TIMEOUT


def test_classify_storage():
    assert classify_failure("IO error: disk full") == FailureCategory.STORAGE
    assert classify_failure("Permission denied writing file") == FailureCategory.STORAGE


def test_classify_runtime():
    assert classify_failure("RuntimeError: something broke") == FailureCategory.RUNTIME
    assert classify_failure("Exception: unexpected") == FailureCategory.RUNTIME


def test_classify_unknown():
    assert classify_failure("mysterious cosmic ray") == FailureCategory.UNKNOWN


# ---------------------------------------------------------------------------
# JSON export (W195)
# ---------------------------------------------------------------------------

def test_export_json():
    m = Mission(name="test", tags=["a"])
    e = export_mission_json(m, [])
    assert e["mission"]["name"] == "test"
    assert e["mission"]["tags"] == ["a"]
    assert "exported_at" in e
    assert e["results"] == []


# ---------------------------------------------------------------------------
# Markdown export
# ---------------------------------------------------------------------------

def test_export_markdown():
    m = Mission(name="md_test")
    md = export_mission_markdown(m, [])
    assert "# Mission Report: md_test" in md
    assert "## Results" in md


def test_export_markdown_with_error():
    m = Mission(name="err", error="Invalid input detected")
    m.status = MissionStatus.FAILED
    md = export_mission_markdown(m, [])
    assert "Invalid input detected" in md
    assert "VALIDATION" in md


# ---------------------------------------------------------------------------
# Write export (path safety)
# ---------------------------------------------------------------------------

def test_write_export(tmp_path):
    path = tmp_path / "subdir" / "report.md"
    write_export("# Hello", path)
    assert path.exists()
    assert path.read_text() == "# Hello"


def test_write_export_blocked_outside_home():
    """Should reject paths outside home dir."""
    with pytest.raises(PermissionError):
        write_export("content", Path("/etc/malicious"))
