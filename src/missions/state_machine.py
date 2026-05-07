"""Mission State Machine — 7 estados, transições validadas."""
from __future__ import annotations

from enum import Enum


class MissionStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


VALID_TRANSITIONS: dict[MissionStatus, list[MissionStatus]] = {
    MissionStatus.DRAFT: [MissionStatus.RUNNING, MissionStatus.CANCELLED],
    MissionStatus.RUNNING: [
        MissionStatus.WAITING_APPROVAL,
        MissionStatus.PAUSED,
        MissionStatus.COMPLETED,
        MissionStatus.FAILED,
        MissionStatus.CANCELLED,
    ],
    MissionStatus.WAITING_APPROVAL: [
        MissionStatus.RUNNING,
        MissionStatus.CANCELLED,
    ],
    MissionStatus.PAUSED: [MissionStatus.RUNNING, MissionStatus.CANCELLED],
    MissionStatus.COMPLETED: [],
    MissionStatus.FAILED: [MissionStatus.RUNNING],
    MissionStatus.CANCELLED: [],
}

TERMINAL_STATES: frozenset[MissionStatus] = frozenset({
    MissionStatus.COMPLETED,
    MissionStatus.CANCELLED,
})


class InvalidTransitionError(Exception):
    """Transição de estado inválida."""


def assert_transition(
    current: MissionStatus,
    target: MissionStatus,
) -> None:
    """Levanta InvalidTransitionError se a transição não for permitida."""
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise InvalidTransitionError(
            f"Transição inválida: {current.value} -> {target.value}. "
            f"Permitidas: {[s.value for s in allowed]}"
        )
