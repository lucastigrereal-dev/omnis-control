"""Tests for src/api/structured_logging.py — W19.

8 tests covering:
1. JsonFormatter produces valid JSON
2. JsonFormatter includes required fields
3. setup_logging() doesn't crash
4. StructuredLoggingMiddleware writes log entries (monkeypatched path)
5. Log entry has correct status_code
6. Log entry has correct method
7. Log entry has correct path
8. Graceful degradation when log dir is not writable
"""
from __future__ import annotations

import json
import logging
import os
import stat
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_app(access_log_path: Path):
    """Return a minimal Starlette TestClient app with the middleware wired."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.api.structured_logging import StructuredLoggingMiddleware

    api = FastAPI()

    @api.get("/ping")
    def ping():
        return {"ok": True}

    api.add_middleware(StructuredLoggingMiddleware, access_log=access_log_path)
    return TestClient(api)


# ---------------------------------------------------------------------------
# 1. JsonFormatter produces valid JSON
# ---------------------------------------------------------------------------


def test_json_formatter_produces_valid_json():
    from src.api.structured_logging import JsonFormatter

    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello world",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)  # must not raise
    assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# 2. JsonFormatter includes required fields
# ---------------------------------------------------------------------------


def test_json_formatter_required_fields():
    from src.api.structured_logging import JsonFormatter

    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="omnis.test",
        level=logging.WARNING,
        pathname=__file__,
        lineno=42,
        msg="check fields",
        args=(),
        exc_info=None,
    )
    parsed = json.loads(formatter.format(record))

    for field in ("ts", "level", "logger", "message", "module", "line"):
        assert field in parsed, f"missing field: {field}"

    assert parsed["level"] == "WARNING"
    assert parsed["logger"] == "omnis.test"
    assert parsed["message"] == "check fields"
    assert parsed["line"] == 42


# ---------------------------------------------------------------------------
# 3. setup_logging() doesn't crash
# ---------------------------------------------------------------------------


def test_setup_logging_does_not_crash(tmp_path):
    from src.api.structured_logging import setup_logging

    log_file = tmp_path / "test.log"
    # Should not raise any exception
    setup_logging(log_level="DEBUG", log_file=str(log_file))
    # No assertion needed — reaching here means no crash


# ---------------------------------------------------------------------------
# 4. StructuredLoggingMiddleware writes log entries
# ---------------------------------------------------------------------------


def test_middleware_writes_log_entry(tmp_path):
    access_log = tmp_path / "api_access.jsonl"
    client = _make_app(access_log)

    client.get("/ping")

    assert access_log.exists(), "access log file should be created"
    lines = [l for l in access_log.read_text().splitlines() if l.strip()]
    assert len(lines) >= 1, "at least one log entry expected"
    entry = json.loads(lines[0])
    assert "ts" in entry
    assert "status_code" in entry
    assert "method" in entry
    assert "path" in entry
    assert "duration_ms" in entry


# ---------------------------------------------------------------------------
# 5. Log entry has correct status_code
# ---------------------------------------------------------------------------


def test_middleware_logs_correct_status_code(tmp_path):
    access_log = tmp_path / "api_access.jsonl"
    client = _make_app(access_log)

    client.get("/ping")

    lines = [l for l in access_log.read_text().splitlines() if l.strip()]
    entry = json.loads(lines[0])
    assert entry["status_code"] == 200


# ---------------------------------------------------------------------------
# 6. Log entry has correct method
# ---------------------------------------------------------------------------


def test_middleware_logs_correct_method(tmp_path):
    access_log = tmp_path / "api_access.jsonl"
    client = _make_app(access_log)

    client.get("/ping")

    lines = [l for l in access_log.read_text().splitlines() if l.strip()]
    entry = json.loads(lines[0])
    assert entry["method"] == "GET"


# ---------------------------------------------------------------------------
# 7. Log entry has correct path
# ---------------------------------------------------------------------------


def test_middleware_logs_correct_path(tmp_path):
    access_log = tmp_path / "api_access.jsonl"
    client = _make_app(access_log)

    client.get("/ping")

    lines = [l for l in access_log.read_text().splitlines() if l.strip()]
    entry = json.loads(lines[0])
    assert entry["path"] == "/ping"


# ---------------------------------------------------------------------------
# 8. Graceful degradation if log dir not writable
# ---------------------------------------------------------------------------


def test_middleware_graceful_degradation_unwritable_dir(tmp_path, monkeypatch):
    """Middleware should not raise even when _write_entry always fails."""
    from src.api.structured_logging import StructuredLoggingMiddleware

    # Point to a path under a read-only directory by monkeypatching _write_entry
    write_calls = []

    def _broken_write_entry(self, **fields):
        write_calls.append(fields)
        raise OSError("disk full")

    monkeypatch.setattr(
        StructuredLoggingMiddleware, "_write_entry", _broken_write_entry
    )

    access_log = tmp_path / "broken" / "api_access.jsonl"
    client = _make_app(access_log)

    # Should not raise
    resp = client.get("/ping")
    assert resp.status_code == 200
    # _write_entry was called (and raised internally, but API survived)
    assert len(write_calls) >= 1
