"""Models for Creative Production OS."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class CreativeBrief:
    """Brief criativo para produção de um conteúdo."""
    creative_brief_id: str
    queue_id: str
    account_handle: str
    format: str  # carrossel, reel, foto, video
    objective: str
    visual_direction: str
    caption_draft_id: Optional[str] = None
    script: str = ""
    shot_list: str = ""
    design_notes: str = ""
    editing_notes: str = ""
    asset_requirements: dict = field(default_factory=dict)
    tool_suggestions: list = field(default_factory=list)
    status: str = "draft"  # draft, approved, rejected, in_production
    warnings: list = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    notes: str = ""

    def __post_init__(self):
        now = datetime.now().isoformat(timespec="seconds")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class ProductionItem:
    """Item na fila de produção criativa."""
    production_id: str
    queue_id: str
    creative_brief_id: str
    asset_type: str  # video, image, carousel_asset
    tool_target: str  # canva, capcut, runway
    status: str = "pending"  # pending, in_progress, done, failed, skipped
    asset_path: Optional[str] = None
    asset_id: Optional[str] = None
    review_notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now().isoformat(timespec="seconds")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class CreativeReview:
    """Registro de revisão de criativo."""
    review_id: str
    creative_brief_id: str
    reviewer: str = "operator"
    status: str = "pending"  # pending, approved, rejected, changes_requested
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now().isoformat(timespec="seconds")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
