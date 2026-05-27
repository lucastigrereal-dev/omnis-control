"""Router de marketing — missoes de conteudo e SDR."""
from fastapi import APIRouter
from src.sectors.marketing.router import MarketingRouter
from src.sectors.marketing.mission_types import MarketingMissionInput

router = APIRouter()


@router.get("/sprint")
def get_sprint():
    return {"status": "ok", "sprint": [], "note": "Notion integration pending"}


@router.post("/missions")
def create_marketing_mission(mission: dict):
    """Executa missao de marketing via MarketingRouter."""
    try:
        inp = MarketingMissionInput(
            type=mission.get("type", "content_production"),
            squad=mission.get("squad", "instagram"),
            priority=mission.get("priority", "P2"),
            goal=mission.get("goal", ""),
            deadline=mission.get("deadline", "2099-12-31"),
            inputs=mission,
            model=mission.get("model", "haiku"),
        )
        r = MarketingRouter().execute(inp)
        return r.model_dump()
    except Exception as e:
        return {"error": str(e)}


@router.get("/agents")
def list_agents():
    return {"agents": ["ContentAgent", "SDRAgent"]}
