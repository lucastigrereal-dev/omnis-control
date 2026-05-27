"""GET /missions — missões executadas."""
from fastapi import APIRouter, HTTPException, Query
from src.missions.repository import JsonlRepository

router = APIRouter()


def _to_dict(obj) -> dict:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return vars(obj)


def _build_mission_summary(mission) -> dict:
    """Resumo compatível com contrato v1/KRATOS."""
    data = _to_dict(mission)
    mission_id = (
        data.get("mission_id")
        or data.get("id")
        or data.get("run_id")
        or ""
    )
    return {
        "mission_id": mission_id,
        "title": data.get("title") or data.get("name") or mission_id or "mission",
        "sector": data.get("sector", "unknown"),
        "status": data.get("status", "running"),
        "current_step": data.get("current_step"),
        "retry_count": int(data.get("retry_count", 0) or 0),
        "max_retries": int(data.get("max_retries", 3) or 3),
        "last_retry_node": data.get("last_retry_node"),
        "checkpoint_id": data.get("checkpoint_id"),
        "checkpoint_label": data.get("checkpoint_label"),
        "checkpoint_at": data.get("checkpoint_at"),
        "checkpoint_completed_steps": data.get("checkpoint_completed_steps", []) or [],
        "checkpoint_pause_reason": data.get("checkpoint_pause_reason"),
        "cumulative_cost_usd": float(data.get("cumulative_cost_usd", 0.0) or 0.0),
        "last_event_type": data.get("last_event_type"),
        "last_event_label": data.get("last_event_label"),
        "last_event_at": data.get("last_event_at"),
        "error_count": int(data.get("error_count", 0) or 0),
        "last_error": data.get("last_error"),
        "event_count": int(data.get("event_count", 0) or 0),
        "budget_exceeded": bool(data.get("budget_exceeded", False)),
        "approval_pending": bool(data.get("approval_pending", False)),
        "approval_reason": data.get("approval_reason"),
    }


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
    summaries = [_build_mission_summary(m) for m in missions]
    return {
        "total": len(missions),
        "missions": [_to_dict(m) for m in missions],  # legado
        "data": summaries,  # v1
        "source": "live",
    }


@router.get("/active")
def list_missions_active(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    """Compat alias para KRATOS atual + shape do contrato v1."""
    repo = JsonlRepository()
    try:
        missions = repo.list_missions(status=status)
    except Exception as exc:
        return {"data": [], "total": 0, "source": "empty", "error": str(exc)}
    missions = missions[:limit]
    return {
        "data": [_build_mission_summary(m) for m in missions],
        "total": len(missions),
        "source": "live",
    }


@router.get("/{mission_id}")
def get_mission(mission_id: str) -> dict:
    repo = JsonlRepository()
    try:
        contract = repo.get_contract(mission_id)
        events = repo.get_events(mission_id)
    except Exception as exc:
        raise HTTPException(404, str(exc))
    contract_data = _to_dict(contract)
    return {
        "contract": contract_data,  # legado
        "events": [_to_dict(e) for e in events],  # legado
        "data": {
            "mission_id": mission_id,
            "contract": contract_data,
            "summary": _build_mission_summary(contract_data),
        },
    }


@router.get("/{mission_id}/events")
def get_mission_events(mission_id: str, limit: int = Query(50, ge=1, le=500)) -> dict:
    """Event log explícito para contrato v1/KRATOS."""
    repo = JsonlRepository()
    try:
        events = repo.get_events(mission_id)
    except Exception as exc:
        raise HTTPException(404, str(exc))
    events = events[:limit]
    return {
        "mission_id": mission_id,
        "total": len(events),
        "data": [_to_dict(e) for e in events],
    }
