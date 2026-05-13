"""P3 Caption Approval V2 — Dry-run approval modeling layer.

Does NOT approve real content, mutate queues, or write to data/.
All operations produce models/plans only.
"""

from .models import (
    CaptionDraftV2,
    CaptionVariant,
    CaptionChecklist,
    ApprovalDecision,
    ApprovalPolicy,
    CaptionApprovalPackage,
    DraftStatusV2,
    DecisionOutcome,
    ChecklistSeverity,
    PolicyRule,
    PolicyEffect,
)
from .planner import CaptionApprovalPlanner

__all__ = [
    "CaptionDraftV2",
    "CaptionVariant",
    "CaptionChecklist",
    "ApprovalDecision",
    "ApprovalPolicy",
    "CaptionApprovalPackage",
    "DraftStatusV2",
    "DecisionOutcome",
    "ChecklistSeverity",
    "PolicyRule",
    "PolicyEffect",
    "CaptionApprovalPlanner",
]
