"""State machine do ciclo de vida de criacao de skills."""
from __future__ import annotations
import logging
from typing import Dict, List

from .models import CreationContext, CreationState

logger = logging.getLogger("omnis.forge.lifecycle")

ALLOWED_CREATION_TRANSITIONS: Dict[CreationState, List[CreationState]] = {
    CreationState.DISCOVERY: [CreationState.GAP_CONFIRMED, CreationState.DUPLICATE_FOUND],
    CreationState.GAP_CONFIRMED: [CreationState.SPEC_READY],
    CreationState.SPEC_READY: [CreationState.BUILD],
    CreationState.BUILD: [CreationState.BUILD_OK, CreationState.TESTS_FAILED],
    CreationState.BUILD_OK: [CreationState.TESTS_PASSED, CreationState.TESTS_FAILED],
    CreationState.TESTS_PASSED: [CreationState.SCORE_OK, CreationState.SCORE_LOW],
    CreationState.SCORE_OK: [CreationState.APPROVED],
    CreationState.SCORE_LOW: [CreationState.SPEC_READY],
    CreationState.DUPLICATE_FOUND: [],
    CreationState.TESTS_FAILED: [CreationState.BUILD],
    CreationState.APPROVED: [],
}


class InvalidCreationTransitionError(Exception):
    pass


def transition(ctx: CreationContext, target: str) -> CreationContext:
    """Aplica transicao de estado por nome do target."""
    target_map = {
        "duplicate_found": CreationState.DUPLICATE_FOUND,
        "gap_confirmed": CreationState.GAP_CONFIRMED,
        "spec_ready": CreationState.SPEC_READY,
        "build": CreationState.BUILD,
        "build_ok": CreationState.BUILD_OK,
        "tests_passed": CreationState.TESTS_PASSED,
        "tests_failed": CreationState.TESTS_FAILED,
        "score_ok": CreationState.SCORE_OK,
        "score_low": CreationState.SCORE_LOW,
        "approved": CreationState.APPROVED,
    }
    new_state = target_map.get(target)
    if new_state is None:
        raise InvalidCreationTransitionError(f"Target desconhecido: {target}")

    allowed = ALLOWED_CREATION_TRANSITIONS.get(ctx.state, [])
    if new_state not in allowed:
        raise InvalidCreationTransitionError(
            f"Transicao invalida: {ctx.state.name} -> {new_state.name}"
        )

    ctx.state = new_state
    ctx.logs.append(f"state={new_state.name}")
    logger.info("creation_transition", extra={"from": ctx.state.name, "to": new_state.name})
    return ctx
