"""Mission-Aware Pipeline — orquestrador magro que conecta missão ao pipeline local."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from src.missions.repository import JsonlRepository, MissionRepository
from src.missions.events import EventEnvelope, EventType
from src.missions.state_machine import MissionStatus
from src.missions.runtime import checkpoint_mission, get_resume_context
from src.tool_registry import get_tool_availability
from src.pipeline_local.service import PipelineLocalService
from src.pipeline_local.models import PipelineRunStatus, PipelineBlockReason
from src.pipeline_local.mission_models import (
    MissionPipelineResult,
    MissionPipelineStatus,
    MissionPipelineBlockReason,
)


def run_mission_content_pipeline(
    mission_id: str,
    queue_item_id: Optional[str] = None,
    caption_draft_id: Optional[str] = None,
    repo: Optional[MissionRepository] = None,
) -> MissionPipelineResult:
    """Orquestra pipeline local com eventos de missão.

    Args:
        mission_id: Content hash do MissionContract.
        queue_item_id: ID opcional do item na Content Queue.
        caption_draft_id: ID opcional do draft de legenda.
        repo: Repository opcional (usa JsonlRepository default).

    Returns:
        MissionPipelineResult com status, eventos emitidos, evidências.
    """
    repo = repo or JsonlRepository()
    run_id = uuid.uuid4().hex[:12]
    result = MissionPipelineResult(run_id=run_id, mission_id=mission_id)

    # ── Stage 0: Validate mission exists ──────────────────────────
    try:
        contract = repo.get_contract(mission_id)
    except (FileNotFoundError, Exception):
        result.status = MissionPipelineStatus.BLOCKED
        result.block_reason = MissionPipelineBlockReason.MISSION_NOT_FOUND
        result.add_warning("Mission contract não encontrado")
        return result

    # ── Stage 1: Check current state (idempotency) ────────────────
    current_state = repo.project(mission_id)

    if current_state.status == MissionStatus.PAUSED:
        result.status = MissionPipelineStatus.BLOCKED
        result.block_reason = MissionPipelineBlockReason.MISSION_PAUSED
        result.add_warning(f"Mission is PAUSED. Execute: python jarvis.py mission resume {mission_id[:12]}")
        result.add_evidence("resume_context", get_resume_context(mission_id, repo), "Contexto para resume")
        return result

    if current_state.status == MissionStatus.COMPLETED:
        result.status = MissionPipelineStatus.ALREADY_COMPLETED
        result.add_warning("MISSION_ALREADY_COMPLETED")
        result.add_evidence("mission_state", current_state.status.value, "Missão já concluída")
        return result

    if current_state.status in (MissionStatus.FAILED, MissionStatus.CANCELLED):
        result.status = MissionPipelineStatus.BLOCKED
        result.block_reason = (
            MissionPipelineBlockReason.MISSION_FAILED
            if current_state.status == MissionStatus.FAILED
            else MissionPipelineBlockReason.MISSION_CANCELLED
        )
        result.add_warning(f"Mission is {current_state.status.value}, não pode reexecutar")
        return result

    # ── Stage 2: Resolve queue/caption context ────────────────────
    if caption_draft_id and queue_item_id:
        # Both provided — verify consistency
        from src.caption_approval import DraftsManager
        dm = DraftsManager()
        draft = dm.get(caption_draft_id)
        if draft and draft.queue_id != queue_item_id:
            result.status = MissionPipelineStatus.BLOCKED
            result.block_reason = MissionPipelineBlockReason.ID_MISMATCH
            result.add_warning(f"Caption draft queue_id ({draft.queue_id}) != queue_item_id ({queue_item_id})")
            return result

    resolved_queue_id: Optional[str] = queue_item_id
    resolved_caption_id: Optional[str] = caption_draft_id

    # Resolve caption → queue
    if caption_draft_id and not queue_item_id:
        from src.caption_approval import DraftsManager
        dm = DraftsManager()
        draft = dm.get(caption_draft_id)
        if draft:
            resolved_queue_id = draft.queue_id
            result.caption_draft_id = caption_draft_id
            result.add_evidence("caption_draft", caption_draft_id, "Legenda fornecida")
        else:
            result.add_warning("CAPTION_DRAFT_NOT_FOUND")

    # Resolve queue → caption
    if resolved_queue_id and not caption_draft_id:
        from src.caption_approval import DraftsManager
        dm = DraftsManager()
        drafts = dm.list_all()
        for d in drafts:
            if d.queue_id == resolved_queue_id:
                resolved_caption_id = d.draft_id
                result.caption_draft_id = d.draft_id
                result.add_evidence("caption_draft", d.draft_id, f"Legenda encontrada (status={d.status})")
                break

    if not resolved_queue_id:
        result.status = MissionPipelineStatus.BLOCKED
        result.block_reason = MissionPipelineBlockReason.QUEUE_CONTEXT_REQUIRED
        result.add_warning("Nenhum queue_item_id ou caption_draft_id fornecido/encontrado")
        return result

    result.queue_item_id = resolved_queue_id

    # Checkpoint: contexto resolvido
    _emit_event(repo, result, mission_id, "evidence_recorded", "pipeline",
               {"evidence_type": "context_resolved",
                "queue_item_id": resolved_queue_id,
                "caption_draft_id": resolved_caption_id,
                "how": "Contexto queue/caption resolvido — pipeline pronto para executar"})

    # Light tool availability check (P0.8)
    dry_run_tool = get_tool_availability("publisher_local_dry_run")
    if dry_run_tool is None:
        result.add_warning("Tool Registry: publisher_local_dry_run nao registrado. Execute 'tools discover'.")
    elif dry_run_tool.status == "blocked":
        result.add_warning(f"Tool Registry: publisher_local_dry_run esta {dry_run_tool.status}.")
    elif dry_run_tool.status != "dry_run":
        result.add_warning(f"Tool Registry: publisher_local_dry_run status={dry_run_tool.status}, esperado dry_run.")

    # ── Stage 3: Check caption approval status ────────────────────
    if resolved_caption_id:
        from src.caption_approval import DraftsManager
        dm = DraftsManager()
        draft = dm.get(resolved_caption_id)
        if draft:
            if draft.status == "draft":
                result.status = MissionPipelineStatus.BLOCKED
                result.block_reason = MissionPipelineBlockReason.CAPTION_NOT_SUBMITTED
                result.add_warning("CAPTION_NOT_SUBMITTED — legenda ainda é draft")
                _emit_event(repo, result, mission_id, "error_logged", "pipeline",
                           {"error": result.block_reason, "stage": "caption_check"})
                return result

            if draft.status == "rejected":
                result.status = MissionPipelineStatus.BLOCKED
                result.block_reason = MissionPipelineBlockReason.CAPTION_REJECTED
                result.add_warning("CAPTION_REJECTED — legenda foi rejeitada")
                _emit_event(repo, result, mission_id, "error_logged", "pipeline",
                           {"error": result.block_reason, "stage": "caption_check"})
                return result

            if draft.status in ("needs_review", "revised"):
                # Check if already waiting_approval — don't duplicate
                if current_state.status == MissionStatus.WAITING_APPROVAL:
                    result.status = MissionPipelineStatus.WAITING_APPROVAL
                    result.add_warning("Aguardando aprovação de legenda (já em waiting_approval)")
                    result.add_evidence("caption_draft", resolved_caption_id, f"Aguardando aprovação (status={draft.status})")
                    return result

                # First time — emit events
                _emit_event(repo, result, mission_id, "mission_started", "pipeline",
                           {"contract_title": contract.title}) if current_state.status == MissionStatus.DRAFT else None
                if current_state.status == MissionStatus.DRAFT:
                    pass  # mission_started above

                _emit_event(repo, result, mission_id, "approval_requested", "pipeline",
                           {"caption_draft_id": resolved_caption_id, "status": draft.status})
                result.status = MissionPipelineStatus.WAITING_APPROVAL
                result.add_warning(f"Legenda em {draft.status} — approval_requested")
                result.add_evidence("caption_draft", resolved_caption_id, f"Aguardando aprovação (status={draft.status})")
                return result

    # ── Stage 4: Execute pipeline ──────────────────────────────────
    # Checkpoint pré-execução
    checkpoint_mission(mission_id, repo, label="pre-pipeline-execution")

    # Emit mission_started if first time
    if current_state.status == MissionStatus.DRAFT:
        _emit_event(repo, result, mission_id, "mission_started", "pipeline",
                   {"contract_title": contract.title})

    # Emit step_started
    _emit_event(repo, result, mission_id, "step_started", "pipeline",
               {"step_id": "pipeline_execution", "queue_item_id": resolved_queue_id})

    # Delegate to existing PipelineLocalService
    service = PipelineLocalService()
    pipeline_result = service.run_local_content_pipeline(resolved_queue_id)

    # Map pipeline results
    result.creative_brief_id = pipeline_result.creative_brief_id
    result.export_package_path = pipeline_result.export_package_path
    result.publisher_draft_id = pipeline_result.publisher_draft_id

    for w in pipeline_result.warnings:
        result.add_warning(w)
    for e in pipeline_result.evidence_refs:
        if isinstance(e, str):
            result.add_evidence("ref", e)
        elif isinstance(e, dict):
            result.add_evidence(e.get("type", "ref"), e.get("ref", str(e)))

    # ── Stage 5: Map pipeline result to mission events ─────────────
    if pipeline_result.status in (PipelineRunStatus.SUCCESS, PipelineRunStatus.SUCCESS_WITH_WARNINGS):
        # Emit artifacts
        artifacts_payload: dict = {"artifacts": []}
        if pipeline_result.export_package_path:
            artifacts_payload["artifacts"].append({
                "path": pipeline_result.export_package_path,
                "artifact_type": "export_package",
                "description": "Pacote criativo exportado",
            })
        if pipeline_result.publisher_draft_id:
            artifacts_payload["artifacts"].append({
                "path": f"data/publisher_store/{pipeline_result.publisher_draft_id}",
                "artifact_type": "publisher_draft",
                "description": "Draft local de publicação",
            })
        if pipeline_result.creative_brief_id:
            artifacts_payload["artifacts"].append({
                "path": f"data/creative_briefs/{pipeline_result.creative_brief_id}",
                "artifact_type": "creative_brief",
                "description": "Brief criativo",
            })
        if artifacts_payload["artifacts"]:
            _emit_event(repo, result, mission_id, "artifact_produced", "pipeline", artifacts_payload)

        # Step completed
        _emit_event(repo, result, mission_id, "step_completed", "pipeline",
                   {"step_id": "pipeline_execution", "warnings": pipeline_result.warnings})

        # Mission completed
        _emit_event(repo, result, mission_id, "mission_completed", "pipeline", {})

        result.status = MissionPipelineStatus.SUCCESS
        if pipeline_result.warnings:
            result.add_evidence("status", "success_with_warnings", f"{len(pipeline_result.warnings)} warnings")

    elif pipeline_result.status == PipelineRunStatus.BLOCKED:
        _emit_event(repo, result, mission_id, "error_logged", "pipeline",
                   {"error": pipeline_result.block_reason or "PIPELINE_BLOCKED", "stage": "pipeline_execution"})
        result.status = MissionPipelineStatus.BLOCKED
        result.block_reason = pipeline_result.block_reason
    else:
        _emit_event(repo, result, mission_id, "error_logged", "pipeline",
                   {"error": "PIPELINE_FAILED", "stage": "pipeline_execution"})
        _emit_event(repo, result, mission_id, "mission_failed", "pipeline",
                   {"reason": "Pipeline execution failed"})
        result.status = MissionPipelineStatus.FAILED

    result.finished_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return result


def _emit_event(
    repo: MissionRepository,
    result: MissionPipelineResult,
    mission_id: str,
    event_type: EventType,
    actor: str,
    payload: dict,
) -> EventEnvelope:
    """Helper: cria evento e registra no repo + result."""
    event = EventEnvelope(
        mission_id=mission_id,
        event_type=event_type,
        sequence=0,  # repo calcula
        actor=actor,
        actor_detail="mission-pipeline",
        payload=payload,
    )
    appended = repo.append_event(event)
    result.add_event(appended.idempotency_key)
    result.add_evidence("event", appended.idempotency_key, event_type)
    return appended


def get_mission_pipeline_status(
    mission_id: str,
    repo: Optional[MissionRepository] = None,
) -> dict:
    """Retorna status combinado: TaskState + sugestão de próximo passo."""
    repo = repo or JsonlRepository()
    try:
        state = repo.project(mission_id)
    except Exception:
        return {"status": "not_found", "mission_id": mission_id}

    next_action = None
    if state.status == MissionStatus.WAITING_APPROVAL:
        next_action = f"Aguardando aprovação. Após aprovar, rode: python jarvis.py pipeline mission-run {mission_id[:12]}"
    elif state.status == MissionStatus.DRAFT:
        next_action = f"Missão em rascunho. Execute: python jarvis.py pipeline mission-run {mission_id[:12]}"
    elif state.status == MissionStatus.RUNNING:
        next_action = "Missão em execução."
    elif state.status == MissionStatus.COMPLETED:
        next_action = "Missão concluída."
    elif state.status == MissionStatus.FAILED:
        next_action = "Missão falhou. Crie nova missão com --parent se quiser reexecutar."
    elif state.status == MissionStatus.CANCELLED:
        next_action = "Missão cancelada. Crie nova missão se necessário."

    return {
        "mission_id": mission_id,
        "title": state.contract_title,
        "sector": state.sector,
        "status": state.status.value,
        "cumulative_tokens": state.cumulative_tokens,
        "cumulative_cost_usd": state.cumulative_cost_usd,
        "last_event_sequence": state.last_event_sequence,
        "last_updated": state.last_updated.isoformat() if hasattr(state.last_updated, "isoformat") else str(state.last_updated),
        "pending_approval": state.approval_pending,
        "errors": state.errors[-3:] if state.errors else [],
        "next_action": next_action,
    }
