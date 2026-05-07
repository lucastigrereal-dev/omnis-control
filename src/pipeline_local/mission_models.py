"""Modelos do Mission-Aware Pipeline — P0.6."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MissionPipelineStatus:
    SUCCESS = "success"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    FAILED = "failed"
    ALREADY_COMPLETED = "already_completed"


class MissionPipelineBlockReason:
    MISSION_NOT_FOUND = "MISSION_NOT_FOUND"
    QUEUE_ITEM_NOT_FOUND = "QUEUE_ITEM_NOT_FOUND"
    CAPTION_DRAFT_NOT_FOUND = "CAPTION_DRAFT_NOT_FOUND"
    CAPTION_NOT_SUBMITTED = "CAPTION_NOT_SUBMITTED"
    CAPTION_REJECTED = "CAPTION_REJECTED"
    CAPTION_NOT_APPROVED = "CAPTION_NOT_APPROVED"
    ACCOUNT_NOT_SPECIFIED = "ACCOUNT_NOT_SPECIFIED"
    CREATIVE_BRIEF_MISSING = "CREATIVE_BRIEF_MISSING"
    MISSION_ALREADY_COMPLETED = "MISSION_ALREADY_COMPLETED"
    MISSION_FAILED = "MISSION_FAILED"
    MISSION_CANCELLED = "MISSION_CANCELLED"
    MISSION_PAUSED = "MISSION_PAUSED"
    QUEUE_CONTEXT_REQUIRED = "QUEUE_CONTEXT_REQUIRED"
    INFRA_ERROR = "INFRA_ERROR"
    ID_MISMATCH = "ID_MISMATCH"


class MissionPipelineResult(BaseModel):
    """Resultado da execução mission-aware do pipeline."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    mission_id: str
    queue_item_id: Optional[str] = None
    caption_draft_id: Optional[str] = None
    creative_brief_id: Optional[str] = None
    export_package_path: Optional[str] = None
    publisher_draft_id: Optional[str] = None
    status: str = MissionPipelineStatus.SUCCESS
    block_reason: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    events_emitted: List[str] = Field(default_factory=list)
    evidence_refs: List[Dict[str, Any]] = Field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if not self.started_at:
            object.__setattr__(self, "started_at", now)
        if not self.finished_at:
            object.__setattr__(self, "finished_at", now)

    def add_event(self, event_id: str) -> None:
        object.__setattr__(self, "events_emitted", self.events_emitted + [event_id])

    def add_warning(self, warning: str) -> None:
        object.__setattr__(self, "warnings", self.warnings + [warning])

    def add_evidence(self, ref_type: str, ref: str, description: str = "") -> None:
        obj = {"type": ref_type, "ref": ref}
        if description:
            obj["description"] = description
        object.__setattr__(self, "evidence_refs", self.evidence_refs + [obj])
