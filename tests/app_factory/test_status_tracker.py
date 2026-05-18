"""Tests for status tracker module."""
from __future__ import annotations

import pytest

from src.app_factory.status_tracker import (
    IdeaStatus,
    PipelineSummary,
    StatusTracker,
)


class TestIdeaStatus:
    def test_to_dict(self):
        s = IdeaStatus(
            idea_id="idea_001", title="Test App",
            overall_status="running", progress_pct=45.5,
            current_stage="build_schema",
        )
        d = s.to_dict()
        assert d["idea_id"] == "idea_001"
        assert d["title"] == "Test App"
        assert d["progress_pct"] == 45.5

    def test_default_values(self):
        s = IdeaStatus(idea_id="i1", title="T", overall_status="pending", progress_pct=0.0, current_stage="validate_idea")
        assert s.failed_stage is None
        assert s.error_message == ""


class TestPipelineSummary:
    def test_healthy_when_no_failures(self):
        s = PipelineSummary(total=3, pending=1, running=1, completed=1, failed=0, avg_progress_pct=50.0, generated_at="2026-01-01T00:00:00Z")
        assert s.healthy is True

    def test_not_healthy_when_failures(self):
        s = PipelineSummary(total=3, pending=1, running=0, completed=1, failed=1, avg_progress_pct=50.0, generated_at="2026-01-01T00:00:00Z")
        assert s.healthy is False

    def test_all_complete(self):
        s = PipelineSummary(total=2, pending=0, running=0, completed=2, failed=0, avg_progress_pct=100.0, generated_at="2026-01-01T00:00:00Z")
        assert s.all_complete is True

    def test_not_all_complete_when_pending(self):
        s = PipelineSummary(total=2, pending=1, running=0, completed=1, failed=0, avg_progress_pct=50.0, generated_at="2026-01-01T00:00:00Z")
        assert s.all_complete is False


class TestStatusTracker:
    def test_register_idea_creates_state(self):
        tracker = StatusTracker()
        state = tracker.register_idea("idea_001", "My App")
        assert state.idea_id == "idea_001"
        assert state.overall_status.value == "pending"

    def test_register_idea_idempotent(self):
        tracker = StatusTracker()
        s1 = tracker.register_idea("idea_001", "My App")
        s2 = tracker.register_idea("idea_001", "My App")
        assert s1 is s2

    def test_get_status_returns_snapshot(self):
        tracker = StatusTracker()
        tracker.register_idea("idea_001", "App")
        status = tracker.get_status("idea_001")
        assert status is not None
        assert status.idea_id == "idea_001"
        assert status.title == "App"
        assert status.overall_status == "pending"

    def test_get_status_nonexistent(self):
        tracker = StatusTracker()
        assert tracker.get_status("nonexistent") is None

    def test_mark_stage_advances_progress(self):
        tracker = StatusTracker()
        tracker.register_idea("idea_001", "App")
        tracker.mark_stage("idea_001", "validate_idea", "completed")
        state = tracker.get_state("idea_001")
        assert state.stages["validate_idea"].status.value == "completed"

    def test_mark_failed_updates_status(self):
        tracker = StatusTracker()
        tracker.register_idea("idea_001", "App")
        tracker.mark_stage("idea_001", "generate_prd", "completed")
        tracker.mark_stage("idea_001", "build_schema", "failed", "Schema error")
        status = tracker.get_status("idea_001")
        assert status.overall_status == "failed"
        assert status.failed_stage == "build_schema"

    def test_auto_finish_when_all_stages_complete(self):
        tracker = StatusTracker()
        tracker.register_idea("idea_001", "App")
        from src.app_factory.recovery import STAGE_ORDER
        for stage in STAGE_ORDER:
            tracker.mark_stage("idea_001", stage, "completed")
        status = tracker.get_status("idea_001")
        assert status.overall_status == "completed"

    def test_list_all(self):
        tracker = StatusTracker()
        tracker.register_idea("a1", "App1")
        tracker.register_idea("a2", "App2")
        all_statuses = tracker.list_all()
        assert len(all_statuses) == 2

    def test_list_by_status(self):
        tracker = StatusTracker()
        tracker.register_idea("a1", "App1")
        tracker.register_idea("a2", "App2")
        tracker.mark_stage("a1", "generate_prd", "failed", "error")
        failed = tracker.list_by_status("failed")
        pending = tracker.list_by_status("pending")
        assert len(failed) == 1
        assert len(pending) == 1

    def test_summary_empty(self):
        tracker = StatusTracker()
        s = tracker.summary()
        assert s.total == 0

    def test_summary_with_ideas(self):
        tracker = StatusTracker()
        tracker.register_idea("a1", "App1")
        tracker.register_idea("a2", "App2")
        tracker.mark_stage("a2", "generate_prd", "failed", "err")
        s = tracker.summary()
        assert s.total == 2
        assert s.failed == 1
        assert s.pending == 1

    def test_remove_idea(self):
        tracker = StatusTracker()
        tracker.register_idea("a1", "App1")
        assert tracker.remove("a1") is True
        assert tracker.get_status("a1") is None

    def test_remove_nonexistent(self):
        tracker = StatusTracker()
        assert tracker.remove("ghost") is False

    def test_get_state_nonexistent(self):
        tracker = StatusTracker()
        assert tracker.get_state("ghost") is None

    def test_mark_stage_nonexistent_idea(self):
        tracker = StatusTracker()
        result = tracker.mark_stage("ghost", "validate_idea", "completed")
        assert result is None

    def test_multiple_ideas_independent_progress(self):
        tracker = StatusTracker()
        tracker.register_idea("a1", "App1")
        tracker.register_idea("a2", "App2")
        tracker.mark_stage("a1", "validate_idea", "completed")
        tracker.mark_stage("a1", "extract_requirements", "completed")
        s1 = tracker.get_status("a1")
        s2 = tracker.get_status("a2")
        assert s1.progress_pct > s2.progress_pct

    def test_save_and_load(self, tmp_path):
        tracker = StatusTracker()
        tracker.register_idea("a1", "App1")
        tracker.mark_stage("a1", "validate_idea", "completed")
        tracker.mark_stage("a1", "extract_requirements", "completed")
        tracker.mark_stage("a1", "design_blueprint", "failed", "test error")

        filepath = tmp_path / "status.jsonl"
        count = tracker.save(str(filepath))
        assert count == 1

        tracker2 = StatusTracker()
        loaded = tracker2.load(str(filepath))
        assert loaded == 1
        status = tracker2.get_status("a1")
        assert status is not None
        assert status.title == "App1"
        assert status.overall_status == "failed"

    def test_load_empty_file(self, tmp_path):
        tracker = StatusTracker()
        filepath = tmp_path / "nonexistent.jsonl"
        count = tracker.load(str(filepath))
        assert count == 0

    def test_idea_count(self):
        tracker = StatusTracker()
        assert tracker.idea_count == 0
        tracker.register_idea("a1", "A1")
        tracker.register_idea("a2", "A2")
        assert tracker.idea_count == 2
