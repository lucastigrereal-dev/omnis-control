"""GET /skills — skills disponíveis."""
from fastapi import APIRouter
from src.checkers import skills_check

router = APIRouter()


@router.get("")
def list_skills() -> dict:
    result = skills_check.check()
    return result
