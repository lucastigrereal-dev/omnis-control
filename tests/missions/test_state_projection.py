"""Testes de projeção determinística: contract + events → TaskState."""
from __future__ import annotations

import pytest

from src.missions.events import EventEnvelope
from src.missions.state import project_from_events, TaskState
from src.missions.state_machine import MissionStatus


class TestProjectFromEvents:
    """Projeção determinística a partir de contract + eventos."""

    def test_no_events_returns_draft(self, sample_contract):
        state = project_from_events(sample_contract, [])
        assert state.status == MissionStatus.DRAFT
        assert state.mission_id == sample_contract.content_hash()
        assert state.cumulative_tokens == 0
        assert state.cumulative_cost_usd == 0.0
        assert state.last_event_sequence == 0

    def test_mission_started(self, sample_contract):
        events = [
            EventEnvelope(
                mission_id=sample_contract.content_hash(),
                event_type="mission_started",
                sequence=1,
                actor="test",
            ),
        ]
        state = project_from_events(sample_contract, events)
        assert state.status == MissionStatus.RUNNING

    def test_mission_lifecycle(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="mission_completed", sequence=2, actor="test"),
        ]
        state = project_from_events(sample_contract, events)
        assert state.status == MissionStatus.COMPLETED

    def test_mission_failed(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="mission_failed", sequence=2, actor="test"),
        ]
        state = project_from_events(sample_contract, events)
        assert state.status == MissionStatus.FAILED

    def test_mission_cancelled(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="mission_cancelled", sequence=2, actor="test"),
        ]
        state = project_from_events(sample_contract, events)
        assert state.status == MissionStatus.CANCELLED

    def test_events_must_be_sorted(self, sample_contract):
        """Eventos fora de ordem devem ser reordenados internamente."""
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_completed", sequence=3, actor="test"),
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="step_started", sequence=2, actor="test"),
        ]
        state = project_from_events(sample_contract, events)
        assert state.status == MissionStatus.COMPLETED
        assert state.last_event_sequence == 3

    def test_last_updated_reflects_last_event(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="mission_completed", sequence=2, actor="test"),
        ]
        state = project_from_events(sample_contract, events)
        assert state.last_updated == events[1].timestamp


class TestCumulativeTokens:
    """cumulative_tokens e cumulative_cost_usd vêm do último evento."""

    def test_cumulative_from_events(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(
                mission_id=mid, event_type="token_used", sequence=1, actor="test",
                cumulative_tokens=500, cumulative_cost_usd=0.05,
            ),
            EventEnvelope(
                mission_id=mid, event_type="token_used", sequence=2, actor="test",
                cumulative_tokens=1200, cumulative_cost_usd=0.12,
            ),
        ]
        state = project_from_events(sample_contract, events)
        assert state.cumulative_tokens == 1200
        assert state.cumulative_cost_usd == 0.12


class TestApprovalFlow:
    """Fluxo de aprovação."""

    def test_approval_requested(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="approval_requested", sequence=2, actor="test"),
        ]
        state = project_from_events(sample_contract, events)
        assert state.status == MissionStatus.WAITING_APPROVAL
        assert state.approval_pending is True

    def test_approval_granted(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="approval_requested", sequence=2, actor="test"),
            EventEnvelope(mission_id=mid, event_type="approval_granted", sequence=3, actor="test"),
        ]
        state = project_from_events(sample_contract, events)
        assert state.status == MissionStatus.RUNNING
        assert state.approval_pending is False

    def test_approval_rejected(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="approval_requested", sequence=2, actor="test"),
            EventEnvelope(mission_id=mid, event_type="approval_rejected", sequence=3, actor="test"),
        ]
        state = project_from_events(sample_contract, events)
        assert state.status == MissionStatus.CANCELLED


class TestStepsAndArtifacts:
    """Steps e artifacts tracking."""

    def test_step_started(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="step_started", sequence=2, actor="test",
                         payload={"step_id": "step-1"}),
        ]
        state = project_from_events(sample_contract, events)
        assert state.current_step == "step-1"

    def test_step_completed(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="step_started", sequence=1, actor="test",
                         payload={"step_id": "step-1"}),
            EventEnvelope(mission_id=mid, event_type="step_completed", sequence=2, actor="test",
                         payload={"step_id": "step-1"}),
        ]
        state = project_from_events(sample_contract, events)
        assert "step-1" in state.completed_steps
        assert state.current_step is None

    def test_artifact_produced(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="artifact_produced", sequence=1, actor="test",
                         payload={"artifacts": [{"path": "docs/test.md", "artifact_type": "markdown"}]}),
        ]
        state = project_from_events(sample_contract, events)
        assert "docs/test.md" in state.artifacts

    def test_artifact_deduplication(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="artifact_produced", sequence=1, actor="test",
                         payload={"artifacts": [{"path": "docs/test.md"}]}),
            EventEnvelope(mission_id=mid, event_type="artifact_produced", sequence=2, actor="test",
                         payload={"artifacts": [{"path": "docs/test.md"}]}),
        ]
        state = project_from_events(sample_contract, events)
        assert state.artifacts.count("docs/test.md") == 1


class TestErrorsAndRetries:
    """Error logging e retries."""

    def test_error_logged(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="error_logged", sequence=1, actor="test",
                         payload={"error": "Connection refused", "stage": "deploy"}),
        ]
        state = project_from_events(sample_contract, events)
        assert len(state.errors) == 1
        assert state.errors[0]["error"] == "Connection refused"

    def test_retry_attempted(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="retry_attempted", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="retry_attempted", sequence=2, actor="test"),
        ]
        state = project_from_events(sample_contract, events)
        assert state.retry_count == 2


class TestBudgetExceeded:
    """budget_exceeded sempre vai para waiting_approval."""

    def test_budget_exceeded_pauses(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="budget_exceeded", sequence=2, actor="test",
                         payload={"limit": "max_tokens", "current": 99999}),
        ]
        state = project_from_events(sample_contract, events)
        assert state.status == MissionStatus.WAITING_APPROVAL
        assert state.budget_exceeded is True


class TestPauseResume:
    """Pause e resume."""

    def test_pause_resume(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="mission_paused", sequence=2, actor="test"),
            EventEnvelope(mission_id=mid, event_type="mission_resumed", sequence=3, actor="test"),
        ]
        state = project_from_events(sample_contract, events)
        assert state.status == MissionStatus.RUNNING


class TestDeterminism:
    """Mesma entrada → mesma projeção."""

    def test_deterministic_projection(self, sample_contract):
        mid = sample_contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="step_started", sequence=2, actor="test",
                         payload={"step_id": "s1"}),
            EventEnvelope(mission_id=mid, event_type="step_completed", sequence=3, actor="test",
                         payload={"step_id": "s1"}),
            EventEnvelope(mission_id=mid, event_type="mission_completed", sequence=4, actor="test"),
        ]
        s1 = project_from_events(sample_contract, events)
        s2 = project_from_events(sample_contract, events)
        assert s1.model_dump() == s2.model_dump()
