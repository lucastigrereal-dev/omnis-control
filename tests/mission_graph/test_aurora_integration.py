"""Tests for Aurora integration in mission_graph nodes.

Covers:
  - validate_node + AuroraGuardrail (pass and block)
  - plan_node + AuroraPriority (score in state)
  - finalize_node + AuroraVoice (tom in state)
  - graceful degradation when Aurora raises exceptions
"""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from src.mission_graph.mission_state import initial_state, MissionGraphState
from src.mission_graph.nodes.validate_node import validate_node
from src.mission_graph.nodes.plan_node import plan_node
from src.mission_graph.nodes.finalize_node import finalize_node


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_guardrail_result(is_blocked: bool, reason: str = "") -> MagicMock:
    """Create a mock GuardrailResult."""
    result = MagicMock()
    result.is_blocked = is_blocked
    result.reason = reason
    return result


def _make_priority_report(score: int) -> MagicMock:
    """Create a mock PriorityReport with a single item at the given score."""
    item = MagicMock()
    item.score = score
    report = MagicMock()
    report.items = [item]
    return report


def _make_voice_output(adapted: str) -> MagicMock:
    """Create a mock VoiceOutput."""
    out = MagicMock()
    out.adapted = adapted
    return out


# ---------------------------------------------------------------------------
# validate_node + AuroraGuardrail
# ---------------------------------------------------------------------------

def test_validate_node_with_guardrail_pass():
    """AuroraGuardrail returns allowed → validate continues normally."""
    state = initial_state("mission-guardrail-pass")
    mock_guardrail = MagicMock()
    mock_guardrail.check.return_value = _make_guardrail_result(is_blocked=False)

    with patch("src.aurora.guardrail.AuroraGuardrail", return_value=mock_guardrail):
        result = validate_node(state)

    assert result["status"] == "running"
    assert result.get("error") is None
    mock_guardrail.check.assert_called_once_with("run_mission")


def test_validate_node_with_guardrail_block():
    """AuroraGuardrail returns blocked → validate returns status=failed."""
    state = initial_state("mission-guardrail-block")
    mock_guardrail = MagicMock()
    mock_guardrail.check.return_value = _make_guardrail_result(
        is_blocked=True, reason="Acao proibida nesta fase."
    )

    with patch("src.aurora.guardrail.AuroraGuardrail", return_value=mock_guardrail):
        result = validate_node(state)

    assert result["status"] == "failed"
    assert "AuroraGuardrail" in result["error"]
    assert "run_mission bloqueado" in result["error"]


def test_validate_node_guardrail_empty_mission_id():
    """Empty mission_id fails before guardrail is consulted."""
    state = initial_state("")
    mock_guardrail = MagicMock()

    with patch("src.aurora.guardrail.AuroraGuardrail", return_value=mock_guardrail):
        result = validate_node(state)

    assert result["status"] == "failed"
    mock_guardrail.check.assert_not_called()


# ---------------------------------------------------------------------------
# plan_node + AuroraPriority
# ---------------------------------------------------------------------------

def test_plan_node_sets_priority_score():
    """AuroraPriority returns a score → aurora_priority_score present in result."""
    state = initial_state("mission-priority-42")
    mock_scorer = MagicMock()
    mock_scorer.rank.return_value = _make_priority_report(score=75)

    with patch("src.aurora.priority.AuroraPriority", return_value=mock_scorer):
        result = plan_node(state)

    assert "steps" in result
    assert result.get("aurora_priority_score") == 75
    mock_scorer.rank.assert_called_once()


def test_plan_node_priority_score_zero_when_no_items():
    """If PriorityReport has no items, aurora_priority_score is absent (defaults to 0 in state)."""
    state = initial_state("mission-priority-empty")
    mock_scorer = MagicMock()
    empty_report = MagicMock()
    empty_report.items = []
    mock_scorer.rank.return_value = empty_report

    with patch("src.aurora.priority.AuroraPriority", return_value=mock_scorer):
        result = plan_node(state)

    assert "steps" in result
    # No score set in result — state default (0) is used
    assert result.get("aurora_priority_score") is None


# ---------------------------------------------------------------------------
# finalize_node + AuroraVoice
# ---------------------------------------------------------------------------

def test_finalize_node_sets_aurora_tom_completed():
    """AuroraVoice adapts message on completed mission → aurora_tom in result."""
    state = initial_state("mission-voice-ok")
    state["error"] = None
    mock_voice = MagicMock()
    mock_voice.adapt.return_value = _make_voice_output("Direto ao ponto: missao concluida. Move.")

    with patch("src.aurora.voice.AuroraVoice", return_value=mock_voice):
        result = finalize_node(state)

    assert result["status"] == "completed"
    assert result.get("aurora_tom") == "Direto ao ponto: missao concluida. Move."
    mock_voice.adapt.assert_called_once()


def test_finalize_node_sets_aurora_tom_failed():
    """AuroraVoice adapts message on failed mission → aurora_tom in result."""
    state = initial_state("mission-voice-fail")
    state["error"] = "something broke"
    mock_voice = MagicMock()
    mock_voice.adapt.return_value = _make_voice_output("OMNIS detectou: missao falhou. Faz isso hoje.")

    with patch("src.aurora.voice.AuroraVoice", return_value=mock_voice):
        result = finalize_node(state)

    assert result["status"] == "failed"
    assert result.get("aurora_tom") == "OMNIS detectou: missao falhou. Faz isso hoje."


# ---------------------------------------------------------------------------
# Graceful degradation — Aurora raises exceptions
# ---------------------------------------------------------------------------

def test_aurora_graceful_degradation_validate():
    """If AuroraGuardrail raises an exception, validate_node continues normally."""
    state = initial_state("mission-degrade-validate")

    with patch(
        "src.aurora.guardrail.AuroraGuardrail",
        side_effect=RuntimeError("Aurora unavailable"),
    ):
        result = validate_node(state)

    assert result["status"] == "running"
    assert result.get("error") is None


def test_aurora_graceful_degradation_plan():
    """If AuroraPriority raises an exception, plan_node returns steps without score."""
    state = initial_state("mission-degrade-plan")

    with patch(
        "src.aurora.priority.AuroraPriority",
        side_effect=RuntimeError("Aurora unavailable"),
    ):
        result = plan_node(state)

    assert "steps" in result
    assert len(result["steps"]) > 0
    # No score key added when Aurora fails
    assert result.get("aurora_priority_score") is None


def test_aurora_graceful_degradation_finalize():
    """If AuroraVoice raises an exception, finalize_node returns status without aurora_tom."""
    state = initial_state("mission-degrade-finalize")
    state["error"] = None

    with patch(
        "src.aurora.voice.AuroraVoice",
        side_effect=RuntimeError("Aurora unavailable"),
    ):
        result = finalize_node(state)

    assert result["status"] == "completed"
    # No aurora_tom key added when Aurora fails
    assert result.get("aurora_tom") is None


def test_aurora_graceful_degradation_full_flow():
    """All three nodes degrade gracefully simultaneously — mission graph completes normally."""
    state = initial_state("mission-full-degrade")

    # validate passes (Aurora down)
    with patch(
        "src.aurora.guardrail.AuroraGuardrail",
        side_effect=Exception("down"),
    ):
        v_result = validate_node(state)

    assert v_result["status"] == "running"

    # plan proceeds (Aurora down)
    state.update(v_result)
    with patch(
        "src.aurora.priority.AuroraPriority",
        side_effect=Exception("down"),
    ):
        p_result = plan_node(state)

    assert "steps" in p_result

    # finalize completes (Aurora down)
    state.update(p_result)
    with patch(
        "src.aurora.voice.AuroraVoice",
        side_effect=Exception("down"),
    ):
        f_result = finalize_node(state)

    assert f_result["status"] == "completed"


# ---------------------------------------------------------------------------
# finalize_node + AuroraRecovery
# ---------------------------------------------------------------------------

def test_finalize_node_calls_aurora_recovery():
    """finalize_node calls AuroraRecovery.save_checkpoint after completion."""
    state = initial_state("mission-recovery-ok")
    state["steps"] = [{"name": "step1"}, {"name": "step2"}]
    mock_recovery = MagicMock()

    with patch("src.aurora.recovery.AuroraRecovery", return_value=mock_recovery):
        result = finalize_node(state)

    assert result["status"] == "completed"
    mock_recovery.save_checkpoint.assert_called_once()
    call_kwargs = mock_recovery.save_checkpoint.call_args.kwargs
    assert "mission-recovery-ok" in call_kwargs["session_context"]
    assert call_kwargs["last_action"] == "finalize_mission"
    assert call_kwargs["phase"] == "D1-W5"


def test_finalize_node_recovery_degradation():
    """If AuroraRecovery raises, finalize_node returns result normally."""
    state = initial_state("mission-recovery-fail")
    state["error"] = None

    with patch("src.aurora.recovery.AuroraRecovery", side_effect=RuntimeError("disk full")):
        result = finalize_node(state)

    assert result["status"] == "completed"


# ---------------------------------------------------------------------------
# MissionGraphState — new fields default values
# ---------------------------------------------------------------------------

def test_initial_state_has_aurora_fields():
    """initial_state() includes aurora_priority_score=0 and aurora_tom=''."""
    state = initial_state("mission-state-aurora")
    assert state["aurora_priority_score"] == 0
    assert state["aurora_tom"] == ""
