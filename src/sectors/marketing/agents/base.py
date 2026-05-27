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

    def execute_mission_dict(self, mission: dict) -> dict:
        """Executa missão a partir de dict simples (interface do squad_orchestrator)."""
        try:
            inp = MarketingMissionInput(
                type=mission.get("type", "content_production"),
                squad=mission.get("squad", "instagram"),
                priority=mission.get("priority", "P2"),
                goal=mission.get("goal", "executar"),
                deadline=mission.get("deadline", "2099-12-31"),
                inputs=mission,
                model=mission.get("model", "haiku"),
            )
            return self.execute_mission(inp)
        except Exception as e:
            return {"status": "error", "error": str(e), "cost_usd": 0.0, "tokens_used": 0}
