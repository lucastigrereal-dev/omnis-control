"""SquadSelector — monta squad especializado por setor detectado."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── squad member ───────────────────────────────────────────────────────

@dataclass
class SquadMember:
    role: str
    skill_id: str
    intent: str  # create | read | analyze | generate | publish
    primary: bool = False

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "skill_id": self.skill_id,
            "intent": self.intent,
            "primary": self.primary,
        }


# ── squad definition ───────────────────────────────────────────────────

@dataclass
class SquadDefinition:
    squad_id: str
    name: str
    sector: str
    description: str
    members: list[SquadMember] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    export_formats: list[str] = field(default_factory=list)

    @property
    def primary_member(self) -> SquadMember | None:
        for m in self.members:
            if m.primary:
                return m
        return self.members[0] if self.members else None

    def to_dict(self) -> dict:
        return {
            "squad_id": self.squad_id,
            "name": self.name,
            "sector": self.sector,
            "description": self.description,
            "members": [m.to_dict() for m in self.members],
            "capabilities": self.capabilities,
            "export_formats": self.export_formats,
        }


# ── squad assignment ───────────────────────────────────────────────────

@dataclass
class SquadAssignment:
    mission_id: str
    squad: SquadDefinition
    reason: str
    assembled_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "squad": self.squad.to_dict(),
            "reason": self.reason,
            "assembled_at": self.assembled_at,
        }


# ── squad registry ─────────────────────────────────────────────────────

_SQUADS: dict[str, SquadDefinition] = {
    "marketing": SquadDefinition(
        squad_id="SQD-MKT",
        name="Marketing Squad",
        sector="marketing",
        description="Content + Caption + Calendar + Publisher — entrega conteúdo pronto pra postar",
        members=[
            SquadMember(role="Content Strategist", skill_id="create_30_day_content_calendar", intent="create", primary=True),
            SquadMember(role="Caption Writer", skill_id="generate_seogram_caption", intent="create", primary=False),
            SquadMember(role="Carousel Designer", skill_id="create_instagram_carousel", intent="create", primary=False),
            SquadMember(role="Publisher Bridge", skill_id="argos-bridge", intent="publish", primary=False),
        ],
        capabilities=[
            "Calendário editorial 30 dias",
            "Legendas otimizadas SEO + CTA",
            "Carrosséis Instagram prontos",
            "Publicação integrada ARGOS",
        ],
        export_formats=["csv", "md", "json", "png"],
    ),
    "sales": SquadDefinition(
        squad_id="SQD-SALES",
        name="Sales Squad",
        sector="sales",
        description="Lead Qualifier + DM Sequence + CRM Pipeline — prospecção e fechamento",
        members=[
            SquadMember(role="Lead Qualifier", skill_id="jarvis-router", intent="analyze", primary=True),
            SquadMember(role="DM Outreach", skill_id="create_sales_dm_sequence", intent="create", primary=False),
            SquadMember(role="CRM Manager", skill_id="crm-pipeline", intent="read", primary=False),
            SquadMember(role="Revenue Analyst", skill_id="revenue-tracker", intent="analyze", primary=False),
        ],
        capabilities=[
            "Qualificação de leads (BANT)",
            "Sequências de DM personalizadas",
            "Pipeline CRM atualizado",
            "Tracking de receita e conversão",
        ],
        export_formats=["csv", "md", "json"],
    ),
    "app_factory": SquadDefinition(
        squad_id="SQD-APP",
        name="App Factory Squad",
        sector="app_factory",
        description="PRD + Schema + API + Tests — gera apps completas a partir de briefing",
        members=[
            SquadMember(role="Product Architect", skill_id="jarvis-brain", intent="analyze", primary=True),
            SquadMember(role="Code Generator", skill_id="skill-creator", intent="create", primary=False),
            SquadMember(role="Test Engineer", skill_id="jarvis-decide", intent="analyze", primary=False),
            SquadMember(role="Package Builder", skill_id="jarvis-memory-write", intent="create", primary=False),
        ],
        capabilities=[
            "Product Requirements Document (PRD)",
            "Database schema + migrations",
            "API contract OpenAPI",
            "Test suite scaffold",
            "Package .zip exportável",
        ],
        export_formats=["md", "json", "yaml", "zip"],
    ),
    "computer_ops": SquadDefinition(
        squad_id="SQD-OPS",
        name="Computer Ops Squad",
        sector="computer_ops",
        description="Disk Audit + Health Check + Quarantine — mantém sistema saudável",
        members=[
            SquadMember(role="System Auditor", skill_id="jarvis-brain", intent="analyze", primary=True),
            SquadMember(role="Health Monitor", skill_id="jarvis-decide", intent="read", primary=False),
            SquadMember(role="Cleanup Agent", skill_id="jarvis-guardrails", intent="delete", primary=False),
            SquadMember(role="Ops Reporter", skill_id="jarvis-memory-write", intent="create", primary=False),
        ],
        capabilities=[
            "Auditoria de disco completa",
            "Health check multi-componente",
            "Plano de quarentena automático",
            "Relatório de saúde do sistema",
        ],
        export_formats=["md", "json", "csv"],
    ),
}

_FALLBACK_SQUAD = SquadDefinition(
    squad_id="SQD-GEN",
    name="General Squad",
    sector="general",
    description="Squad genérico para missões sem setor específico — fallback seguro",
    members=[
        SquadMember(role="General Runner", skill_id="manual-review", intent="read", primary=True),
    ],
    capabilities=["Execução genérica com revisão manual"],
    export_formats=["md"],
)


# ── selector ───────────────────────────────────────────────────────────

class SquadSelector:
    """Seleciona e monta o squad apropriado baseado no setor da missão."""

    def __init__(self) -> None:
        self._squads = dict(_SQUADS)

    def select(self, sector: str) -> SquadDefinition:
        """Retorna o squad para um setor, ou fallback se não encontrado."""
        squad = self._squads.get(sector)
        if squad:
            return squad
        return _FALLBACK_SQUAD

    def assign(self, mission_id: str, sector: str) -> SquadAssignment:
        """Atribui um squad a uma missão com justificativa."""
        squad = self.select(sector)
        reason = (
            f"Setor '{sector}' mapeado para {squad.name} ({squad.squad_id}) "
            f"com {len(squad.members)} membros"
        )
        return SquadAssignment(
            mission_id=mission_id,
            squad=squad,
            reason=reason,
        )

    def list_all(self) -> list[SquadDefinition]:
        """Lista todos os squads disponíveis."""
        return list(self._squads.values())

    def get_capabilities(self, sector: str) -> list[str]:
        """Retorna as capacidades de um squad pelo setor."""
        return self.select(sector).capabilities

    def get_export_formats(self, sector: str) -> list[str]:
        """Retorna os formatos de exportação de um squad pelo setor."""
        return self.select(sector).export_formats

    @property
    def available_sectors(self) -> list[str]:
        return list(self._squads.keys())
