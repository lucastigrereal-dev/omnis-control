"""GET /assets — registro de video assets."""
from fastapi import APIRouter, HTTPException, Query
from src.video_assets import Registry, AssetStatus

router = APIRouter()


@router.get("")
def list_assets(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    reg = Registry()
    assets = reg.list_all()
    if status:
        try:
            s = AssetStatus(status)
            assets = [a for a in assets if a.status == s]
        except ValueError:
            raise HTTPException(422, f"Status inválido: {status}")
    assets = assets[:limit]
    return {"total": len(assets), "assets": [a.to_dict() for a in assets]}


@router.get("/{asset_id}")
def get_asset(asset_id: str) -> dict:
    reg = Registry()
    asset = reg.get(asset_id)
    if not asset:
        raise HTTPException(404, f"Asset não encontrado: {asset_id}")
    return asset.to_dict()
