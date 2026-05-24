"""MissionOrchestrator — orquestra missão ponta a ponta: brief → agency → workflow → akasha.

Onda 14 — conecta todos os organismos construídos nas Ondas 10-13:
  - MissionContract / MissionEngine  → ciclo de vida da missão
  - AgencyRegistry                   → roteia missão para a agência certa
  - WorkflowRegistry                 → executa o workflow adequado
  - RunContext                       → run_id único por orquestração
  - AkashaSinkAdapter                → persiste resultado com run_id

Pipeline:
  1. brief       → cria MissionContract (MissionEngine)
  2. route_agency → AgencyRegistry.route_mission() → AcceptResult
  3. run_workflow → WorkflowRegistry.run(wf_name, **wf_kwargs) → workflow result
  4. akasha      → evento com run_id, mission_id, workflow_name, success
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.agentic.agency import Agency, AgencyRegistry
from src.agentic.mission_engine import MissionContract, MissionEngine
from src.workflows.workflow_registry import WorkflowRegistry
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.agentic.orchestrator")


# ── MissionBrief ──────────────────────────────────────────────────────────────

@dataclass
class MissionBrief:
    """Entrada simplificada para o orquestrador."""
    objetivo: str
    setor: str
    workflow_name: str
    workflow_kwargs: dict[str, Any] = field(default_factory=dict)
    criado_por: str = "orchestrator"


# ── OrchestrationResult ───────────────────────────────────────────────────────

@dataclass
class OrchestrationResult:
    """Resultado consolidado de uma orquestração completa."""
    run_id: str
    mission_id: str
    success: bool
    setor: str
    workflow_name: str
    workflow_result: Any = None
    agency_id: str = ""
    squad_id: str = ""
    akasha_event_id: str = ""
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        wf_dict = {}
        if hasattr(self.workflow_result, "to_dict"):
            wf_dict = self.workflow_result.to_dict()
        elif isinstance(self.workflow_result, dict):
            wf_dict = self.workflow_result

        return {
            "run_id": self.run_id,
            "mission_id": self.mission_id,
            "success": self.success,
            "setor": self.setor,
            "workflow_name": self.workflow_name,
            "agency_id": self.agency_id,
            "squad_id": self.squad_id,
            "akasha_event_id": self.akasha_event_id,
            "workflow_result": wf_dict,
            "error": self.error,
        }


# ── MissionOrchestrator ───────────────────────────────────────────────────────

class MissionOrchestrator:
    """Orquestra missão ponta a ponta: brief → agency → workflow → akasha.

    Injeção de dependências para testes:
      agency_registry   → AgencyRegistry (default: vazio)
      workflow_registry → WorkflowRegistry (default: WorkflowRegistry.default())
      mission_engine    → MissionEngine (default: instância padrão)
      akasha_sink       → AkashaSinkAdapter (default: FileAkashaSink dry_run=True)
    """

    def __init__(
        self,
        agency_registry: AgencyRegistry | None = None,
        workflow_registry: WorkflowRegistry | None = None,
        mission_engine: MissionEngine | None = None,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/orchestrator/",
    ) -> None:
        self._agencies = agency_registry or AgencyRegistry()
        self._workflows = workflow_registry or WorkflowRegistry.default()
        self._engine = mission_engine or MissionEngine()
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)

    def orchestrate(self, brief: MissionBrief) -> OrchestrationResult:
        """Executa o pipeline completo para um MissionBrief."""
        ctx = RunContext.new()
        _logger.info(
            "%s MissionOrchestrator.orchestrate: setor=%s, wf=%s",
            ctx.log_prefix(), brief.setor, brief.workflow_name,
        )

        # Passo 1 — Criar contrato de missão
        contract = MissionContract(
            mission_id=f"MSN-{ctx.run_id[:8]}",
            timestamp=RunContext.new().log_prefix(),
            status="open",
            setor=brief.setor,
            objetivo=brief.objetivo,
            criado_por=brief.criado_por,
        )
        _logger.info("%s mission contract: %s", ctx.log_prefix(), contract.mission_id)

        # Passo 2 — Rotear para agência
        accept = self._agencies.route_mission(contract)
        agency_id = ""
        squad_id = ""
        if accept is not None:
            if not accept.accepted:
                _logger.warning(
                    "%s agency rejected mission %s: %s",
                    ctx.log_prefix(), contract.mission_id, accept.error,
                )
                return OrchestrationResult(
                    run_id=ctx.run_id,
                    mission_id=contract.mission_id,
                    success=False,
                    setor=brief.setor,
                    workflow_name=brief.workflow_name,
                    error=accept.error,
                )
            agency_id = accept.agency_id
            squad_id = accept.squad_assignment.squad.squad_id if accept.squad_assignment else ""
            _logger.info(
                "%s agency %s accepted → squad %s",
                ctx.log_prefix(), agency_id, squad_id,
            )

        # Passo 3 — Executar workflow
        try:
            wf_result = self._workflows.run(brief.workflow_name, **brief.workflow_kwargs)
        except KeyError:
            _logger.error("%s workflow '%s' not found", ctx.log_prefix(), brief.workflow_name)
            return OrchestrationResult(
                run_id=ctx.run_id,
                mission_id=contract.mission_id,
                success=False,
                setor=brief.setor,
                workflow_name=brief.workflow_name,
                agency_id=agency_id,
                squad_id=squad_id,
                error=f"workflow_not_found: {brief.workflow_name}",
            )
        except Exception as exc:
            _logger.error("%s workflow error: %s", ctx.log_prefix(), exc)
            return OrchestrationResult(
                run_id=ctx.run_id,
                mission_id=contract.mission_id,
                success=False,
                setor=brief.setor,
                workflow_name=brief.workflow_name,
                agency_id=agency_id,
                squad_id=squad_id,
                error=f"workflow_error: {exc}",
            )

        _logger.info("%s workflow '%s' completed OK", ctx.log_prefix(), brief.workflow_name)

        # Passo 4 — Completar missão na agência
        if accept is not None and accept.accepted:
            agency = self._agencies.get(agency_id)
            if agency:
                agency.complete_mission(contract.mission_id)

        # Passo 5 — Gravar no akasha
        wf_success = getattr(wf_result, "success", True)
        event = SinkEvent(
            event_type="orchestration_completed",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "mission_id": contract.mission_id,
                "setor": brief.setor,
                "objetivo": brief.objetivo[:200],
                "workflow_name": brief.workflow_name,
                "agency_id": agency_id,
                "squad_id": squad_id,
                "workflow_success": wf_success,
            },
        )
        self._sink.write_event(event)

        return OrchestrationResult(
            run_id=ctx.run_id,
            mission_id=contract.mission_id,
            success=bool(wf_success),
            setor=brief.setor,
            workflow_name=brief.workflow_name,
            workflow_result=wf_result,
            agency_id=agency_id,
            squad_id=squad_id,
            akasha_event_id=event.event_id,
            artifacts={
                "run_id": ctx.run_id,
                "akasha_event_id": event.event_id,
            },
        )
