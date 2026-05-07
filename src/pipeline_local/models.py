"""Modelos do Pipeline Local Dry-Run."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


class PipelineRunStatus:
    SUCCESS = "success"
    BLOCKED = "blocked"
    FAILED = "failed"
    SUCCESS_WITH_WARNINGS = "success_with_warnings"


class PipelineBlockReason:
    QUEUE_ITEM_NOT_FOUND = "QUEUE_ITEM_NOT_FOUND"
    CAPTION_NOT_FOUND = "CAPTION_NOT_FOUND"
    CAPTION_NOT_APPROVED = "CAPTION_NOT_APPROVED"
    BRIEF_FAILED = "BRIEF_FAILED"
    EXPORT_FAILED = "EXPORT_FAILED"
    PUBLISHER_FAILED = "PUBLISHER_FAILED"


@dataclass
class PipelineRunResult:
    """Resultado estruturado de uma execução do pipeline local."""
    run_id: str
    queue_item_id: str
    caption_draft_id: Optional[str] = None
    creative_brief_id: Optional[str] = None
    export_package_path: Optional[str] = None
    publisher_draft_id: Optional[str] = None
    status: str = PipelineRunStatus.SUCCESS
    warnings: list = field(default_factory=list)
    block_reason: Optional[str] = None
    evidence_refs: list = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if not self.started_at:
            self.started_at = now
        if not self.finished_at:
            self.finished_at = now

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineRunResult":
        return cls(**data)
