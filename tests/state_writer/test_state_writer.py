"""Tests for StateWriter — validates data/state.json output is real and dynamic."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.state_writer.state_writer import (
    collect_state,
    write_state,
    _count_tests,
    _last_commit,
    _current_branch,
    _workflow_count,
    _active_mission_title,
    _last_orchestrator_run,
)


# ── Unit tests (fast, mocked) ─────────────────────────────────────────────────

class TestCollectStateStructure:
    def _base_patches(self):
        return (
            patch("src.state_writer.state_writer._count_tests", return_value=9844),
            patch("src.state_writer.state_writer._last_commit", return_value={"hash": "abc1234", "message": "fix: test", "date": "2026-05-24"}),
            patch("src.state_writer.state_writer._current_branch", return_value="feature/test"),
            patch("src.state_writer.state_writer._workflow_count", return_value=20),
            patch("src.state_writer.state_writer._active_mission_title", return_value=None),
            patch("src.state_writer.state_writer._last_orchestrator_run", return_value={"last_run_id": None, "last_run_status": None}),
        )

    def test_all_keys_present(self):
        patches = self._base_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            state = collect_state()

        assert "timestamp" in state
        assert "test_count" in state
        assert "last_commit" in state
        assert "branch" in state
        assert "workflows_registered" in state
        assert "active_mission_title" in state
        assert "last_run_id" in state
        assert "last_run_status" in state

    def test_cost_local_pct_removed(self):
        patches = self._base_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            state = collect_state()
        assert "cost_local_pct" not in state

    def test_test_count_is_int(self):
        with patch("src.state_writer.state_writer._count_tests", return_value=9844), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=0), \
             patch("src.state_writer.state_writer._active_mission_title", return_value=None), \
             patch("src.state_writer.state_writer._last_orchestrator_run", return_value={"last_run_id": None, "last_run_status": None}):
            state = collect_state()
        assert isinstance(state["test_count"], int)

    def test_workflows_registered_is_int(self):
        with patch("src.state_writer.state_writer._count_tests", return_value=0), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=20), \
             patch("src.state_writer.state_writer._active_mission_title", return_value=None), \
             patch("src.state_writer.state_writer._last_orchestrator_run", return_value={"last_run_id": None, "last_run_status": None}):
            state = collect_state()
        assert state["workflows_registered"] == 20

    def test_active_mission_title_propagated(self):
        with patch("src.state_writer.state_writer._count_tests", return_value=0), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=0), \
             patch("src.state_writer.state_writer._active_mission_title", return_value="Missão Teste"), \
             patch("src.state_writer.state_writer._last_orchestrator_run", return_value={"last_run_id": None, "last_run_status": None}):
            state = collect_state()
        assert state["active_mission_title"] == "Missão Teste"

    def test_last_run_fields_propagated(self):
        with patch("src.state_writer.state_writer._count_tests", return_value=0), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=0), \
             patch("src.state_writer.state_writer._active_mission_title", return_value=None), \
             patch("src.state_writer.state_writer._last_orchestrator_run", return_value={"last_run_id": "run_abc123", "last_run_status": "dry_run"}):
            state = collect_state()
        assert state["last_run_id"] == "run_abc123"
        assert state["last_run_status"] == "dry_run"

    def test_timestamp_is_iso_format(self):
        with patch("src.state_writer.state_writer._count_tests", return_value=0), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=0), \
             patch("src.state_writer.state_writer._active_mission_title", return_value=None), \
             patch("src.state_writer.state_writer._last_orchestrator_run", return_value={"last_run_id": None, "last_run_status": None}):
            state = collect_state()
        assert "T" in state["timestamp"]
        assert "+" in state["timestamp"] or "Z" in state["timestamp"]


# ── Tests for _active_mission_title ──────────────────────────────────────────

class TestActiveMissionTitle:
    def test_returns_none_if_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert _active_mission_title() is None

    def test_returns_running_mission(self, tmp_path, monkeypatch):
        missions_dir = tmp_path / "data" / "missions"
        missions_dir.mkdir(parents=True)
        index = missions_dir / "index.jsonl"
        index.write_text(
            '{"mission_id":"aaa","title":"Draft Mission","status":"draft"}\n'
            '{"mission_id":"bbb","title":"Running Mission","status":"running"}\n',
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        assert _active_mission_title() == "Running Mission"

    def test_returns_last_entry_if_no_running(self, tmp_path, monkeypatch):
        missions_dir = tmp_path / "data" / "missions"
        missions_dir.mkdir(parents=True)
        index = missions_dir / "index.jsonl"
        index.write_text(
            '{"mission_id":"aaa","title":"First Draft","status":"draft"}\n'
            '{"mission_id":"bbb","title":"Second Draft","status":"draft"}\n',
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        assert _active_mission_title() == "Second Draft"

    def test_tolerates_malformed_lines(self, tmp_path, monkeypatch):
        missions_dir = tmp_path / "data" / "missions"
        missions_dir.mkdir(parents=True)
        index = missions_dir / "index.jsonl"
        index.write_text(
            'NOT_JSON\n'
            '{"mission_id":"aaa","title":"Good Mission","status":"running"}\n',
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        assert _active_mission_title() == "Good Mission"

    def test_returns_none_if_empty_file(self, tmp_path, monkeypatch):
        missions_dir = tmp_path / "data" / "missions"
        missions_dir.mkdir(parents=True)
        (missions_dir / "index.jsonl").write_text("", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        assert _active_mission_title() is None


# ── Tests for _last_orchestrator_run ─────────────────────────────────────────

class TestLastOrchestratorRun:
    def test_returns_none_fields_if_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = _last_orchestrator_run()
        assert result == {"last_run_id": None, "last_run_status": None}

    def test_returns_last_run(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        runs = data_dir / "orchestrator_runs.jsonl"
        runs.write_text(
            '{"run_id":"run_aaa","status":"done"}\n'
            '{"run_id":"run_bbb","status":"blocked_pending_approval"}\n',
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        result = _last_orchestrator_run()
        assert result["last_run_id"] == "run_bbb"
        assert result["last_run_status"] == "blocked_pending_approval"

    def test_returns_none_if_empty_file(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "orchestrator_runs.jsonl").write_text("", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        result = _last_orchestrator_run()
        assert result == {"last_run_id": None, "last_run_status": None}

    def test_tolerates_missing_fields(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        runs = data_dir / "orchestrator_runs.jsonl"
        runs.write_text('{"other_key":"value"}\n', encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        result = _last_orchestrator_run()
        assert result["last_run_id"] is None
        assert result["last_run_status"] is None


# ── WriteState tests ──────────────────────────────────────────────────────────

class TestWriteState:
    def _all_patches(self, **overrides):
        defaults = dict(
            _count_tests=100,
            _last_commit={"hash": "abc"},
            _current_branch="main",
            _workflow_count=5,
            _active_mission_title=None,
            _last_orchestrator_run={"last_run_id": None, "last_run_status": None},
        )
        defaults.update(overrides)
        return defaults

    def test_writes_valid_json(self, tmp_path):
        out_path = str(tmp_path / "state.json")
        d = self._all_patches()
        with patch("src.state_writer.state_writer._count_tests", return_value=d["_count_tests"]), \
             patch("src.state_writer.state_writer._last_commit", return_value=d["_last_commit"]), \
             patch("src.state_writer.state_writer._current_branch", return_value=d["_current_branch"]), \
             patch("src.state_writer.state_writer._workflow_count", return_value=d["_workflow_count"]), \
             patch("src.state_writer.state_writer._active_mission_title", return_value=d["_active_mission_title"]), \
             patch("src.state_writer.state_writer._last_orchestrator_run", return_value=d["_last_orchestrator_run"]):
            written = write_state(out_path)

        assert written == out_path
        data = json.loads(Path(out_path).read_text(encoding="utf-8"))
        assert data["test_count"] == 100
        assert data["workflows_registered"] == 5
        assert "cost_local_pct" not in data

    def test_creates_parent_dirs(self, tmp_path):
        out_path = str(tmp_path / "deep" / "nested" / "state.json")
        d = self._all_patches(_count_tests=0, _workflow_count=0)
        with patch("src.state_writer.state_writer._count_tests", return_value=0), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=0), \
             patch("src.state_writer.state_writer._active_mission_title", return_value=None), \
             patch("src.state_writer.state_writer._last_orchestrator_run", return_value={"last_run_id": None, "last_run_status": None}):
            write_state(out_path)
        assert Path(out_path).exists()

    def test_respects_env_var(self, tmp_path, monkeypatch):
        env_path = str(tmp_path / "env_state.json")
        monkeypatch.setenv("OMNIS_STATE_PATH", env_path)
        with patch("src.state_writer.state_writer._count_tests", return_value=0), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=0), \
             patch("src.state_writer.state_writer._active_mission_title", return_value=None), \
             patch("src.state_writer.state_writer._last_orchestrator_run", return_value={"last_run_id": None, "last_run_status": None}):
            written = write_state()
        assert written == env_path
        assert Path(env_path).exists()

    def test_explicit_path_overrides_env(self, tmp_path, monkeypatch):
        env_path = str(tmp_path / "env.json")
        explicit_path = str(tmp_path / "explicit.json")
        monkeypatch.setenv("OMNIS_STATE_PATH", env_path)
        with patch("src.state_writer.state_writer._count_tests", return_value=0), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=0), \
             patch("src.state_writer.state_writer._active_mission_title", return_value=None), \
             patch("src.state_writer.state_writer._last_orchestrator_run", return_value={"last_run_id": None, "last_run_status": None}):
            written = write_state(explicit_path)
        assert written == explicit_path
        assert not Path(env_path).exists()


# ── Helper tests ──────────────────────────────────────────────────────────────

class TestHelpers:
    def test_last_commit_has_hash(self):
        commit = _last_commit()
        assert isinstance(commit, dict)
        if commit:
            assert "hash" in commit
            assert len(commit["hash"]) >= 7

    def test_current_branch_is_string(self):
        branch = _current_branch()
        assert isinstance(branch, str)
        assert len(branch) > 0

    def test_workflow_count_is_positive(self):
        count = _workflow_count()
        assert count > 0

    def test_workflow_count_matches_registry(self):
        from src.workflows.workflow_registry import WorkflowRegistry
        expected = WorkflowRegistry.default().count
        assert _workflow_count() == expected


# ── Integration test: real test_count must match suite ───────────────────────

class TestRealTestCount:
    def test_count_tests_real_suite(self):
        """Run actual pytest --collect-only and verify count matches real suite."""
        count = _count_tests()
        assert count > 9000, (
            f"test_count={count} is suspiciously low — "
            "expected ~9877. Check that tests/ is accessible."
        )

    def test_write_state_with_real_count(self, tmp_path):
        """Full integration: write_state() produces valid JSON with real test_count."""
        out_path = str(tmp_path / "state.json")
        write_state(out_path)

        data = json.loads(Path(out_path).read_text(encoding="utf-8"))
        assert data["test_count"] > 9000
        assert data["workflows_registered"] == 20
        assert "cost_local_pct" not in data
        assert data["branch"] != ""
        assert data["last_commit"].get("hash", "") != ""
        assert "active_mission_title" in data
        assert "last_run_id" in data
        assert "last_run_status" in data
