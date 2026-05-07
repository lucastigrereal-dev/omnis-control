"""Creative brief generation and management."""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import CreativeBrief, CreativeReview

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
BRIEFS_FILE = DATA_DIR / "creative_briefs.jsonl"
REVIEW_LOG = DATA_DIR / "creative_review_log.jsonl"


def _load_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _append_jsonl(path: Path, record: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def create_brief(
    queue_id: str,
    account_handle: str,
    format: str,
    objective: str,
    visual_direction: str,
    caption_draft_id: Optional[str] = None,
    script: str = "",
    shot_list: str = "",
    design_notes: str = "",
    editing_notes: str = "",
    asset_requirements: dict = None,
    tool_suggestions: list = None,
) -> CreativeBrief:
    """Create a new creative brief with validation."""
    warnings = []

    # Validate queue_id against content queue
    queue_items = _load_jsonl(DATA_DIR / "content_queue.jsonl")
    queue_ids = {item.get("queue_id") or item.get("id") for item in queue_items
                 if item.get("queue_id") or item.get("id")}
    if queue_ids and queue_id not in queue_ids:
        warnings.append("QUEUE_NOT_FOUND")

    # Validate caption approval if draft_id provided
    if caption_draft_id:
        drafts = _load_jsonl(DATA_DIR / "caption_drafts.jsonl")
        draft_ids = {d.get("draft_id") or d.get("id") for d in drafts}
        if caption_draft_id not in draft_ids:
            warnings.append("CAPTION_DRAFT_NOT_FOUND")
        else:
            # Check if caption is approved
            approved = any(
                d.get("status") == "approved"
                for d in drafts
                if (d.get("draft_id") or d.get("id")) == caption_draft_id
            )
            if not approved:
                warnings.append("CAPTION_NOT_APPROVED")
    else:
        warnings.append("CAPTION_NOT_APPROVED")

    brief = CreativeBrief(
        creative_brief_id=str(uuid.uuid4())[:8],
        queue_id=queue_id,
        caption_draft_id=caption_draft_id,
        account_handle=account_handle,
        format=format,
        objective=objective,
        visual_direction=visual_direction,
        script=script,
        shot_list=shot_list,
        design_notes=design_notes,
        editing_notes=editing_notes,
        asset_requirements=asset_requirements or {},
        tool_suggestions=tool_suggestions or [],
        status="draft",
        warnings=warnings,
    )

    _append_jsonl(BRIEFS_FILE, brief.to_dict())
    return brief


def list_briefs(status: Optional[str] = None) -> list:
    """List all creative briefs, optionally filtered by status."""
    briefs = _load_jsonl(BRIEFS_FILE)
    if status:
        briefs = [b for b in briefs if b.get("status") == status]
    return sorted(briefs, key=lambda x: x.get("created_at", ""), reverse=True)


def get_brief(brief_id: str) -> Optional[CreativeBrief]:
    """Get a single brief by ID."""
    for b in list_briefs():
        if b.get("creative_brief_id") == brief_id:
            return CreativeBrief.from_dict(b)
    return None


def update_brief_status(brief_id: str, new_status: str) -> bool:
    """Update brief status in-place."""
    briefs = _load_jsonl(BRIEFS_FILE)
    updated = False
    for b in briefs:
        if b.get("creative_brief_id") == brief_id:
            b["status"] = new_status
            b["updated_at"] = datetime.now().isoformat(timespec="seconds")
            updated = True
            break
    if updated:
        with open(BRIEFS_FILE, "w", encoding="utf-8") as f:
            for b in briefs:
                f.write(json.dumps(b, ensure_ascii=False) + "\n")
    return updated


def create_review(brief_id: str, status: str, notes: str = "") -> CreativeReview:
    """Create a review record for a creative brief."""
    review = CreativeReview(
        review_id=str(uuid.uuid4())[:8],
        creative_brief_id=brief_id,
        status=status,
        notes=notes,
    )
    _append_jsonl(REVIEW_LOG, review.to_dict())
    if status in ("approved", "rejected"):
        update_brief_status(brief_id, status.replace("approved", "approved").replace("rejected", "rejected"))
    return review


def brief_stats() -> dict:
    """Aggregated statistics for creative briefs."""
    from collections import Counter
    briefs = list_briefs()
    by_status = Counter(b.get("status") for b in briefs if b.get("status"))
    by_format = Counter(b.get("format") for b in briefs if b.get("format"))
    return {
        "total": len(briefs),
        "by_status": dict(by_status),
        "by_format": dict(by_format),
    }


def validate_queue_exists(queue_id: str) -> bool:
    """Check if a queue ID exists in the content queue."""
    queue_items = _load_jsonl(DATA_DIR / "content_queue.jsonl")
    return any(
        (item.get("queue_id") or item.get("id")) == queue_id
        for item in queue_items
    )
