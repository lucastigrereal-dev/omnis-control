"""GET /health — estado de saúde do OMNIS."""
from fastapi import APIRouter
from src.checkers import (
    skills_check, docker_check, publisher_check,
    memory_check, obsidian_check, disk_check,
)

router = APIRouter()


@router.get("")
def get_health() -> dict:
    """Retorna status de todos os checkers."""
    results: dict[str, object] = {}
    checkers = {
        "skills": skills_check.check,
        "docker": docker_check.check,
        "publisher": publisher_check.check,
        "memory": memory_check.check,
        "obsidian": obsidian_check.check,
        "disk": disk_check.check,
    }
    for name, fn in checkers.items():
        try:
            results[name] = fn()
        except Exception as exc:
            results[name] = {"status": "error", "error": str(exc)}

    statuses = [v.get("status", "unknown") for v in results.values() if isinstance(v, dict)]
    overall = "ok" if all(s == "ok" for s in statuses) else (
        "warning" if any(s == "ok" for s in statuses) else "error"
    )
    return {"overall": overall, "checks": results}
