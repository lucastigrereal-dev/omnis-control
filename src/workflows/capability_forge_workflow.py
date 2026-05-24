"""CapabilityForgeWorkflow — detecta gaps + forja skills → akasha.

Onda 28: envolve ForgeOrchestrator para processar N missões com skills
faltantes, detectar gaps de capacidade e gerar ForgeResults (dry_run).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from src.agentic.forge_orchestrator import ForgeOrchestrator, GapReport, ForgeResult
from src.akasha_event_sink.adapter import AkashaSinkAdapter
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.capability_forge")

_COST_LOCAL_PCT = 100


@dataclass
class MissionForgeResult:
    """Gaps + results de forge para uma missão."""
    mission_id: str
    sector: str
    gaps: list[GapReport]
    forge_results: list[ForgeResult]

    @property
    def gaps_count(self) -> int:
        return len(self.gaps)

    @property
    def all_successful(self) -> bool:
        return all(r.success for r in self.forge_results)


@dataclass
class CapabilityForgeResult:
    run_id: str
    success: bool
    missions_count: int
    total_gaps: int
    total_forge_results: int
    high_severity_gaps: int
    mission_results: list[MissionForgeResult]
    akasha_event_id: str
    dry_run: bool
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None

    @property
    def all_successful(self) -> bool:
        return all(mr.all_successful for mr in self.mission_results)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "missions_count": self.missions_count,
            "total_gaps": self.total_gaps,
            "total_forge_results": self.total_forge_results,
            "high_severity_gaps": self.high_severity_gaps,
            "all_successful": self.all_successful,
            "akasha_event_id": self.akasha_event_id,
            "cost_local_pct": self.cost_local_pct,
        }


class CapabilityForgeWorkflow:
    """Detecta gaps de skill e gera ForgeResults para N missões."""

    def __init__(self, akasha_sink=None) -> None:
        self._sink = akasha_sink or AkashaSinkAdapter()

    def run(
        self,
        missions: list[dict],
        dry_run: bool = True,
    ) -> CapabilityForgeResult:
        """Detecta gaps e forja skills para cada missão do lote.

        Args:
            missions: lista de dicts com keys: mission_id (str), sector (str),
                      missing_skills (list[str]), deliverables (list[str]).
            dry_run: se True, ForgeOrchestrator opera em modo simulação.

        Returns:
            CapabilityForgeResult com todos os gaps e forge results.
        """
        ctx = RunContext.new(budget_usd=0.0)

        if not missions:
            _logger.warning("capability_forge[%s]: empty missions list", ctx.run_id)
            return CapabilityForgeResult(
                run_id=ctx.run_id,
                success=False,
                missions_count=0,
                total_gaps=0,
                total_forge_results=0,
                high_severity_gaps=0,
                mission_results=[],
                akasha_event_id="",
                dry_run=dry_run,
                error="empty_missions",
            )

        orchestrator = ForgeOrchestrator(dry_run=dry_run)
        mission_results: list[MissionForgeResult] = []

        for mission in missions:
            mission_id = mission.get("mission_id", "")
            sector = mission.get("sector", "general")
            missing_skills: list[str] = mission.get("missing_skills", [])
            deliverables: list[str] = mission.get("deliverables", [])

            gaps = orchestrator.detect_gaps(
                mission_id=mission_id,
                sector=sector,
                missing_skills=missing_skills,
                deliverables=deliverables,
            )
            forge_results: list[ForgeResult] = []
            for gap in gaps:
                result = orchestrator.forge(gap, output_dir=None)
                forge_results.append(result)

            mission_results.append(MissionForgeResult(
                mission_id=mission_id,
                sector=sector,
                gaps=gaps,
                forge_results=forge_results,
            ))
            _logger.debug(
                "capability_forge[%s]: %s → %d gaps, %d forge",
                ctx.run_id, mission_id, len(gaps), len(forge_results),
            )

        total_gaps = sum(mr.gaps_count for mr in mission_results)
        total_forge = sum(len(mr.forge_results) for mr in mission_results)
        high_severity = sum(
            1 for mr in mission_results
            for g in mr.gaps
            if g.severity == "high"
        )

        _logger.info(
            "capability_forge[%s]: %d missions, %d gaps (%d high), %d forge",
            ctx.run_id, len(missions), total_gaps, high_severity, total_forge,
        )

        event = SinkEvent(
            event_type="capability_gaps_detected",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "missions_count": len(missions),
                "total_gaps": total_gaps,
                "high_severity_gaps": high_severity,
                "total_forge_results": total_forge,
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return CapabilityForgeResult(
            run_id=ctx.run_id,
            success=True,
            missions_count=len(missions),
            total_gaps=total_gaps,
            total_forge_results=total_forge,
            high_severity_gaps=high_severity,
            mission_results=mission_results,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
        )
