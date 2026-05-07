"""Durable Mission Runtime — checkpoint, pause, resume, retry. P0.7."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.missions.repository import JsonlRepository, MissionRepository
from src.missions.events import EventEnvelope
from src.missions.state import TaskState
from src.missions.state_machine import MissionStatus, assert_transition


def checkpoint_mission(
    mission_id: str,
    repo: Optional[MissionRepository] = None,
    label: str = "",
) -> Dict[str, Any]:
    """Cria um checkpoint do estado atual da missão.

    Emite evento checkpoint_created + salva snapshot em disco.
    Idempotente: pode ser chamado múltiplas vezes, cada chamada gera novo checkpoint.
    """
    repo = repo or JsonlRepository()
    state = repo.project(mission_id)
    checkpoint_id = uuid.uuid4().hex[:12]

    resume_context = {
        "current_step": state.current_step,
        "completed_steps": state.completed_steps,
        "last_sequence": state.last_event_sequence,
        "artifacts": state.artifacts,
    }

    event = EventEnvelope(
        mission_id=mission_id,
        event_type="checkpoint_created",
        sequence=0,
        actor="runtime",
        actor_detail="checkpoint",
        payload={
            "checkpoint_id": checkpoint_id,
            "label": label,
            "resume_context": resume_context,
            "state_summary": {
                "status": state.status.value,
                "cumulative_tokens": state.cumulative_tokens,
                "errors": len(state.errors),
            },
        },
    )
    appended = repo.append_event(event)
    repo.save_checkpoint(mission_id, checkpoint_id, state)

    return {
        "checkpoint_id": checkpoint_id,
        "mission_id": mission_id,
        "label": label,
        "idempotency_key": appended.idempotency_key,
    }


def pause_mission(
    mission_id: str,
    reason: str = "",
    repo: Optional[MissionRepository] = None,
) -> Dict[str, Any]:
    """Pausa a missão com motivo registrado.

    Só pode pausar missão em estado RUNNING ou WAITING_APPROVAL.
    Emite mission_paused + checkpoint_created (snapshot pré-pause).
    """
    repo = repo or JsonlRepository()
    state = repo.project(mission_id)

    assert_transition(state.status, MissionStatus.PAUSED)

    # Auto-checkpoint antes de pausar
    checkpoint_mission(mission_id, repo, label=f"pre-pause: {reason}" if reason else "pre-pause")

    event = EventEnvelope(
        mission_id=mission_id,
        event_type="mission_paused",
        sequence=0,
        actor="runtime",
        actor_detail="pause",
        payload={"reason": reason},
    )
    appended = repo.append_event(event)

    return {
        "mission_id": mission_id,
        "status": "paused",
        "reason": reason,
        "idempotency_key": appended.idempotency_key,
    }


def resume_mission(
    mission_id: str,
    repo: Optional[MissionRepository] = None,
) -> Dict[str, Any]:
    """Resume missão pausada, retornando contexto para continuar.

    Só pode resumir missão em estado PAUSED.
    Emite mission_resumed. Retorna resume_context do último checkpoint.
    """
    repo = repo or JsonlRepository()
    state = repo.project(mission_id)

    assert_transition(state.status, MissionStatus.RUNNING)

    # Busca contexto do último checkpoint
    latest = repo.get_latest_checkpoint(mission_id)
    resume_context = {}
    if latest and "state" in latest:
        st = latest["state"]
        resume_context = {
            "current_step": st.get("current_step"),
            "completed_steps": st.get("completed_steps", []),
            "last_sequence": st.get("last_event_sequence", 0),
            "artifacts": st.get("artifacts", []),
        }

    event = EventEnvelope(
        mission_id=mission_id,
        event_type="mission_resumed",
        sequence=0,
        actor="runtime",
        actor_detail="resume",
        payload={"resume_context": resume_context},
    )
    appended = repo.append_event(event)

    return {
        "mission_id": mission_id,
        "status": "running",
        "resume_context": resume_context,
        "idempotency_key": appended.idempotency_key,
    }


def retry_mission(
    mission_id: str,
    repo: Optional[MissionRepository] = None,
) -> Dict[str, Any]:
    """Retenta missão que falhou, se ainda houver tentativas disponíveis.

    Só pode retry de FAILED.
    Bloqueia se retry_count >= max_retries.
    Emite retry_attempted + mission_resumed.
    """
    repo = repo or JsonlRepository()
    state = repo.project(mission_id)

    if state.status != MissionStatus.FAILED:
        return {
            "mission_id": mission_id,
            "status": "blocked",
            "reason": f"Missão em estado '{state.status.value}', não 'failed'. Use pause/resume ou crie nova missão.",
            "retry_allowed": False,
        }

    if state.retry_count >= state.max_retries:
        return {
            "mission_id": mission_id,
            "status": "blocked",
            "reason": f"Limite de retries atingido ({state.retry_count}/{state.max_retries}). Crie nova missão com --parent.",
            "retry_allowed": False,
            "retry_count": state.retry_count,
            "max_retries": state.max_retries,
        }

    assert_transition(state.status, MissionStatus.RUNNING)

    # Emit retry_attempted
    retry_event = EventEnvelope(
        mission_id=mission_id,
        event_type="retry_attempted",
        sequence=0,
        actor="runtime",
        actor_detail="retry",
        payload={
            "attempt": state.retry_count + 1,
            "max_retries": state.max_retries,
            "previous_errors": [
                {"error": e.get("error", ""), "stage": e.get("stage", "")}
                for e in state.errors[-3:]
            ],
        },
    )
    repo.append_event(retry_event)

    # Emit mission_resumed (transition failed → running)
    resume_event = EventEnvelope(
        mission_id=mission_id,
        event_type="mission_resumed",
        sequence=0,
        actor="runtime",
        actor_detail="retry",
        payload={"trigger": "retry", "attempt": state.retry_count + 1},
    )
    appended = repo.append_event(resume_event)

    return {
        "mission_id": mission_id,
        "status": "running",
        "retry_attempt": state.retry_count + 1,
        "remaining_retries": state.max_retries - (state.retry_count + 1),
        "idempotency_key": appended.idempotency_key,
    }


def get_resume_context(
    mission_id: str,
    repo: Optional[MissionRepository] = None,
) -> Dict[str, Any]:
    """Retorna o contexto necessário para retomar execução de uma missão.

    Combina TaskState atual + último checkpoint disponível.
    Útil para agents/skills saberem 'onde eu estava?' antes de agir.
    """
    repo = repo or JsonlRepository()

    try:
        state = repo.project(mission_id)
    except Exception:
        return {"mission_id": mission_id, "status": "not_found", "resumable": False}

    latest_ckpt = repo.get_latest_checkpoint(mission_id)

    # Determine resumability
    resumable = state.status in (
        MissionStatus.PAUSED,
        MissionStatus.RUNNING,
        MissionStatus.FAILED,
        MissionStatus.WAITING_APPROVAL,
    )

    return {
        "mission_id": mission_id,
        "title": state.contract_title,
        "status": state.status.value,
        "resumable": resumable,
        "current_step": state.current_step,
        "completed_steps": state.completed_steps,
        "last_sequence": state.last_event_sequence,
        "retry_count": state.retry_count,
        "max_retries": state.max_retries,
        "pause_reason": state.pause_reason,
        "errors": [{"error": e.get("error", ""), "stage": e.get("stage", "")} for e in state.errors[-5:]],
        "artifacts": state.artifacts,
        "budget_remaining": {
            "tokens": state.cumulative_tokens,
            "cost_usd": state.cumulative_cost_usd,
        },
        "latest_checkpoint": latest_ckpt["checkpoint_id"] if latest_ckpt else None,
        "checkpoint_at": state.checkpoint_at.isoformat() if state.checkpoint_at else None,
    }
