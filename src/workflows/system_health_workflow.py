"""SystemHealthWorkflow — health check diário do sistema OMNIS.

Onda 15 — consolida saúde de todos os organismos construídos nas Ondas 10-14:
  - WorkflowRegistry.health_check_all()  → workflows importáveis
  - AgencyRegistry.get_health_report()   → agências e cargas
  - RunContext                           → run_id do snapshot
  - AkashaSinkAdapter                    → persiste snapshot para trend tracking

Resultado:
  - overall_ok: True se todos os checks passam
  - workflows_ok: todos os 4 workflows importáveis
  - agencies: lista de saúde das agências registradas
  - snapshots salvos no akasha para histórico de tendência

Uso típico (relatório matinal):
  wf = SystemHealthWorkflow.default()
  result = wf.run(dry_run=True)
  print(result.to_dict())
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.workflows.workflow_registry import WorkflowHealthReport, WorkflowRegistry
from src.agentic.agency import AgencyRegistry
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.system_health")

_COST_LOCAL_PCT = 100


@dataclass
class SystemHealthResult:
    """Snapshot de saúde consolidada do sistema OMNIS."""

    run_id: str
    overall_ok: bool
    workflows_ok: bool
    workflows_total: int
    workflows_importable: int
    workflows_failed: int
    agencies_total: int
    agencies_active: int
    agencies_saturated: int
    akasha_event_id: str = ""
    dry_run: bool = True
    cost_local_pct: int = _COST_LOCAL_PCT
    workflow_details: list[dict[str, Any]] = field(default_factory=list)
    agency_details: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    @property
    def summary(self) -> str:
        status = "OK" if self.overall_ok else "DEGRADED"
        return (
            f"[{status}] Workflows: {self.workflows_importable}/{self.workflows_total} ok | "
            f"Agencies: {self.agencies_total} total, {self.agencies_active} active"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "overall_ok": self.overall_ok,
            "workflows_ok": self.workflows_ok,
            "workflows_total": self.workflows_total,
            "workflows_importable": self.workflows_importable,
            "workflows_failed": self.workflows_failed,
            "agencies_total": self.agencies_total,
            "agencies_active": self.agencies_active,
            "agencies_saturated": self.agencies_saturated,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "summary": self.summary,
            "workflow_details": self.workflow_details,
            "agency_details": self.agency_details,
            "error": self.error,
        }


class SystemHealthWorkflow:
    """Health check diário: consolida WorkflowRegistry + AgencyRegistry → akasha."""

    def __init__(
        self,
        workflow_registry: WorkflowRegistry | None = None,
        agency_registry: AgencyRegistry | None = None,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/health/",
    ) -> None:
        self._workflows = workflow_registry or WorkflowRegistry()
        self._agencies = agency_registry or AgencyRegistry()
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)

    def run(self, dry_run: bool = True) -> SystemHealthResult:
        """Executa health check e retorna snapshot consolidado."""
        ctx = RunContext.new()
        _logger.info("%s SystemHealthWorkflow.run: dry_run=%s", ctx.log_prefix(), dry_run)

        # Check 1 — Workflows
        wf_report: WorkflowHealthReport = self._workflows.health_check_all()
        _logger.info(
            "%s workflows: %d/%d ok",
            ctx.log_prefix(), wf_report.importable, wf_report.total,
        )

        # Check 2 — Agencies
        agency_report = self._agencies.get_health_report()
        agencies_active = sum(1 for a in agency_report if a.get("status") == "active")
        agencies_saturated = sum(1 for a in agency_report if a.get("status") == "saturated")
        _logger.info(
            "%s agencies: %d total, %d active, %d saturated",
            ctx.log_prefix(), len(agency_report), agencies_active, agencies_saturated,
        )

        overall_ok = wf_report.all_ok

        # Gravar snapshot no akasha
        event = SinkEvent(
            event_type="system_health_snapshot",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "overall_ok": overall_ok,
                "workflows_ok": wf_report.all_ok,
                "workflows_total": wf_report.total,
                "workflows_importable": wf_report.importable,
                "agencies_total": len(agency_report),
                "agencies_active": agencies_active,
                "cost_local_pct": _COST_LOCAL_PCT,
                "dry_run": dry_run,
            },
        )
        written = self._sink.write_event(event)
        _logger.info("%s akasha health snapshot: event_id=%s, ok=%s", ctx.log_prefix(), event.event_id, written)

        return SystemHealthResult(
            run_id=ctx.run_id,
            overall_ok=overall_ok,
            workflows_ok=wf_report.all_ok,
            workflows_total=wf_report.total,
            workflows_importable=wf_report.importable,
            workflows_failed=wf_report.failed,
            agencies_total=len(agency_report),
            agencies_active=agencies_active,
            agencies_saturated=agencies_saturated,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
            cost_local_pct=_COST_LOCAL_PCT,
            workflow_details=wf_report.entries,
            agency_details=agency_report,
        )

    @classmethod
    def default(cls) -> "SystemHealthWorkflow":
        """Instância padrão com WorkflowRegistry.default() pré-carregado."""
        return cls(workflow_registry=WorkflowRegistry.default())
