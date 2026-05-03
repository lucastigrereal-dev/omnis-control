"""Caption Draft + Approval Gate (Fase 2C).

Gerencia rascunhos de legenda e o fluxo de aprovação local.
Dependência unidirecional: caption_approval → content_queue.
"""

from .models import CaptionDraft, DraftStatus, CaptionTemplate, ApprovalLogEntry
from .drafts import DraftsManager
from .approvals import ApprovalGate
from .templates import TemplateLibrary

__all__ = [
    "CaptionDraft",
    "DraftStatus",
    "CaptionTemplate",
    "ApprovalLogEntry",
    "DraftsManager",
    "ApprovalGate",
    "TemplateLibrary",
]
