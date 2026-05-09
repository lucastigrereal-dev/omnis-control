"""Planner — builds orchestration steps from a request.

Deterministic. No LLM. No network. Uses mission_builder intent detection.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.mission_orchestrator.models import (
    OrchestratorRun,
    OrchestratorStep,
    RUN_STATUS_PLANNED,
    RUN_STATUS_BLOCKED,
)
from src.mission_orchestrator.errors import UnknownIntentError


def build_plan(
    request_text: str,
    account_handle: str = "",
    objective: str = "engajamento",
    dry_run: bool = True,
    allow_unknown: bool = False,
    config_path: Optional[Path] = None,
) -> OrchestratorRun:
    """Build an OrchestratorRun with planned steps. No execution."""
    from src.mission_builder.intent import detect_intent

    kwargs = {}
    if config_path is not None:
        kwargs["config_path"] = config_path

    intent, deliverable, description = detect_intent(request_text, **kwargs)

    if intent == "unknown" and not allow_unknown:
        raise UnknownIntentError(
            f"Intent desconhecido para: '{request_text}'. "
            "Tente mencionar: carrossel, reels, campanha, post, stories."
        )

    run = OrchestratorRun.new(
        request_text=request_text,
        account_handle=account_handle,
        objective=objective,
        dry_run=dry_run,
        intent=intent,
    )

    steps = [
        OrchestratorStep(
            step_id="s01",
            label="Detectar intent e gerar plano",
            module="mission_builder",
            command=f"jarvis mission-builder plan \"{request_text}\"",
        ),
        OrchestratorStep(
            step_id="s02",
            label="Criar mission package (dry-run)",
            module="mission_builder",
            command=f"jarvis mission-builder run \"{request_text}\" --dry-run",
        ),
        OrchestratorStep(
            step_id="s03",
            label="Importar asset (quando disponível)",
            module="asset_inbox",
            command="jarvis asset-inbox import <arquivo>",
            status="skipped" if dry_run else "pending",
            notes="Executar quando asset local estiver disponível",
        ),
        OrchestratorStep(
            step_id="s04",
            label="Atribuir asset à missão",
            module="asset_inbox",
            command="jarvis asset-inbox assign <asset_id> --mission <mission_id>",
            status="skipped" if dry_run else "pending",
            notes="Executar após importação de asset",
        ),
        OrchestratorStep(
            step_id="s05",
            label="Fechar missão com relatório",
            module="mission_report",
            command="jarvis mission-report close <mission_id> completed",
            status="pending",
            notes="Executar após validação humana",
        ),
    ]

    run.steps = steps
    run.status = RUN_STATUS_PLANNED
    return run
