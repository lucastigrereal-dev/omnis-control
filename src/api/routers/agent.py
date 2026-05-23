"""GET /agent — observabilidade da camada agentic para KRATOS."""
from fastapi import APIRouter, HTTPException, Query

from src.agentic.agent_models import AgentRunRepository, AgentRunStatus
from src.agentic.llm_adapter import LiteLLMAdapter
from src.agentic.scheduler import ScheduleRepository, ScheduleRunRepository
from src.content_queue import Queue, QueueStatus
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


@router.get("/status")
def get_agent_status() -> dict:
    """Snapshot de saúde da camada agentic — equivalente a `omnis agent status --json`."""
    q = Queue()
    all_items = q.list_all()
    pending = [i for i in all_items if i.status in (QueueStatus.PLANNED, QueueStatus.NEEDS_CAPTION)]
    caption_ready = [i for i in all_items if i.status == "caption_ready"]

    repo = AgentRunRepository()
    all_runs = repo.list_all()
    run_counts = {
        "completed": sum(1 for r in all_runs if r.status == AgentRunStatus.COMPLETED),
        "dry_run": sum(1 for r in all_runs if r.status == AgentRunStatus.DRY_RUN),
        "failed": sum(1 for r in all_runs if r.status == AgentRunStatus.FAILED),
    }

    sched_repo = ScheduleRepository()
    schedules = sched_repo.list_all()
    active = [s for s in schedules if s.enabled]
    due = [s for s in active if s.is_due]

    reader = CaptionMemoryReader()

    return {
        "queue": {
            "total": len(all_items),
            "pending": len(pending),
            "caption_ready": len(caption_ready),
        },
        "runs": {
            "total": len(all_runs),
            **run_counts,
        },
        "schedules": {
            "total": len(schedules),
            "active": len(active),
            "due_now": len(due),
        },
        "memory": {"total_entries": reader.count()},
        "litellm_available": LiteLLMAdapter().health_check(),
    }
