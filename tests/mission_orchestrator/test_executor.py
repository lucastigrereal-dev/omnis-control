"""Tests for mission orchestrator executor."""
import socket
import pytest
from src.mission_orchestrator.planner import build_plan
from src.mission_orchestrator.executor import execute
from src.mission_orchestrator.models import RUN_STATUS_DRY_RUN


def test_execute_dry_run_sets_status(tmp_path):
    run = build_plan("reels hotel Natal", account_handle="oinatalrn")
    result = execute(run, packages_root=tmp_path / "packages")
    assert result.status == RUN_STATUS_DRY_RUN


def test_execute_creates_mission_id(tmp_path):
    run = build_plan("carrossel viagem Natal", account_handle="oinatalrn")
    result = execute(run, packages_root=tmp_path / "packages")
    assert result.mission_id is not None
    assert result.mission_id.startswith("mb_")


def test_execute_s01_done(tmp_path):
    run = build_plan("reels hotel")
    result = execute(run, packages_root=tmp_path / "pkg")
    s01 = next((s for s in result.steps if s.step_id == "s01"), None)
    assert s01 is not None
    assert s01.status == "done"


def test_execute_s02_done(tmp_path):
    run = build_plan("carrossel Natal")
    result = execute(run, packages_root=tmp_path / "pkg")
    s02 = next((s for s in result.steps if s.step_id == "s02"), None)
    assert s02 is not None
    assert s02.status == "done"


def test_execute_no_network(tmp_path, monkeypatch):
    def _block(*args, **kwargs):
        raise AssertionError("Network blocked in orchestrator test")
    monkeypatch.setattr(socket.socket, "connect", _block)
    run = build_plan("stories praia Natal", allow_unknown=True)
    result = execute(run, packages_root=tmp_path / "pkg")
    assert result.status in (RUN_STATUS_DRY_RUN, "failed")


def test_execute_no_env_reads(tmp_path, monkeypatch):
    import os
    original = os.getenv
    def _assert_no_secret(key, *args, **kwargs):
        assert not key.startswith("META_") and not key.startswith("INSTAGRAM_")
        return original(key, *args, **kwargs)
    monkeypatch.setattr(os, "getenv", _assert_no_secret)
    run = build_plan("reels hotel")
    execute(run, packages_root=tmp_path / "pkg")
