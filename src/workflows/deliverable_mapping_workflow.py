"""DeliverableMappingWorkflow — text → MissionIntake → DeliverableManifest lote → akasha.

Onda 26: encadeia MissionIntake + DeliverableMapper para processar N descrições
de missão em texto livre e produzir os manifestos de deliverables esperados.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from src.agentic.mission_intake import MissionIntake, MissionIntakeResult
from src.agentic.deliverable_mapper import DeliverableMapper, DeliverableManifest
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.deliverable_mapping")

_COST_LOCAL_PCT = 100


@dataclass
class MissionDeliverable:
    """Par intake + manifesto para uma missão processada."""
    intake: MissionIntakeResult
    manifest: DeliverableManifest

    @property
    def deliverables_count(self) -> int:
        return len(self.manifest.deliverables)

    @property
    def sector(self) -> str:
        return self.intake.setor

    def to_dict(self) -> dict:
        return {
            "setor": self.intake.setor,
            "tipo": self.intake.tipo,
            "risco": self.intake.risco,
            "deliverables_count": self.deliverables_count,
            "export_hint": self.manifest.export_hint,
        }


@dataclass
class DeliverableMappingResult:
    run_id: str
    success: bool
    missions_count: int
    results: list[MissionDeliverable]
    total_deliverables: int
    sectors: list[str]
    akasha_event_id: str
    dry_run: bool
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None

    @property
    def unique_sectors(self) -> int:
        return len(set(self.sectors))

    @property
    def high_risk_count(self) -> int:
        return sum(1 for r in self.results if r.intake.risco == "alto")

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "missions_count": self.missions_count,
            "total_deliverables": self.total_deliverables,
            "unique_sectors": self.unique_sectors,
            "high_risk_count": self.high_risk_count,
            "sectors": self.sectors,
            "akasha_event_id": self.akasha_event_id,
            "cost_local_pct": self.cost_local_pct,
        }


class DeliverableMappingWorkflow:
    """Processa descrições de missões e produz manifestos de deliverables."""

    def __init__(
        self,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/deliverable_mapping/",
    ) -> None:
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)

    def run(
        self,
        mission_texts: list[str],
        dry_run: bool = True,
    ) -> DeliverableMappingResult:
        """Parse textos → intake → manifesto de deliverables por missão.

        Args:
            mission_texts: lista de textos livres descrevendo missões.
            dry_run: se True, marca resultado como simulação.

        Returns:
            DeliverableMappingResult com todos os manifestos.
        """
        ctx = RunContext.new(budget_usd=0.0)

        if not mission_texts:
            _logger.warning("deliverable_mapping[%s]: empty mission_texts", ctx.run_id)
            return DeliverableMappingResult(
                run_id=ctx.run_id,
                success=False,
                missions_count=0,
                results=[],
                total_deliverables=0,
                sectors=[],
                akasha_event_id="",
                dry_run=dry_run,
                error="empty_missions",
            )

        intake_parser = MissionIntake()
        mapper = DeliverableMapper()
        results: list[MissionDeliverable] = []
        sectors: list[str] = []

        for text in mission_texts:
            intake = intake_parser.parse(text)
            manifest = mapper.map(intake)
            results.append(MissionDeliverable(intake=intake, manifest=manifest))
            sectors.append(intake.setor)
            _logger.debug(
                "deliverable_mapping[%s]: setor=%s tipo=%s deliverables=%d",
                ctx.run_id, intake.setor, intake.tipo, len(manifest.deliverables),
            )

        total_deliverables = sum(r.deliverables_count for r in results)
        unique_sectors = len(set(sectors))
        _logger.info(
            "deliverable_mapping[%s]: %d missions, %d total deliverables, %d sectors",
            ctx.run_id, len(mission_texts), total_deliverables, unique_sectors,
        )

        event = SinkEvent(
            event_type="deliverables_mapped",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "missions_count": len(mission_texts),
                "total_deliverables": total_deliverables,
                "unique_sectors": unique_sectors,
                "sectors": sectors,
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return DeliverableMappingResult(
            run_id=ctx.run_id,
            success=True,
            missions_count=len(mission_texts),
            results=results,
            total_deliverables=total_deliverables,
            sectors=sectors,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
        )
