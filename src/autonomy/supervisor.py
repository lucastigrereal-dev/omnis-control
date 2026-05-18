"""AutonomySupervisor — controla nível N0→N7 por missão."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── autonomy levels ────────────────────────────────────────────────────
#
# N0 — Fully manual: Lucas faz tudo. OMNIS só observa.
# N1 — Suggest only: OMNIS sugere, Lucas decide tudo.
# N2 — Dry-run auto, execute precisa de aprovação.
# N3 — Auto-executa risco baixo, aprovação para médio+.
# N4 — Auto-executa risco médio-, aprovação para alto+.
# N5 — Auto-executa risco alto-, aprovação só para crítico.
# N6 — Full auto: executa tudo, loga tudo.
# N7 — Full autonomous: auto-aprova, auto-executa, auto-aprende.

AUTONOMY_LEVELS: dict[int, str] = {
    0: "fully_manual",
    1: "suggest_only",
    2: "dry_run_auto",
    3: "low_auto",
    4: "medium_auto",
    5: "high_auto",
    6: "full_auto",
    7: "full_autonomous",
}

AUTONOMY_LABELS: dict[int, str] = {
    0: "N0 — Totalmente Manual",
    1: "N1 — Apenas Sugestões",
    2: "N2 — Dry-Run Automático",
    3: "N3 — Baixo Risco Auto",
    4: "N4 — Médio Risco Auto",
    5: "N5 — Alto Risco Auto",
    6: "N6 — Full Auto",
    7: "N7 — Autônomo Total",
}

# Which risk levels each autonomy level allows without approval
_LEVEL_ALLOW_MAP: dict[int, set[str]] = {
    0: set(),                    # nothing auto
    1: set(),                    # nothing auto
    2: set(),                    # dry-run only (not real execution)
    3: {"low"},                  # low risk auto
    4: {"low", "medium"},        # medium- auto
    5: {"low", "medium", "high"},  # high- auto
    6: {"low", "medium", "high", "critical"},  # everything auto
    7: {"low", "medium", "high", "critical"},  # everything auto + self-approve
}

DEFAULT_LEVEL = 2  # N2: dry-run auto, execute needs approval


# ── models ─────────────────────────────────────────────────────────────

@dataclass
class AutonomyDecision:
    mission_id: str
    level: int
    level_label: str
    action_allowed: bool
    reason: str
    requires_approval: bool
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "level": self.level,
            "level_label": self.level_label,
            "action_allowed": self.action_allowed,
            "reason": self.reason,
            "requires_approval": self.requires_approval,
            "timestamp": self.timestamp,
        }


# ── supervisor ─────────────────────────────────────────────────────────

class AutonomySupervisor:
    """Controla o nível de autonomia por missão e decide o que pode executar."""

    def __init__(self, default_level: int = DEFAULT_LEVEL) -> None:
        if default_level not in AUTONOMY_LEVELS:
            raise ValueError(
                f"Nível inválido: {default_level}. Deve ser 0-7."
            )
        self.default_level = default_level
        self._mission_levels: dict[str, int] = {}

    def set_mission_level(self, mission_id: str, level: int) -> None:
        """Define o nível de autonomia para uma missão específica."""
        if level not in AUTONOMY_LEVELS:
            raise ValueError(f"Nível inválido: {level}. Deve ser 0-7.")
        self._mission_levels[mission_id] = level

    def get_level(self, mission_id: str) -> int:
        """Retorna o nível de autonomia para uma missão."""
        return self._mission_levels.get(mission_id, self.default_level)

    def get_level_label(self, mission_id: str) -> str:
        """Retorna o label legível do nível atual."""
        level = self.get_level(mission_id)
        return AUTONOMY_LABELS.get(level, f"N{level}")

    def can_execute(self, mission_id: str, risk_level: str) -> AutonomyDecision:
        """Verifica se uma ação com dado risco pode executar no nível atual."""
        level = self.get_level(mission_id)
        allowed_risks = _LEVEL_ALLOW_MAP.get(level, set())

        # N0-N1: nunca executa automaticamente
        if level <= 1:
            return AutonomyDecision(
                mission_id=mission_id,
                level=level,
                level_label=AUTONOMY_LABELS[level],
                action_allowed=False,
                reason=f"Nível {level} ({AUTONOMY_LABELS[level]}) não executa ações — apenas sugere",
                requires_approval=True,
            )

        # N2: apenas dry-run (simulado pelo approval gate)
        if level == 2:
            return AutonomyDecision(
                mission_id=mission_id,
                level=level,
                level_label=AUTONOMY_LABELS[level],
                action_allowed=False,
                reason="N2 permite apenas dry-run — execução real requer aprovação",
                requires_approval=True,
            )

        # N3-N7: verifica contra o mapa de riscos permitidos
        if risk_level in allowed_risks:
            return AutonomyDecision(
                mission_id=mission_id,
                level=level,
                level_label=AUTONOMY_LABELS[level],
                action_allowed=True,
                reason=f"Risco '{risk_level}' permitido no nível {level} ({AUTONOMY_LABELS[level]})",
                requires_approval=False,
            )

        return AutonomyDecision(
            mission_id=mission_id,
            level=level,
            level_label=AUTONOMY_LABELS[level],
            action_allowed=False,
            reason=f"Risco '{risk_level}' acima do permitido no nível {level} — requer aprovação",
            requires_approval=True,
        )

    def suggest_level(self, sector: str) -> int:
        """Sugere nível de autonomia baseado no setor."""
        suggestions = {
            "marketing": 3,      # low risk auto
            "sales": 2,          # dry-run auto (envolve contato externo)
            "app_factory": 4,    # medium auto (local, controlado)
            "computer_ops": 3,   # low auto (pode ser destrutivo)
            "finance": 1,        # suggest only (dinheiro envolvido)
            "general": 2,        # dry-run auto
        }
        return suggestions.get(sector, self.default_level)

    @property
    def mission_levels(self) -> dict[str, int]:
        return dict(self._mission_levels)
