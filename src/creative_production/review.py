"""Creative review workflow — approve/reject creative briefs."""
from typing import Optional

from .briefs import create_review, get_brief, list_briefs


def approve_brief(brief_id: str, notes: str = "") -> bool:
    """Approve a creative brief. Returns True if successful."""
    brief = get_brief(brief_id)
    if not brief:
        return False
    create_review(brief_id, "approved", notes)
    return True


def reject_brief(brief_id: str, notes: str = "") -> bool:
    """Reject a creative brief. Returns True if successful."""
    brief = get_brief(brief_id)
    if not brief:
        return False
    create_review(brief_id, "rejected", notes)
    return True


def request_changes(brief_id: str, notes: str = "") -> bool:
    """Request changes to a creative brief."""
    brief = get_brief(brief_id)
    if not brief:
        return False
    create_review(brief_id, "changes_requested", notes)
    return True


def get_pending_reviews() -> list:
    """List all briefs awaiting review."""
    return [b for b in list_briefs() if b.get("status") == "draft"]


def is_ready_for_argos(brief_id: str) -> tuple:
    """Check if a brief is ready for ARGOS (caption approved + creative approved + asset attached)."""
    brief = get_brief(brief_id)
    if not brief:
        return False, "BRIEF_NOT_FOUND"

    issues = []
    if "CAPTION_NOT_APPROVED" in brief.warnings:
        issues.append("CAPTION_NOT_APPROVED")
    if brief.status != "approved":
        issues.append("CREATIVE_NOT_APPROVED")
    if not issues:
        return True, "READY_FOR_ARGOS"
    return False, "; ".join(issues)
