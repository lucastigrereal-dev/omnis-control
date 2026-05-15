"""Tests for W112 — Pipeline stage state machine."""
from __future__ import annotations

import pytest

from src.sales.pipeline import (
    PipelineStage,
    PipelineContext,
    TransitionLog,
    InvalidTransitionError,
    ALLOWED_TRANSITIONS,
    get_valid_transitions,
    can_transition,
)


class TestPipelineStage:
    def test_all_stages_present(self):
        stages = {s.value for s in PipelineStage}
        assert "novo" in stages
        assert "qualificado" in stages
        assert "proposta" in stages
        assert "negociacao" in stages
        assert "fechado" in stages
        assert "perdido" in stages
        assert "arquivado" in stages
        assert len(stages) == 7


class TestAllowedTransitions:
    def test_novo_to_qualificado_valid(self):
        assert can_transition("novo", "qualificado") is True

    def test_qualificado_to_proposta_valid(self):
        assert can_transition("qualificado", "proposta") is True

    def test_fechado_to_novo_invalid(self):
        assert can_transition("fechado", "novo") is False

    def test_perdido_to_arquivado_valid(self):
        assert can_transition("perdido", "arquivado") is True

    def test_fechado_to_arquivado_valid(self):
        assert can_transition("fechado", "arquivado") is True

    def test_arquivado_no_exit(self):
        assert get_valid_transitions("arquivado") == []

    def test_perdido_can_restart(self):
        assert can_transition("perdido", "novo") is True


class TestPipelineContext:
    def test_default_stage_is_novo(self):
        ctx = PipelineContext(entity_id="d1")
        assert ctx.current_stage == "novo"
        assert ctx.dry_run is True

    def test_transition_valid(self):
        ctx = PipelineContext(entity_id="d1")
        ctx.transition_to("qualificado", actor="vendedor", reason="Lead quente")
        assert ctx.current_stage == "qualificado"
        assert ctx.transition_count == 1

    def test_transition_invalid_raises(self):
        ctx = PipelineContext(entity_id="d1")
        with pytest.raises(InvalidTransitionError, match="Invalid transition"):
            ctx.transition_to("arquivado")  # novo -> arquivado nao existe

    def test_transition_log_recorded(self):
        ctx = PipelineContext(entity_id="d1")
        ctx.transition_to("qualificado", actor="lucas", reason="Qualificado manualmente")
        log = ctx.transition_log[0]
        assert log.from_stage == "novo"
        assert log.to_stage == "qualificado"
        assert log.actor == "lucas"
        assert log.reason == "Qualificado manualmente"

    def test_full_happy_path(self):
        ctx = PipelineContext(entity_id="d1")
        ctx.transition_to("qualificado")
        ctx.transition_to("proposta")
        ctx.transition_to("negociacao")
        ctx.transition_to("fechado")
        ctx.transition_to("arquivado")
        assert ctx.current_stage == "arquivado"
        assert ctx.transition_count == 5

    def test_is_closed_won(self):
        ctx = PipelineContext(entity_id="d1")
        ctx.transition_to("qualificado")
        ctx.transition_to("proposta")
        ctx.transition_to("negociacao")
        ctx.transition_to("fechado")
        assert ctx.is_closed_won is True
        assert ctx.is_closed_lost is False
        assert ctx.is_active is False

    def test_is_closed_lost(self):
        ctx = PipelineContext(entity_id="d1")
        ctx.transition_to("perdido")
        assert ctx.is_closed_lost is True
        assert ctx.is_closed_won is False
        assert ctx.is_active is False

    def test_is_active(self):
        ctx = PipelineContext(entity_id="d1")
        assert ctx.is_active is True
        ctx.transition_to("qualificado")
        assert ctx.is_active is True

    def test_to_dict_roundtrip(self):
        ctx = PipelineContext(entity_id="d1")
        ctx.transition_to("qualificado", actor="test", reason="test reason")
        d = ctx.to_dict()
        restored = PipelineContext.from_dict(d)
        assert restored.entity_id == "d1"
        assert restored.current_stage == "qualificado"
        assert restored.transition_count == 1

    def test_transition_qualificado_back_to_novo(self):
        ctx = PipelineContext(entity_id="d1")
        ctx.transition_to("qualificado")
        ctx.transition_to("novo", reason="Requalificacao necessaria")
        assert ctx.current_stage == "novo"

    def test_dry_run_default(self):
        ctx = PipelineContext(entity_id="d1")
        assert ctx.dry_run is True


class TestTransitionLog:
    def test_create_log(self):
        log = TransitionLog(from_stage="novo", to_stage="qualificado", actor="test")
        assert log.from_stage == "novo"
        assert log.to_stage == "qualificado"

    def test_to_dict(self):
        log = TransitionLog(
            from_stage="novo",
            to_stage="qualificado",
            actor="lucas",
            reason="teste",
        )
        d = log.to_dict()
        assert d["from_stage"] == "novo"
        assert d["actor"] == "lucas"
