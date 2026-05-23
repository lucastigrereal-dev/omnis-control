"""GET /agent — observabilidade da camada agentic para KRATOS."""
from fastapi import APIRouter, HTTPException, Query

from src.agentic.agent_models import AgentRunRepository
from src.agentic.scheduler import ScheduleRepository, ScheduleRunRepository
from src.memory.caption_memory import CaptionMemoryReader

router = APIRouter()


@router.get("/runs")
def list_agent_runs(
    account: str | None = Query(None, description="Filtrar por conta"),
    status: str | None = Query(None, description="Filtrar por status"),
    limit: int = Query(20, ge=1, le=200),
) -> dict:
    """Lista runs do CaptionDraftAgent, mais recentes primeiro."""
    repo = AgentRunRepository()
    runs = list(reversed(repo.list_all()))
    if account:
        runs = [r for r in runs if r.account_handle == account]
    if status:
        runs = [r for r in runs if r.status == status]
    runs = runs[:limit]
    return {"total": len(runs), "runs": [r.to_dict() for r in runs]}


@router.get("/runs/{run_id}")
def get_agent_run(run_id: str) -> dict:
    """Retorna um run específico pelo ID."""
    repo = AgentRunRepository()
    for run in repo.list_all():
        if run.run_id == run_id:
            return run.to_dict()
    raise HTTPException(404, f"AgentRun[{run_id}]: Run não encontrado")


@router.get("/schedules")
def list_schedules(
    enabled_only: bool = Query(False, description="Mostrar apenas schedules ativos"),
) -> dict:
    """Lista schedules de batch cadastrados."""
    repo = ScheduleRepository()
    schedules = repo.list_all()
    if enabled_only:
        schedules = [s for s in schedules if s.enabled]
    return {"total": len(schedules), "schedules": [s.to_dict() for s in schedules]}


@router.get("/schedules/{schedule_id}/history")
def get_schedule_history(
    schedule_id: str,
    limit: int = Query(10, ge=1, le=100),
) -> dict:
    """Histórico de execuções de um schedule."""
    run_repo = ScheduleRunRepository()
    runs = list(reversed(run_repo.for_schedule(schedule_id)))[:limit]
    return {"schedule_id": schedule_id, "total": len(runs), "runs": [r.to_dict() for r in runs]}


@router.get("/memory")
def get_memory_stats(
    account: str | None = Query(None, description="Filtrar por conta"),
) -> dict:
    """Estatísticas da memória de legendas aprovadas."""
    reader = CaptionMemoryReader()
    total = reader.count(account)
    return {"account_filter": account, "total_entries": total}
