"""GET /reports — relatórios e briefings."""
from fastapi import APIRouter
from src.reports import status_report, briefing as briefing_mod
from src.utils.logger import new_session_id

router = APIRouter()


@router.get("/status")
def get_status_report() -> dict:
    session_id = new_session_id()
    try:
        content = status_report.generate(session_id)
        return {"session_id": session_id, "report": content}
    except Exception as exc:
        return {"session_id": session_id, "report": None, "error": str(exc)}


@router.get("/briefing")
def get_briefing() -> dict:
    try:
        content = briefing_mod.generate(save=False)
        return {"briefing": content}
    except Exception as exc:
        return {"briefing": None, "error": str(exc)}
