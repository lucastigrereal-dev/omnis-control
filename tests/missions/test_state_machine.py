"""Testes da máquina de estados: transições válidas e inválidas."""
from __future__ import annotations

import pytest

from src.missions.state_machine import (
    MissionStatus,
    VALID_TRANSITIONS,
    TERMINAL_STATES,
    InvalidTransitionError,
    assert_transition,
)


class TestValidTransitions:
    """Transições permitidas."""

    @pytest.mark.parametrize("from_state,to_state", [
        (MissionStatus.DRAFT, MissionStatus.RUNNING),
        (MissionStatus.DRAFT, MissionStatus.CANCELLED),
        (MissionStatus.RUNNING, MissionStatus.WAITING_APPROVAL),
        (MissionStatus.RUNNING, MissionStatus.PAUSED),
        (MissionStatus.RUNNING, MissionStatus.COMPLETED),
        (MissionStatus.RUNNING, MissionStatus.FAILED),
        (MissionStatus.RUNNING, MissionStatus.CANCELLED),
        (MissionStatus.WAITING_APPROVAL, MissionStatus.RUNNING),
        (MissionStatus.WAITING_APPROVAL, MissionStatus.CANCELLED),
        (MissionStatus.PAUSED, MissionStatus.RUNNING),
        (MissionStatus.PAUSED, MissionStatus.CANCELLED),
        (MissionStatus.FAILED, MissionStatus.RUNNING),
    ])
    def test_valid_transition(self, from_state, to_state):
        assert_transition(from_state, to_state)  # não deve levantar

    def test_all_states_in_transitions_dict(self):
        for status in MissionStatus:
            assert status in VALID_TRANSITIONS


class TestInvalidTransitions:
    """Transições proibidas."""

    @pytest.mark.parametrize("from_state,to_state", [
        (MissionStatus.DRAFT, MissionStatus.COMPLETED),
        (MissionStatus.DRAFT, MissionStatus.FAILED),
        (MissionStatus.DRAFT, MissionStatus.PAUSED),
        (MissionStatus.DRAFT, MissionStatus.WAITING_APPROVAL),
        (MissionStatus.RUNNING, MissionStatus.DRAFT),
        (MissionStatus.COMPLETED, MissionStatus.RUNNING),
        (MissionStatus.COMPLETED, MissionStatus.DRAFT),
        (MissionStatus.COMPLETED, MissionStatus.FAILED),
        (MissionStatus.CANCELLED, MissionStatus.RUNNING),
        (MissionStatus.CANCELLED, MissionStatus.DRAFT),
        (MissionStatus.CANCELLED, MissionStatus.COMPLETED),
        (MissionStatus.WAITING_APPROVAL, MissionStatus.COMPLETED),
        (MissionStatus.WAITING_APPROVAL, MissionStatus.DRAFT),
    ])
    def test_invalid_transition_raises(self, from_state, to_state):
        with pytest.raises(InvalidTransitionError):
            assert_transition(from_state, to_state)

    def test_error_message_contains_states(self):
        with pytest.raises(InvalidTransitionError) as excinfo:
            assert_transition(MissionStatus.COMPLETED, MissionStatus.RUNNING)
        msg = str(excinfo.value)
        assert "completed" in msg
        assert "running" in msg


class TestTerminalStates:
    """Estados terminais não permitem saída."""

    @pytest.mark.parametrize("status", [
        MissionStatus.COMPLETED,
        MissionStatus.CANCELLED,
    ])
    def test_terminal_has_no_transitions(self, status):
        assert VALID_TRANSITIONS[status] == []
        assert status in TERMINAL_STATES

    def test_failed_is_not_terminal(self):
        assert MissionStatus.FAILED not in TERMINAL_STATES
        assert VALID_TRANSITIONS[MissionStatus.FAILED] == [MissionStatus.RUNNING]
