"""W159 — Tests for CommandAuditLog."""
import json
import pytest
from src.remote_control.audit_log import AuditEntry, AuditFilter, CommandAuditLog


def _entry(**kwargs) -> AuditEntry:
    defaults = dict(command="status", source="TELEGRAM", user_id="u1", allowed=True, dry_run=True)
    defaults.update(kwargs)
    return AuditEntry(**defaults)


# ---------------------------------------------------------------------------
# AuditEntry
# ---------------------------------------------------------------------------

def test_entry_round_trip():
    e = _entry(command="publish", risk="MEDIUM")
    e2 = AuditEntry.from_dict(e.to_dict())
    assert e2.command == "publish"
    assert e2.risk == "MEDIUM"
    assert e2.user_id == "u1"


def test_entry_defaults():
    e = AuditEntry()
    assert e.dry_run is True
    assert e.allowed is True
    assert e.status == "RECEIVED"


def test_entry_metadata():
    e = _entry(metadata={"wave": "W159"})
    d = e.to_dict()
    assert d["metadata"]["wave"] == "W159"


# ---------------------------------------------------------------------------
# Basic record & query
# ---------------------------------------------------------------------------

def test_record_and_query_all():
    log = CommandAuditLog()
    log.record(_entry())
    log.record(_entry(command="publish"))
    entries = log.query()
    assert len(entries) == 2


def test_query_by_source():
    log = CommandAuditLog()
    log.record(_entry(source="TELEGRAM"))
    log.record(_entry(source="WHATSAPP"))
    f = AuditFilter(source="TELEGRAM")
    results = log.query(f)
    assert len(results) == 1
    assert results[0].source == "TELEGRAM"


def test_query_by_user():
    log = CommandAuditLog()
    log.record(_entry(user_id="alice"))
    log.record(_entry(user_id="bob"))
    results = log.query(AuditFilter(user_id="alice"))
    assert len(results) == 1


def test_query_by_command():
    log = CommandAuditLog()
    log.record(_entry(command="status"))
    log.record(_entry(command="publish"))
    results = log.query(AuditFilter(command="status"))
    assert len(results) == 1


def test_query_by_status():
    log = CommandAuditLog()
    log.record(_entry(status="EXECUTED"))
    log.record(_entry(status="BLOCKED"))
    results = log.query(AuditFilter(status="EXECUTED"))
    assert len(results) == 1


def test_query_allowed_only():
    log = CommandAuditLog()
    log.record(_entry(allowed=True))
    log.record(_entry(allowed=False))
    results = log.query(AuditFilter(allowed_only=True))
    assert all(e.allowed for e in results)
    assert len(results) == 1


def test_query_rejected_only():
    log = CommandAuditLog()
    log.record(_entry(allowed=False, rejection_reason="rate_limit"))
    log.record(_entry(allowed=True))
    results = log.query(AuditFilter(rejected_only=True))
    assert len(results) == 1
    assert not results[0].allowed


def test_query_dry_run_only():
    log = CommandAuditLog()
    log.record(_entry(dry_run=True))
    log.record(_entry(dry_run=False))
    results = log.query(AuditFilter(dry_run_only=True))
    assert len(results) == 1
    assert results[0].dry_run is True


def test_query_limit():
    log = CommandAuditLog()
    for _ in range(10):
        log.record(_entry())
    results = log.query(AuditFilter(limit=3))
    assert len(results) == 3


# ---------------------------------------------------------------------------
# get / get_all_for_command
# ---------------------------------------------------------------------------

def test_get_by_command_id():
    log = CommandAuditLog()
    e = _entry(command_id="cmd_001")
    log.record(e)
    found = log.get("cmd_001")
    assert found is not None
    assert found.command_id == "cmd_001"


def test_get_missing_returns_none():
    log = CommandAuditLog()
    assert log.get("nonexistent") is None


def test_get_all_for_command():
    log = CommandAuditLog()
    log.record(_entry(command_id="cmd_001", status="RECEIVED"))
    log.record(_entry(command_id="cmd_001", status="EXECUTED"))
    log.record(_entry(command_id="cmd_002"))
    entries = log.get_all_for_command("cmd_001")
    assert len(entries) == 2


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_stats_counts():
    log = CommandAuditLog()
    log.record(_entry(source="TELEGRAM", allowed=True, dry_run=True, status="EXECUTED"))
    log.record(_entry(source="TELEGRAM", allowed=False, dry_run=True, status="BLOCKED"))
    log.record(_entry(source="WHATSAPP", allowed=True, dry_run=False, status="EXECUTED"))
    s = log.stats()
    assert s["total"] == 3
    assert s["allowed"] == 2
    assert s["rejected"] == 1
    assert s["dry_run"] == 2
    assert s["by_source"]["TELEGRAM"] == 2
    assert s["by_source"]["WHATSAPP"] == 1
    assert s["by_status"]["EXECUTED"] == 2
    assert s["by_status"]["BLOCKED"] == 1


def test_stats_empty():
    log = CommandAuditLog()
    s = log.stats()
    assert s["total"] == 0


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------

def test_clear():
    log = CommandAuditLog()
    log.record(_entry())
    log.clear()
    assert log.query() == []


# ---------------------------------------------------------------------------
# record_dict
# ---------------------------------------------------------------------------

def test_record_dict():
    log = CommandAuditLog()
    log.record_dict({"command": "ping", "source": "CLI", "user_id": "u2"})
    results = log.query(AuditFilter(command="ping"))
    assert len(results) == 1


# ---------------------------------------------------------------------------
# JSONL persistence
# ---------------------------------------------------------------------------

def test_jsonl_persistence(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    log = CommandAuditLog(log_path=log_file)
    log.record(_entry(command="status", source="TELEGRAM"))
    log.record(_entry(command="publish", source="WHATSAPP"))
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    data = json.loads(lines[0])
    assert data["command"] == "status"


def test_jsonl_reload(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    log1 = CommandAuditLog(log_path=log_file)
    log1.record(_entry(command="first"))
    log1.record(_entry(command="second"))

    log2 = CommandAuditLog(log_path=log_file)
    results = log2.query()
    assert len(results) == 2
    assert {e.command for e in results} == {"first", "second"}


def test_jsonl_reload_method(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    log = CommandAuditLog(log_path=log_file)
    log.record(_entry(command="ping"))
    log.clear()
    log.reload()
    assert len(log.query()) == 1


def test_no_path_works_in_memory():
    log = CommandAuditLog()
    log.record(_entry())
    assert len(log.query()) == 1
