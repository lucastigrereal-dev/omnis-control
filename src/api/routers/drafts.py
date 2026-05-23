"""GET /drafts — rascunhos de legenda."""
from fastapi import APIRouter, HTTPException, Query
from src.caption_approval import DraftsManager
from src.caption_approval.models import DraftStatus

router = APIRouter()


@router.get("")
def list_drafts(
    status: str | None = Query(None, description="Filtrar por status"),
    account: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    dm = DraftsManager()
    drafts = dm.list_all()
    if status:
        valid = {v for k, v in vars(DraftStatus).items() if not k.startswith("_")}
        if status not in valid:
            raise HTTPException(422, f"Status inválido: {status}. Válidos: {sorted(valid)}")
        drafts = [d for d in drafts if d.status == status]
    if account:
        drafts = [d for d in drafts if d.account_handle == account]
    drafts = drafts[:limit]
    return {"total": len(drafts), "drafts": [d.to_dict() for d in drafts]}


@router.get("/{draft_id}")
def get_draft(draft_id: str) -> dict:
    dm = DraftsManager()
    draft = dm.get(draft_id)
    if not draft:
        raise HTTPException(404, f"Draft não encontrado: {draft_id}")
    return draft.to_dict()
