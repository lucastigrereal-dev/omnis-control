"""MarketingRouter — roteia missões de marketing para o squad correto."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from src.sectors.marketing.mission_types import MarketingMissionInput, MarketingMissionOutput
from src.sectors.marketing.agents.content_agent import ContentAgent
from src.sectors.marketing.agents.sdr_agent import SDRAgent

if TYPE_CHECKING:
    from src.sectors.marketing.agents.base import BaseMarketingAgent

# Mapeamento de squad → lista de classes de agente
SQUAD_MAP: dict[str, list[type]] = {
    "instagram": [ContentAgent],
    "comercial": [SDRAgent],
    "growth": [ContentAgent, SDRAgent],
}


class MarketingRouter:
    """Roteia uma missão de marketing para o squad correto e agrega os resultados."""

    def execute(self, input: MarketingMissionInput) -> MarketingMissionOutput:
        """Executa a missão pelo squad mapeado e retorna MarketingMissionOutput."""
        agent_classes = SQUAD_MAP.get(input.squad, [ContentAgent])
        outputs: list[dict] = []
        total_cost = 0.0
        total_tokens = 0

        for agent_cls in agent_classes:
            agent = agent_cls()
            result = agent.execute_mission(input)
            outputs.append(result)
            total_cost += result.get("cost_usd", 0.0)
            total_tokens += result.get("tokens_used", 0)

        # Determina status consolidado — "done" se todos "done", senão "blocked"
        all_done = all(r.get("status") == "done" for r in outputs)
        status = "done" if all_done else "blocked"

        mission_id = f"mkt_{uuid.uuid4().hex[:8]}"
        return MarketingMissionOutput(
            mission_id=mission_id,
            status=status,
            outputs=outputs,
            cost_usd=total_cost,
            tokens_used=total_tokens,
        )
