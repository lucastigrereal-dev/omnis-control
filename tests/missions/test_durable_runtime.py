"""Testes do Durable Mission Runtime — P0.7."""
from __future__ import annotations

import pytest

from src.missions.models import MissionContract, Sector
from src.missions.events import EventEnvelope
from src.missions.repository import JsonlRepository
from src.missions.state import TaskState, project_from_events
from src.missions.state_machine import MissionStatus, InvalidTransitionError
from src.missions.runtime import (
    checkpoint_mission,
    pause_mission,
    resume_mission,
    retry_mission,
    get_resume_context,
)


@pytest.fixture
def tmp_repo(tmp_path):
    return JsonlRepository(base_dir=str(tmp_path / "missions"))


@pytest.fixture
def sample_contract() -> MissionContract:
    return MissionContract(
        title="Runtime Test Mission",
        objective="Testar durable runtime P0.7",
        sector=Sector.RESEARCH,
        user_request="Runtime test",
    )


@pytest.fixture
def saved_mission(tmp_repo, sample_contract):
    mid = tmp_repo.save_contract(sample_contract)
    # Start the mission so it's in RUNNING state
    tmp_repo.append_event(EventEnvelope(
        mission_id=mid, event_type="mission_started", sequence=0, actor="test",
    ))
    return mid


class TestCheckpoint:
    """checkpoint_mission — criação e persistência."""

    def test_checkpoint_creates_event(self, tmp_repo, saved_mission):
        result = checkpoint_mission(saved_mission, repo=tmp_repo)
        assert result["checkpoint_id"] != ""
        assert result["mission_id"] == saved_mission
        assert "idempotency_key" in result

    def test_checkpoint_saves_to_disk(self, tmp_repo, saved_mission):
        result = checkpoint_mission(saved_mission, repo=tmp_repo)
        ckpt = tmp_repo.get_checkpoint(saved_mission, result["checkpoint_id"])
        assert ckpt is not None
        assert ckpt["checkpoint_id"] == result["checkpoint_id"]

    def test_checkpoint_state_projection_updated(self, tmp_repo, saved_mission):
        result = checkpoint_mission(saved_mission, repo=tmp_repo)
        state = tmp_repo.project(saved_mission)
        assert state.checkpoint_id == result["checkpoint_id"]
        assert state.checkpoint_at is not None

    def test_multiple_checkpoints_all_saved(self, tmp_repo, saved_mission):
        c1 = checkpoint_mission(saved_mission, repo=tmp_repo, label="ckpt-1")
        c2 = checkpoint_mission(saved_mission, repo=tmp_repo, label="ckpt-2")
        assert tmp_repo.get_checkpoint(saved_mission, c1["checkpoint_id"]) is not None
        assert tmp_repo.get_checkpoint(saved_mission, c2["checkpoint_id"]) is not None
        # Latest should be c2
        latest = tmp_repo.get_latest_checkpoint(saved_mission)
        assert latest["checkpoint_id"] == c2["checkpoint_id"]


class TestPause:
    """pause_mission — pausa com motivo."""

    def test_pause_running_mission(self, tmp_repo, saved_mission):
        result = pause_mission(saved_mission, reason="Pausa manual", repo=tmp_repo)
        assert result["status"] == "paused"
        assert result["reason"] == "Pausa manual"
        state = tmp_repo.project(saved_mission)
        assert state.status == MissionStatus.PAUSED
        assert state.pause_reason == "Pausa manual"

    def test_pause_without_reason(self, tmp_repo, saved_mission):
        result = pause_mission(saved_mission, repo=tmp_repo)
        assert result["status"] == "paused"
        state = tmp_repo.project(saved_mission)
        assert state.status == MissionStatus.PAUSED
        assert state.pause_reason == ""

    def test_pause_creates_auto_checkpoint(self, tmp_repo, saved_mission):
        pause_mission(saved_mission, reason="Teste checkpoint", repo=tmp_repo)
        latest = tmp_repo.get_latest_checkpoint(saved_mission)
        assert latest is not None
        assert latest["mission_id"] == saved_mission
        # Após pause, estado projetado deve ser PAUSED
        state = tmp_repo.project(saved_mission)
        assert state.status == MissionStatus.PAUSED

    def test_pause_completed_mission_blocked(self, tmp_repo, saved_mission):
        tmp_repo.append_event(EventEnvelope(
            mission_id=saved_mission, event_type="mission_completed", sequence=0, actor="test",
        ))
        with pytest.raises(InvalidTransitionError):
            pause_mission(saved_mission, repo=tmp_repo)


class TestResume:
    """resume_mission — resume com contexto."""

    def test_resume_paused_mission(self, tmp_repo, saved_mission):
        pause_mission(saved_mission, reason="Teste resume", repo=tmp_repo)
        result = resume_mission(saved_mission, repo=tmp_repo)
        assert result["status"] == "running"
        state = tmp_repo.project(saved_mission)
        assert state.status == MissionStatus.RUNNING

    def test_resume_returns_context(self, tmp_repo, saved_mission):
        # Add a completed step, then pause, then resume
        tmp_repo.append_event(EventEnvelope(
            mission_id=saved_mission, event_type="step_completed", sequence=0, actor="test",
            payload={"step_id": "step-1"},
        ))
        pause_mission(saved_mission, reason="mid-flow", repo=tmp_repo)
        result = resume_mission(saved_mission, repo=tmp_repo)
        ctx = result.get("resume_context", {})
        assert "step-1" in ctx.get("completed_steps", [])

    def test_resume_non_paused_blocked(self, tmp_repo, saved_mission):
        with pytest.raises(InvalidTransitionError):
            resume_mission(saved_mission, repo=tmp_repo)


class TestRetry:
    """retry_mission — retry com max_retries."""

    def test_retry_from_failed(self, tmp_repo, saved_mission):
        tmp_repo.append_event(EventEnvelope(
            mission_id=saved_mission, event_type="mission_failed", sequence=0, actor="test",
        ))
        result = retry_mission(saved_mission, repo=tmp_repo)
        assert result["status"] == "running"
        assert result["retry_attempt"] == 1
        assert result["remaining_retries"] >= 0

    def test_retry_blocked_when_max_retries_reached(self, tmp_repo, saved_mission):
        tmp_repo.append_event(EventEnvelope(
            mission_id=saved_mission, event_type="mission_failed", sequence=0, actor="test",
        ))
        # Simulate max retries already used
        for _ in range(3):
            tmp_repo.append_event(EventEnvelope(
                mission_id=saved_mission, event_type="retry_attempted", sequence=0, actor="test",
            ))
            tmp_repo.append_event(EventEnvelope(
                mission_id=saved_mission, event_type="mission_failed", sequence=0, actor="test",
            ))
        result = retry_mission(saved_mission, repo=tmp_repo)
        assert result["status"] == "blocked"
        assert result["retry_allowed"] is False

    def test_retry_not_failed_blocked(self, tmp_repo, saved_mission):
        result = retry_mission(saved_mission, repo=tmp_repo)
        assert result["status"] == "blocked"
        assert result["retry_allowed"] is False


class TestGetResumeContext:
    """get_resume_context — contexto para retomar."""

    def test_resume_context_for_running_mission(self, tmp_repo, saved_mission):
        ctx = get_resume_context(saved_mission, repo=tmp_repo)
        assert ctx["status"] == "running"
        assert ctx["resumable"] is True
        assert ctx["title"] != ""

    def test_resume_context_not_found(self, tmp_repo):
        ctx = get_resume_context("nonexistent_id", repo=tmp_repo)
        assert ctx["status"] == "not_found"
        assert ctx["resumable"] is False

    def test_resume_context_after_pause(self, tmp_repo, saved_mission):
        pause_mission(saved_mission, reason="Contexto teste", repo=tmp_repo)
        ctx = get_resume_context(saved_mission, repo=tmp_repo)
        assert ctx["pause_reason"] == "Contexto teste"
        assert ctx["status"] == "paused"
        assert ctx["resumable"] is True


class TestEvidenceTrail:
    """Trilha de evidências acumulada via eventos."""

    def test_evidence_trail_accumulates(self, tmp_repo, saved_mission):
        # Emit evidence_recorded events
        tmp_repo.append_event(EventEnvelope(
            mission_id=saved_mission, event_type="evidence_recorded", sequence=0, actor="test",
            payload={"evidence_type": "file_generated", "path": "/tmp/test.png"},
        ))
        tmp_repo.append_event(EventEnvelope(
            mission_id=saved_mission, event_type="evidence_recorded", sequence=0, actor="test",
            payload={"evidence_type": "approval", "status": "granted"},
        ))
        state = tmp_repo.project(saved_mission)
        assert len(state.evidence_trail) >= 2
        types = [e.get("evidence_type") for e in state.evidence_trail if "evidence_type" in e]
        assert "file_generated" in types
        assert "approval" in types
