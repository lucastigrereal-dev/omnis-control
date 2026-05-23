"""GET /queue — fila editorial."""
from fastapi import APIRouter, HTTPException, Query
from src.content_queue import Queue, QueueStatus

router = APIRouter()


@router.get("")
def list_queue(
    status: str | None = Query(None, description="Filtrar por status"),
    account: str | None = Query(None, description="Filtrar por handle de conta"),
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    q = Queue()
    items = q.list_all()
    if status:
        valid = {v for k, v in vars(QueueStatus).items() if not k.startswith("_")}
        if status not in valid:
            raise HTTPException(422, f"Status inválido: {status}. Válidos: {sorted(valid)}")
        items = [i for i in items if i.status == status]
    if account:
        items = [i for i in items if i.account_handle == account]
    items = items[:limit]
    return {"total": len(items), "items": [i.to_dict() for i in items]}


@router.get("/{queue_id}")
def get_queue_item(queue_id: str) -> dict:
    q = Queue()
    item = q.get(queue_id)
    if not item:
        raise HTTPException(404, f"Item não encontrado: {queue_id}")
    return item.to_dict()
