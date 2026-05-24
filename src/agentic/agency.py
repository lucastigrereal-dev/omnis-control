"""Agency — agência como organismo: coordena squads, aceita missões, reporta saúde.

Onda 11 — wires existing pieces:
  - SquadDefinition / SquadSelector  → squad routing
  - MissionContract                  → mission lifecycle
  - RunContext                       → event run_id
  - AkashaSinkAdapter                → persiste eventos com run_id

Uma Agency é uma unidade coordenada de squads que:
  1. Aceita missões e roteia para o squad certo
  2. Monitora capacidade (satura quando cheia)
  3. Reporta saúde coletiva (active, completed, budget_used)
  4. Emite evento akasha a cada aceitação e conclusão

Pipeline:
  accept_mission(contract) → check_capacity → assign_squad → emit_event → AcceptResult
  complete_mission(id)     → update_state   → emit_event
  get_health()             → AgencyHealth
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.agentic.squad_selector import SquadAssignment, SquadDefinition, SquadSelector
from src.agentic.mission_engine import MissionContract
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.agentic.agency")

# Status constants
AGENCY_ACTIVE = "active"
AGENCY_IDLE = "idle"
AGENCY_SATURATED = "saturated"
AGENCY_CLOSED = "closed"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── AgencyConfig ──────────────────────────────────────────────────────────────

@dataclass
class AgencyConfig:
    """Configuração estática de uma agência."""
    agency_id: str
    name: str
    sector: str
    squads: list[SquadDefinition] = field(default_factory=list)
    capacity: int = 5
    budget_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agency_id": self.agency_id,
            "name": self.name,
            "sector": self.sector,
            "squads": [s.to_dict() for s in self.squads],
            "capacity": self.capacity,
            "budget_usd": self.budget_usd,
        }


# ── AgencyHealth ──────────────────────────────────────────────────────────────

@dataclass
class AgencyHealth:
    """Snapshot de saúde coletiva da agência."""
    agency_id: str
    name: str
    status: str
    active_missions: int
    completed_missions: int
    rejected_missions: int
    capacity: int
    budget_used_usd: float
    budget_total_usd: float
    squad_count: int
    checked_at: str = field(default_factory=_now_iso)

    @property
    def load_pct(self) -> int:
        if self.capacity == 0:
            return 100
        return min(100, int(self.active_missions / self.capacity * 100))

    @property
    def budget_remaining(self) -> float:
        return max(0.0, self.budget_total_usd - self.budget_used_usd)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agency_id": self.agency_id,
            "name": self.name,
            "status": self.status,
            "active_missions": self.active_missions,
            "completed_missions": self.completed_missions,
            "rejected_missions": self.rejected_missions,
            "capacity": self.capacity,
            "load_pct": self.load_pct,
            "budget_used_usd": self.budget_used_usd,
            "budget_total_usd": self.budget_total_usd,
            "budget_remaining": self.budget_remaining,
            "squad_count": self.squad_count,
            "checked_at": self.checked_at,
        }


# ── AcceptResult ──────────────────────────────────────────────────────────────

@dataclass
class AcceptResult:
    """Resultado de accept_mission()."""
    run_id: str
    accepted: bool
    agency_id: str
    mission_id: str
    squad_assignment: SquadAssignment | None = None
    akasha_event_id: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "accepted": self.accepted,
            "agency_id": self.agency_id,
            "mission_id": self.mission_id,
            "squad": self.squad_assignment.squad.squad_id if self.squad_assignment else None,
            "akasha_event_id": self.akasha_event_id,
            "error": self.error,
        }


# ── Agency ────────────────────────────────────────────────────────────────────

class Agency:
    """Agência como organismo: coordena squads, aceita missões, reporta saúde."""

    def __init__(
        self,
        config: AgencyConfig,
        squad_selector: SquadSelector | None = None,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/agencies/",
    ) -> None:
        self._config = config
        self._selector = squad_selector or SquadSelector()
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)

        self._active: dict[str, SquadAssignment] = {}
        self._completed: list[str] = []
        self._rejected: list[str] = []
        self._budget_used: float = 0.0
        self._status: str = AGENCY_IDLE

    @property
    def agency_id(self) -> str:
        return self._config.agency_id

    @property
    def name(self) -> str:
        return self._config.name

    def accept_mission(self, contract: MissionContract) -> AcceptResult:
        """Aceita uma missão, roteia para squad, emite evento akasha."""
        ctx = RunContext.new()
        _logger.info(
            "%s Agency '%s' accept_mission: %s",
            ctx.log_prefix(), self._config.name, contract.mission_id,
        )

        # Capacity check
        if len(self._active) >= self._config.capacity:
            self._rejected.append(contract.mission_id)
            self._update_status()
            _logger.warning(
                "%s Agency '%s' saturated — rejected %s",
                ctx.log_prefix(), self._config.name, contract.mission_id,
            )
            return AcceptResult(
                run_id=ctx.run_id,
                accepted=False,
                agency_id=self.agency_id,
                mission_id=contract.mission_id,
                error="agency_saturated",
            )

        # Route to squad
        assignment = self._selector.assign(contract.mission_id, contract.setor)
        self._active[contract.mission_id] = assignment
        self._update_status()
        _logger.info(
            "%s mission %s assigned to squad %s",
            ctx.log_prefix(), contract.mission_id, assignment.squad.squad_id,
        )

        # Emit akasha event
        event = SinkEvent(
            event_type="agency_mission_accepted",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "agency_id": self.agency_id,
                "agency_name": self._config.name,
                "mission_id": contract.mission_id,
                "setor": contract.setor,
                "squad_id": assignment.squad.squad_id,
                "squad_name": assignment.squad.name,
                "active_count": len(self._active),
                "capacity": self._config.capacity,
                "status": self._status,
            },
        )
        self._sink.write_event(event)

        return AcceptResult(
            run_id=ctx.run_id,
            accepted=True,
            agency_id=self.agency_id,
            mission_id=contract.mission_id,
            squad_assignment=assignment,
            akasha_event_id=event.event_id,
        )

    def complete_mission(self, mission_id: str) -> bool:
        """Marca missão como concluída, libera capacidade, emite evento."""
        if mission_id not in self._active:
            return False

        assignment = self._active.pop(mission_id)
        self._completed.append(mission_id)
        self._update_status()
        _logger.info(
            "Agency '%s' completed mission %s (squad %s)",
            self._config.name, mission_id, assignment.squad.squad_id,
        )

        ctx = RunContext.new()
        event = SinkEvent(
            event_type="agency_mission_completed",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "agency_id": self.agency_id,
                "mission_id": mission_id,
                "squad_id": assignment.squad.squad_id,
                "active_count": len(self._active),
                "completed_total": len(self._completed),
                "status": self._status,
            },
        )
        self._sink.write_event(event)
        return True

    def get_health(self) -> AgencyHealth:
        """Retorna snapshot de saúde coletiva."""
        return AgencyHealth(
            agency_id=self.agency_id,
            name=self._config.name,
            status=self._status,
            active_missions=len(self._active),
            completed_missions=len(self._completed),
            rejected_missions=len(self._rejected),
            capacity=self._config.capacity,
            budget_used_usd=self._budget_used,
            budget_total_usd=self._config.budget_usd,
            squad_count=len(self._config.squads),
        )

    def list_active(self) -> list[str]:
        return list(self._active.keys())

    def _update_status(self) -> None:
        active = len(self._active)
        cap = self._config.capacity
        if active == 0:
            self._status = AGENCY_IDLE
        elif active >= cap:
            self._status = AGENCY_SATURATED
        else:
            self._status = AGENCY_ACTIVE


# ── AgencyRegistry ────────────────────────────────────────────────────────────

class AgencyRegistry:
    """Registra e recupera agências por ID ou setor."""

    def __init__(self) -> None:
        self._agencies: dict[str, Agency] = {}

    def register(self, agency: Agency) -> None:
        self._agencies[agency.agency_id] = agency

    def get(self, agency_id: str) -> Agency | None:
        return self._agencies.get(agency_id)

    def get_by_sector(self, sector: str) -> Agency | None:
        for ag in self._agencies.values():
            if ag._config.sector == sector:
                return ag
        return None

    def list_all(self) -> list[Agency]:
        return list(self._agencies.values())

    def get_health_report(self) -> list[dict[str, Any]]:
        return [ag.get_health().to_dict() for ag in self._agencies.values()]

    def route_mission(self, contract: MissionContract) -> AcceptResult | None:
        """Rota missão para a agência responsável pelo setor."""
        agency = self.get_by_sector(contract.setor)
        if agency is None:
            return None
        return agency.accept_mission(contract)
