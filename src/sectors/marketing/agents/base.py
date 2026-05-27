"""BaseMarketingAgent — stub base para agentes de marketing."""
from __future__ import annotations

from src.sectors.marketing.mission_types import MarketingMissionInput


class BaseMarketingAgent:
    """Agente base do setor de marketing.

    Stub: retorna resposta determinística sem chamar LLM.
    model é sempre haiku — NUNCA opus.
    """

    model: str = "haiku"

    def execute_mission(self, input: MarketingMissionInput) -> dict:
        """Executa a missão e retorna um dict com status, output, cost_usd e tokens_used."""
        return {
            "status": "done",
            "output": f"{self.__class__.__name__} executou: {input.goal}",
            "cost_usd": 0.001,
            "tokens_used": 100,
        }
