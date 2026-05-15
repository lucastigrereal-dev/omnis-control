"""W112 — Pipeline stage state machine for Sales/CRM."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class PipelineStage(str, Enum):
    NOVO = "novo"
    QUALIFICADO = "qualificado"
    PROPOSTA = "proposta"
    NEGOCIACAO = "negociacao"
    FECHADO = "fechado"
    PERDIDO = "perdido"
    ARQUIVADO = "arquivado"


ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    PipelineStage.NOVO.value: [PipelineStage.QUALIFICADO.value, PipelineStage.PERDIDO.value],
    PipelineStage.QUALIFICADO.value: [
        PipelineStage.PROPOSTA.value,
        PipelineStage.NOVO.value,
        PipelineStage.PERDIDO.value,
    ],
    PipelineStage.PROPOSTA.value: [
        PipelineStage.NEGOCIACAO.value,
        PipelineStage.PERDIDO.value,
        PipelineStage.QUALIFICADO.value,
    ],
    PipelineStage.NEGOCIACAO.value: [
        PipelineStage.FECHADO.value,
        PipelineStage.PERDIDO.value,
        PipelineStage.PROPOSTA.value,
    ],
    PipelineStage.FECHADO.value: [PipelineStage.ARQUIVADO.value],
    PipelineStage.PERDIDO.value: [PipelineStage.NOVO.value, PipelineStage.ARQUIVADO.value],
    PipelineStage.ARQUIVADO.value: [],
}


class InvalidTransitionError(Exception):
    pass


@dataclass
class TransitionLog:
    from_stage: str
    to_stage: str
    actor: str = "system"
    reason: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "actor": self.actor,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


@dataclass
class PipelineContext:
    """Stateful context that moves through pipeline stages."""

    entity_id: str
    entity_type: str = "deal"
    current_stage: str = PipelineStage.NOVO.value
    transition_log: list[TransitionLog] = field(default_factory=list)
    dry_run: bool = True

    def transition_to(
        self,
        new_stage: str,
        actor: str = "system",
        reason: str = "",
    ) -> "PipelineContext":
        allowed = ALLOWED_TRANSITIONS.get(self.current_stage, [])
        if new_stage not in allowed:
            raise InvalidTransitionError(
                f"Invalid transition: {self.current_stage} -> {new_stage}. "
                f"Allowed: {allowed}"
            )
        log_entry = TransitionLog(
            from_stage=self.current_stage,
            to_stage=new_stage,
            actor=actor,
            reason=reason,
        )
        self.transition_log.append(log_entry)
        self.current_stage = new_stage
        return self

    @property
    def is_closed_won(self) -> bool:
        return self.current_stage == PipelineStage.FECHADO.value

    @property
    def is_closed_lost(self) -> bool:
        return self.current_stage == PipelineStage.PERDIDO.value

    @property
    def is_active(self) -> bool:
        return self.current_stage not in {
            PipelineStage.FECHADO.value,
            PipelineStage.PERDIDO.value,
            PipelineStage.ARQUIVADO.value,
        }

    @property
    def transition_count(self) -> int:
        return len(self.transition_log)

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "current_stage": self.current_stage,
            "transition_log": [t.to_dict() for t in self.transition_log],
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PipelineContext":
        ctx = cls(
            entity_id=d["entity_id"],
            entity_type=d.get("entity_type", "deal"),
            current_stage=d.get("current_stage", PipelineStage.NOVO.value),
            dry_run=d.get("dry_run", True),
        )
        ctx.transition_log = [
            TransitionLog(**t) for t in d.get("transition_log", [])
        ]
        return ctx


def get_valid_transitions(stage: str) -> list[str]:
    return ALLOWED_TRANSITIONS.get(stage, [])


def can_transition(from_stage: str, to_stage: str) -> bool:
    return to_stage in ALLOWED_TRANSITIONS.get(from_stage, [])
