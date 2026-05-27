"""ContentAgent — stub para geração de copy de conteúdo."""
from __future__ import annotations

from src.sectors.marketing.agents.base import BaseMarketingAgent
from src.sectors.marketing.mission_types import MarketingMissionInput


class ContentAgent(BaseMarketingAgent):
    """Agente de produção de conteúdo (copy, posts, carrossel).

    Stub: simula geração de copy sem chamada LLM.
    """

    def execute_mission(self, input: MarketingMissionInput) -> dict:
        return {
            "status": "done",
            "output": f"ContentAgent gerou copy para: {input.goal}",
            "cost_usd": 0.001,
            "tokens_used": 100,
        }
