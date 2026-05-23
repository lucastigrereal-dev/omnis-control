"""Planner — builds orchestration steps from a request.

Deterministic. No LLM. No network. Uses mission_builder intent detection.
"""
from __future__ import annotations

from pathlib import Path

from src.mission_orchestrator.models import (
    OrchestratorRun,
    OrchestratorStep,
    RUN_STATUS_PLANNED,
    RUN_STATUS_BLOCKED,
)
from src.mission_orchestrator.errors import UnknownIntentError
from src.utils.dry_run import resolve_dry_run


def _parse_intent(
    request_text: str,
    config_path: Path | None = None,
) -> tuple[str, str, str]:
    from src.mission_builder.intent import detect_intent

    kwargs: dict[str, Path] = {}
    if config_path is not None:
        kwargs["config_path"] = config_path
    return detect_intent(request_text, **kwargs)


def _match_capabilities(request_text: str) -> tuple[list[object], object | None]:
    from src.skill_matcher.matcher import match_capabilities
    from src.sector_registry.matcher import match_sector

    return match_capabilities(request_text), match_sector(request_text)


def _validate_plan(
    request_text: str,
    intent: str,
    cap_results: list[object],
    allow_unknown: bool,
) -> None:
    if intent == "unknown" and not cap_results and not allow_unknown:
        raise UnknownIntentError(
            f"Intent desconhecido para: '{request_text}'. "
            "Tente mencionar: carrossel, reels, campanha, post, stories."
        )


def _apply_capability_intelligence(
    run: OrchestratorRun,
    request_text: str,
    cap_results: list[object],
    sector_result: object | None,
) -> None:
    run.sector_id = sector_result.sector_id if sector_result else "unknown"
    run.matched_capabilities = [capability.capability_id for capability in cap_results]

    if cap_results:
        run.approval_required = any(
            capability.risk_level in ("medium", "high")
            for capability in cap_results
        )
        return

    from src.capability_gap.detector import detect as detect_gap
    gap_result = detect_gap(request_text)
    run.suggested_gap_ids = [gap.gap_id for gap in gap_result.gaps]
    run.approval_required = any(
        gap.risk_level in ("medium", "high") for gap in gap_result.gaps
    )


def _build_steps(request_text: str, dry_run: bool) -> list[OrchestratorStep]:
    return [
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
        OrchestratorStep(
            step_id="s06",
            label="Compor squad a partir do request",
            module="squad_composer",
            command=f"jarvis squad compose \"{request_text}\"",
            status="pending" if not dry_run else "pending",
        ),
        OrchestratorStep(
            step_id="s07",
            label="Construir e executar grafo de passos",
            module="execution_graph",
            command=f"jarvis graph build \"{request_text}\"",
            status="pending" if not dry_run else "pending",
        ),
    ]


def build_plan(
    request_text: str,
    account_handle: str = "",
    objective: str = "engajamento",
    dry_run: bool | None = None,
    allow_unknown: bool = False,
    config_path: Path | None = None,
) -> OrchestratorRun:
    """Build an OrchestratorRun with planned steps. No execution."""
    dry_run = resolve_dry_run(dry_run)
    intent, _deliverable, _description = _parse_intent(request_text, config_path)

    # P5.0 — wire P4 sector/capability/gap intelligence
    cap_results, sector_result = _match_capabilities(request_text)

    # Raise only when intent is unknown AND no capability covers the request
    _validate_plan(request_text, intent, cap_results, allow_unknown)

    run = OrchestratorRun.new(
        request_text=request_text,
        account_handle=account_handle,
        objective=objective,
        dry_run=dry_run,
        intent=intent,
    )

    # Populate P4 intelligence fields
    _apply_capability_intelligence(run, request_text, cap_results, sector_result)

    run.steps = _build_steps(request_text, dry_run)
    run.status = RUN_STATUS_PLANNED
    return run
