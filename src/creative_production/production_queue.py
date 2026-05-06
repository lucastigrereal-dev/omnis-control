"""Production queue — tracks items in creative production."""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import ProductionItem

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
QUEUE_FILE = DATA_DIR / "production_queue.jsonl"


def _load_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _append_jsonl(path: Path, record: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def create_production_item(
    queue_id: str,
    creative_brief_id: str,
    asset_type: str,
    tool_target: str = "manual",
) -> ProductionItem:
    """Create a new production queue item."""
    item = ProductionItem(
        production_id=str(uuid.uuid4())[:8],
        queue_id=queue_id,
        creative_brief_id=creative_brief_id,
        asset_type=asset_type,
        tool_target=tool_target,
    )
    _append_jsonl(QUEUE_FILE, item.to_dict())
    return item


def list_production_items(status: Optional[str] = None) -> list:
    """List production items, optionally filtered by status."""
    items = _load_jsonl(QUEUE_FILE)
    if status:
        items = [i for i in items if i.get("status") == status]
    return sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)


def update_item_status(production_id: str, status: str, asset_path: Optional[str] = None):
    """Update a production item's status."""
    items = _load_jsonl(QUEUE_FILE)
    for item in items:
        if item.get("production_id") == production_id:
            item["status"] = status
            item["updated_at"] = datetime.now().isoformat(timespec="seconds")
            if asset_path:
                item["asset_path"] = asset_path
            break
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def attach_asset(production_id: str, asset_path: str, asset_id: Optional[str] = None):
    """Attach an asset path/ID to a production item."""
    items = _load_jsonl(QUEUE_FILE)
    for item in items:
        if item.get("production_id") == production_id:
            item["asset_path"] = asset_path
            item["updated_at"] = datetime.now().isoformat(timespec="seconds")
            if asset_id:
                item["asset_id"] = asset_id
            item["status"] = "done"
            break
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def get_queue_stats() -> dict:
    """Get production queue statistics."""
    items = _load_jsonl(QUEUE_FILE)
    statuses = {}
    for item in items:
        s = item.get("status", "unknown")
        statuses[s] = statuses.get(s, 0) + 1
    return {
        "total": len(items),
        "by_status": statuses,
        "pending": statuses.get("pending", 0),
        "in_progress": statuses.get("in_progress", 0),
        "done": statuses.get("done", 0),
    }
