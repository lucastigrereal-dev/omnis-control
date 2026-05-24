"""SquadAssignmentWorkflow — atribui squads a N missões → akasha.

Onda 25: envolve SquadSelector para processar lote de missões, atribuindo
o squad especializado correto para cada setor detectado.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from src.agentic.squad_selector import SquadSelector, SquadAssignment
from src.akasha_event_sink.adapter import AkashaSinkAdapter
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.squad_assignment")

_COST_LOCAL_PCT = 100


@dataclass
class SquadAssignmentResult:
    run_id: str
    success: bool
    missions_count: int
    assignments: list[SquadAssignment]
    squads_used: list[str]
    akasha_event_id: str
    dry_run: bool
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None

    @property
    def unique_squads(self) -> int:
        return len(set(self.squads_used))

    @property
    def fallback_count(self) -> int:
        return sum(1 for s in self.squads_used if s == "SQD-GEN")

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "missions_count": self.missions_count,
            "unique_squads": self.unique_squads,
            "fallback_count": self.fallback_count,
            "squads_used": self.squads_used,
            "akasha_event_id": self.akasha_event_id,
            "cost_local_pct": self.cost_local_pct,
        }


class SquadAssignmentWorkflow:
    """Atribui squad especializado a cada missão do lote, emite snapshot akasha."""

    def __init__(self, akasha_sink=None) -> None:
        self._sink = akasha_sink or AkashaSinkAdapter()

    def run(
        self,
        missions: list[dict],
        dry_run: bool = True,
    ) -> SquadAssignmentResult:
        """Processa lote de missões e atribui squads.

        Args:
            missions: lista de dicts com keys: mission_id (str), sector (str).
            dry_run: se True, marca resultado como simulação.

        Returns:
            SquadAssignmentResult com todas as atribuições.
        """
        ctx = RunContext.new(budget_usd=0.0)

        if not missions:
            _logger.warning("squad_assignment[%s]: empty missions list", ctx.run_id)
            return SquadAssignmentResult(
                run_id=ctx.run_id,
                success=False,
                missions_count=0,
                assignments=[],
                squads_used=[],
                akasha_event_id="",
                dry_run=dry_run,
                error="empty_missions",
            )

        selector = SquadSelector()
        assignments: list[SquadAssignment] = []
        squads_used: list[str] = []

        for mission in missions:
            mission_id = mission.get("mission_id", "")
            sector = mission.get("sector", "general")
            assignment = selector.assign(mission_id, sector)
            assignments.append(assignment)
            squads_used.append(assignment.squad.squad_id)
            _logger.debug(
                "squad_assignment[%s]: %s → %s",
                ctx.run_id, mission_id, assignment.squad.squad_id,
            )

        unique_squads = len(set(squads_used))
        _logger.info(
            "squad_assignment[%s]: %d missions assigned, %d unique squads",
            ctx.run_id, len(missions), unique_squads,
        )

        event = SinkEvent(
            event_type="squad_assignments_generated",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "missions_count": len(missions),
                "unique_squads": unique_squads,
                "squads_used": squads_used,
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return SquadAssignmentResult(
            run_id=ctx.run_id,
            success=True,
            missions_count=len(missions),
            assignments=assignments,
            squads_used=squads_used,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
        )
