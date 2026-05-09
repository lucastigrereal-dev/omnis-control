"""Asset Assignment Center service — P1.9.

Connects: VideoAsset registry + ContentQueue + CaptionApproval
to produce an AssetAssignmentResult that drives offline packaging.

NEVER calls external APIs. NEVER publishes. NEVER reads .env secrets.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import AssetAssignmentResult


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_assignment_status(queue_id: str) -> AssetAssignmentResult:
    """Inspect a queue slot and report asset assignment readiness."""
    result = AssetAssignmentResult(queue_id=queue_id)

    # 1. Load queue item
    queue_item = None
    try:
        from src.content_queue.queue import Queue
        q = Queue()
        queue_item = q.get(queue_id)
    except Exception:
        pass

    if not queue_item:
        result.blockers.append(f"Queue item '{queue_id}' nao encontrado")
        result.next_actions.append(f"Verificar ID: python jarvis.py queue list")
        return result

    result.account_handle = getattr(queue_item, "account_handle", "")
    result.previous_status = getattr(queue_item, "status", "")

    # 2. Check asset
    asset_id = getattr(queue_item, "asset_id", None)
    if asset_id:
        result.asset_id = asset_id
        try:
            from src.video_assets.registry import Registry
            reg = Registry()
            asset = reg.get(asset_id)
            if asset:
                result.asset_type = getattr(asset, "format", "unknown")
                result.asset_path = getattr(asset, "source_path", "")
                if result.asset_path:
                    result.asset_exists_on_disk = Path(result.asset_path).exists()
                    if not result.asset_exists_on_disk:
                        result.warnings.append(f"Asset path nao existe em disco: {result.asset_path}")
            else:
                result.warnings.append(f"Asset '{asset_id}' nao encontrado no registry")
        except Exception as e:
            result.warnings.append(f"Erro ao carregar asset: {e}")
    else:
        result.blockers.append("Nenhum asset atribuido ao slot")
        result.next_actions.append(
            f"Registrar asset: python jarvis.py assets add-mock <nome> --queue {queue_id}"
        )
        result.next_actions.append(
            f"Ou atribuir existente: python jarvis.py queue assign {queue_id} <asset_id>"
        )

    # 3. Check caption
    caption_id = None
    try:
        from src.caption_approval.drafts import DraftsManager
        dm = DraftsManager()
        drafts = [
            d for d in dm.list_all()
            if (d.queue_id == queue_id or d.queue_id.startswith(queue_id))
            and d.status == "approved"
        ]
        if drafts:
            caption_id = drafts[-1].draft_id
            result.caption_id = caption_id
        else:
            result.warnings.append("Nenhuma caption aprovada para este slot")
    except Exception:
        result.warnings.append("Nao foi possivel verificar captions")

    # 4. Determine readiness
    has_asset = bool(asset_id)
    has_caption = bool(caption_id)
    result.ready_for_package = has_asset and has_caption and not result.blockers

    if result.ready_for_package:
        result.new_status = "ready_for_package"
        result.next_actions.append(
            f"Gerar pacote: python jarvis.py offline package-carousel {queue_id}"
        )
    elif has_asset and not has_caption:
        result.new_status = "needs_caption"
        result.next_actions.append(
            f"Aprovar legenda: python jarvis.py captions approve <draft_id>"
        )
    elif has_caption and not has_asset:
        result.new_status = "needs_asset"
    else:
        result.new_status = "blocked"

    return result


def add_mock_asset(
    name: str,
    queue_id: Optional[str] = None,
    format: str = "carousel",
    account_handle: str = "",
    registry_path: Optional[str] = None,
) -> dict:
    """Register a mock/local asset for testing offline packaging.

    Creates an entry in the video_assets registry without requiring a real file.
    Optionally assigns it to a queue slot immediately.

    NEVER calls external APIs. NEVER publishes.
    """
    from src.video_assets.registry import Registry
    from src.video_assets.models import VideoAsset, AssetFormat, AssetSourceType

    reg = Registry(path=registry_path) if registry_path else Registry()

    asset_id = f"mock_{uuid.uuid4().hex[:8]}"
    mock_path = f"[MOCK] {name}"

    asset = VideoAsset.new(
        asset_id=asset_id,
        source_type=AssetSourceType.MANUAL,
        source_path=mock_path,
        file_name=name,
        extension=".mock",
        size_bytes=0,
        format=format,
        account_target=account_handle,
    )
    reg.add(asset)

    result = {
        "asset_id": asset_id,
        "name": name,
        "format": format,
        "account_handle": account_handle,
        "mock": True,
        "assigned_to_queue": None,
    }

    if queue_id:
        try:
            from src.content_queue.queue import Queue
            q = Queue()
            updated, warning = q.assign_asset(queue_id, asset_id, force=True)
            result["assigned_to_queue"] = queue_id
            if warning:
                result["warning"] = warning
        except Exception as e:
            result["assign_error"] = str(e)

    return result


def list_ready_candidates() -> list[dict]:
    """List queue slots that have both an asset and an approved caption."""
    candidates = []
    try:
        from src.content_queue.queue import Queue
        q = Queue()
        items = q.list_all()

        from src.caption_approval.drafts import DraftsManager
        dm = DraftsManager()
        approved_queue_ids = set(
            d.queue_id for d in dm.list_all() if d.status == "approved"
        )

        for item in items:
            has_asset = bool(getattr(item, "asset_id", None))
            has_caption = any(
                qid == item.queue_id or qid.startswith(item.queue_id[:8])
                for qid in approved_queue_ids
            )
            if has_asset or has_caption:
                candidates.append({
                    "queue_id": item.queue_id,
                    "account_handle": item.account_handle,
                    "date": item.date,
                    "status": item.status,
                    "asset_id": getattr(item, "asset_id", None),
                    "has_caption": has_caption,
                    "has_asset": has_asset,
                    "ready_for_package": has_asset and has_caption,
                })
    except Exception:
        pass

    return sorted(candidates, key=lambda c: (not c["ready_for_package"], c["date"]))
