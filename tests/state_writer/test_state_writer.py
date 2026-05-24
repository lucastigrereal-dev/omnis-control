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
)


# ── Unit tests (fast, mocked) ─────────────────────────────────────────────────

class TestCollectStateStructure:
    def test_all_keys_present(self):
        with patch("src.state_writer.state_writer._count_tests", return_value=9844), \
             patch("src.state_writer.state_writer._last_commit", return_value={"hash": "abc1234", "message": "fix: test", "date": "2026-05-24"}), \
             patch("src.state_writer.state_writer._current_branch", return_value="feature/test"), \
             patch("src.state_writer.state_writer._workflow_count", return_value=20):
            state = collect_state()

        assert "timestamp" in state
        assert "test_count" in state
        assert "last_commit" in state
        assert "branch" in state
        assert "workflows_registered" in state
        assert "cost_local_pct" in state

    def test_test_count_is_int(self):
        with patch("src.state_writer.state_writer._count_tests", return_value=9844):
            with patch("src.state_writer.state_writer._last_commit", return_value={}), \
                 patch("src.state_writer.state_writer._current_branch", return_value=""), \
                 patch("src.state_writer.state_writer._workflow_count", return_value=0):
                state = collect_state()
        assert isinstance(state["test_count"], int)

    def test_workflows_registered_is_int(self):
        with patch("src.state_writer.state_writer._count_tests", return_value=0), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=20):
            state = collect_state()
        assert state["workflows_registered"] == 20

    def test_cost_local_pct_is_100(self):
        with patch("src.state_writer.state_writer._count_tests", return_value=0), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=0):
            state = collect_state()
        assert state["cost_local_pct"] == 100

    def test_timestamp_is_iso_format(self):
        with patch("src.state_writer.state_writer._count_tests", return_value=0), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=0):
            state = collect_state()
        assert "T" in state["timestamp"]
        assert "+" in state["timestamp"] or "Z" in state["timestamp"]


class TestWriteState:
    def test_writes_valid_json(self, tmp_path):
        out_path = str(tmp_path / "state.json")
        with patch("src.state_writer.state_writer._count_tests", return_value=100), \
             patch("src.state_writer.state_writer._last_commit", return_value={"hash": "abc"}), \
             patch("src.state_writer.state_writer._current_branch", return_value="main"), \
             patch("src.state_writer.state_writer._workflow_count", return_value=5):
            written = write_state(out_path)

        assert written == out_path
        data = json.loads(Path(out_path).read_text(encoding="utf-8"))
        assert data["test_count"] == 100
        assert data["workflows_registered"] == 5

    def test_creates_parent_dirs(self, tmp_path):
        out_path = str(tmp_path / "deep" / "nested" / "state.json")
        with patch("src.state_writer.state_writer._count_tests", return_value=0), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=0):
            write_state(out_path)
        assert Path(out_path).exists()

    def test_respects_env_var(self, tmp_path, monkeypatch):
        env_path = str(tmp_path / "env_state.json")
        monkeypatch.setenv("OMNIS_STATE_PATH", env_path)
        with patch("src.state_writer.state_writer._count_tests", return_value=0), \
             patch("src.state_writer.state_writer._last_commit", return_value={}), \
             patch("src.state_writer.state_writer._current_branch", return_value=""), \
             patch("src.state_writer.state_writer._workflow_count", return_value=0):
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
             patch("src.state_writer.state_writer._workflow_count", return_value=0):
            written = write_state(explicit_path)
        assert written == explicit_path
        assert not Path(env_path).exists()


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
        """Run actual pytest --collect-only and verify count matches real suite.

        This test takes ~5s (collect-only, not full run).
        Expected: test_count close to 9844 (±200 for ongoing changes).
        """
        count = _count_tests()
        assert count > 9000, (
            f"test_count={count} is suspiciously low — "
            "expected ~9844. Check that tests/ is accessible."
        )

    def test_write_state_with_real_count(self, tmp_path):
        """Full integration: write_state() produces valid JSON with real test_count."""
        out_path = str(tmp_path / "state.json")
        write_state(out_path)

        data = json.loads(Path(out_path).read_text(encoding="utf-8"))
        assert data["test_count"] > 9000
        assert data["workflows_registered"] == 20
        assert data["cost_local_pct"] == 100
        assert data["branch"] != ""
        assert data["last_commit"].get("hash", "") != ""
