"""TaskState — projeção determinística a partir de contract + eventos ordenados."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.missions.state_machine import MissionStatus
from src.missions.models import MissionContract
from src.missions.events import EventEnvelope


class TaskState(BaseModel):
    """Snapshot do estado atual da missão — projeção dos eventos."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mission_id: str
    contract_title: str = ""
    sector: str = ""
    status: MissionStatus = MissionStatus.DRAFT
    current_step: Optional[str] = None
    completed_steps: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    errors: list[Dict[str, Any]] = Field(default_factory=list)
    cumulative_tokens: int = 0
    cumulative_cost_usd: float = 0.0
    last_event_sequence: int = 0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    retry_count: int = 0
    max_retries: int = 3
    budget_exceeded: bool = False
    approval_pending: bool = False
    checkpoint_id: Optional[str] = None
    checkpoint_at: Optional[datetime] = None
    pause_reason: Optional[str] = None
    resume_context: Dict[str, Any] = Field(default_factory=dict)
    evidence_trail: list[Dict[str, Any]] = Field(default_factory=list)


def _base_state(contract: MissionContract) -> TaskState:
    """Estado inicial antes de aplicar eventos."""
    return TaskState(
        mission_id=contract.content_hash(),
        contract_title=contract.title,
        sector=contract.sector.value,
        status=MissionStatus.DRAFT,
    )


def project_from_events(
    contract: MissionContract,
    events: list[EventEnvelope],
) -> TaskState:
    """Projeta TaskState determinístico a partir do contract + eventos ordenados."""
    state = _base_state(contract)

    for ev in sorted(events, key=lambda e: e.sequence):
        state = _apply_event(state, ev)

    return state


def _apply_event(state: TaskState, ev: EventEnvelope) -> TaskState:
    """Aplica um evento ao estado, retornando novo TaskState."""
    kwargs: Dict[str, Any] = {
        "last_event_sequence": ev.sequence,
        "last_updated": ev.timestamp,
        "cumulative_tokens": max(state.cumulative_tokens, ev.cumulative_tokens),
        "cumulative_cost_usd": max(state.cumulative_cost_usd, ev.cumulative_cost_usd),
    }

    match ev.event_type:
        case "mission_created":
            kwargs["status"] = MissionStatus.DRAFT

        case "mission_started":
            kwargs["status"] = MissionStatus.RUNNING

        case "plan_drafted":
            pass  # não altera status principal

        case "plan_approved":
            pass

        case "step_started":
            kwargs["current_step"] = ev.payload.get("step_id", "")

        case "step_completed":
            step_id = ev.payload.get("step_id", "")
            completed = list(state.completed_steps)
            if step_id and step_id not in completed:
                completed.append(step_id)
            kwargs["completed_steps"] = completed
            if state.current_step == step_id:
                kwargs["current_step"] = None

        case "tool_invoked":
            pass

        case "tool_returned":
            pass

        case "skill_invoked":
            pass

        case "skill_returned":
            pass

        case "approval_requested":
            kwargs["status"] = MissionStatus.WAITING_APPROVAL
            kwargs["approval_pending"] = True

        case "approval_granted":
            kwargs["status"] = MissionStatus.RUNNING
            kwargs["approval_pending"] = False

        case "approval_rejected":
            kwargs["status"] = MissionStatus.CANCELLED
            kwargs["approval_pending"] = False

        case "artifact_produced":
            artifacts = list(state.artifacts)
            for a in ev.payload.get("artifacts", []):
                p = a.get("path", "")
                if p and p not in artifacts:
                    artifacts.append(p)
            kwargs["artifacts"] = artifacts

        case "artifact_linked":
            artifacts = list(state.artifacts)
            for a in ev.payload.get("artifacts", []):
                p = a.get("path", "")
                if p and p not in artifacts:
                    artifacts.append(p)
            kwargs["artifacts"] = artifacts

        case "error_logged":
            errors = list(state.errors)
            errors.append({
                "error": ev.payload.get("error", ""),
                "stage": ev.payload.get("stage", ""),
                "sequence": ev.sequence,
                "timestamp": ev.timestamp.isoformat() if hasattr(ev.timestamp, "isoformat") else str(ev.timestamp),
            })
            kwargs["errors"] = errors

        case "retry_attempted":
            kwargs["retry_count"] = state.retry_count + 1

        case "budget_exceeded":
            kwargs["status"] = MissionStatus.WAITING_APPROVAL
            kwargs["budget_exceeded"] = True

        case "token_used":
            pass  # cumulative_tokens já atualizado

        case "cost_incurred":
            pass  # cumulative_cost_usd já atualizado

        case "mission_paused":
            kwargs["status"] = MissionStatus.PAUSED
            kwargs["pause_reason"] = ev.payload.get("reason", "")

        case "mission_resumed":
            kwargs["status"] = MissionStatus.RUNNING

        case "mission_completed":
            kwargs["status"] = MissionStatus.COMPLETED

        case "mission_failed":
            kwargs["status"] = MissionStatus.FAILED

        case "mission_cancelled":
            kwargs["status"] = MissionStatus.CANCELLED

        case "checkpoint_created":
            kwargs["checkpoint_id"] = ev.payload.get("checkpoint_id", "")
            kwargs["checkpoint_at"] = ev.timestamp
            kwargs["resume_context"] = ev.payload.get("resume_context", {})
            trail = list(state.evidence_trail)
            trail.append({
                "type": "checkpoint",
                "checkpoint_id": ev.payload.get("checkpoint_id", ""),
                "label": ev.payload.get("label", ""),
                "timestamp": ev.timestamp.isoformat() if hasattr(ev.timestamp, "isoformat") else str(ev.timestamp),
                "sequence": ev.sequence,
            })
            kwargs["evidence_trail"] = trail

        case "evidence_recorded":
            trail = list(state.evidence_trail)
            evidence = dict(ev.payload)
            evidence["sequence"] = ev.sequence
            evidence["timestamp"] = ev.timestamp.isoformat() if hasattr(ev.timestamp, "isoformat") else str(ev.timestamp)
            trail.append(evidence)
            kwargs["evidence_trail"] = trail

    return state.model_copy(update=kwargs)
