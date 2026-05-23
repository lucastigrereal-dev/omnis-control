"""GET /missions — missões executadas."""
from fastapi import APIRouter, HTTPException, Query
from src.missions.repository import JsonlRepository

router = APIRouter()


@router.get("")
def list_missions(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    repo = JsonlRepository()
    try:
        missions = repo.list_missions(status=status)
    except Exception as exc:
        return {"total": 0, "missions": [], "error": str(exc)}
    missions = missions[:limit]
    return {
        "total": len(missions),
        "missions": [m.to_dict() if hasattr(m, "to_dict") else vars(m) for m in missions],
    }


@router.get("/{mission_id}")
def get_mission(mission_id: str) -> dict:
    repo = JsonlRepository()
    try:
        contract = repo.get_contract(mission_id)
        events = repo.get_events(mission_id)
    except Exception as exc:
        raise HTTPException(404, str(exc))
    return {
        "contract": contract.to_dict() if hasattr(contract, "to_dict") else vars(contract),
        "events": [e.to_dict() if hasattr(e, "to_dict") else vars(e) for e in events],
    }
