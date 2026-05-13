"""Models for Creative Production V2 — deterministic, dry-run, stdlib-only."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _short_id() -> str:
    return str(uuid4())[:8]


# ── Enums ────────────────────────────────────────────────────────────────────

class CreativeFormat(str, Enum):
    CAROUSEL = "carousel"
    REEL = "reel"
    PHOTO = "photo"
    VIDEO = "video"
    STORY = "story"
    MULTI_COPY = "multi_copy"


class CreativeStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PRODUCTION = "in_production"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    READY = "ready"
    ARCHIVED = "archived"


class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT_OVERLAY = "text_overlay"
    LOGO = "logo"
    BACKGROUND = "background"
    THUMBNAIL = "thumbnail"
    CAPTION_CARD = "caption_card"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    FAILED = "failed"


class ReviewVerdict(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


class PackageStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    READY = "ready"
    EXPORTED = "exported"
    ARCHIVED = "archived"


# ── Models ────────────────────────────────────────────────────────────────────

@dataclass
class CreativeRequest:
    """Input request for creative production — the entry point."""
    request_id: str = field(default_factory=_short_id)
    account_handle: str = ""
    format: CreativeFormat = CreativeFormat.CAROUSEL
    topic: str = ""
    objective: str = ""
    tone: str = ""
    target_audience: str = ""
    key_message: str = ""
    visual_style: str = ""
    caption_seed: str = ""
    asset_count: int = 3
    deadline_days: int = 7
    priority: int = 0
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    status: CreativeStatus = CreativeStatus.DRAFT
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["format"] = self.format.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> CreativeRequest:
        data = dict(data)
        if "format" in data and not isinstance(data["format"], CreativeFormat):
            data["format"] = CreativeFormat(data["format"])
        if "status" in data and not isinstance(data["status"], CreativeStatus):
            data["status"] = CreativeStatus(data["status"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CreativeBriefV2:
    """Creative brief v2 — deterministic spec for production."""
    brief_id: str = field(default_factory=_short_id)
    request_id: str = ""
    account_handle: str = ""
    format: CreativeFormat = CreativeFormat.CAROUSEL
    topic: str = ""
    objective: str = ""
    tone: str = ""
    target_audience: str = ""
    key_message: str = ""
    visual_direction: str = ""
    hook_variants: list[str] = field(default_factory=list)
    caption_framework: str = ""  # e.g. "hook → problem → solution → CTA"
    shot_list: list[str] = field(default_factory=list)
    design_notes: str = ""
    editing_notes: str = ""
    music_mood: str = ""
    color_palette: list[str] = field(default_factory=list)
    font_suggestions: list[str] = field(default_factory=list)
    asset_count_target: int = 3
    tool_suggestions: list[str] = field(default_factory=list)
    status: CreativeStatus = CreativeStatus.DRAFT
    warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["format"] = self.format.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> CreativeBriefV2:
        data = dict(data)
        if "format" in data and not isinstance(data["format"], CreativeFormat):
            data["format"] = CreativeFormat(data["format"])
        if "status" in data and not isinstance(data["status"], CreativeStatus):
            data["status"] = CreativeStatus(data["status"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AssetSpec:
    """Specification for a single production asset."""
    asset_index: int = 0
    asset_type: AssetType = AssetType.IMAGE
    description: str = ""
    dimensions: str = "1080x1080"  # WxH
    duration_seconds: float = 0.0
    text_content: str = ""
    source_hint: str = ""  # e.g. "brand_kit/logo.png", "camera", "stock"
    fallback_description: str = ""


@dataclass
class ProductionAssetPlan:
    """Plan describing all assets needed for a creative brief."""
    plan_id: str = field(default_factory=_short_id)
    brief_id: str = ""
    assets: list[AssetSpec] = field(default_factory=list)
    total_estimated_minutes: int = 0
    tool_assignments: dict[str, str] = field(default_factory=dict)
    template_references: dict[str, str] = field(default_factory=dict)
    notes: str = ""
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ProductionAssetPlan:
        data = dict(data)
        assets_raw = data.pop("assets", [])
        plan = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        plan.assets = [
            AssetSpec(**a) if isinstance(a, dict) else a for a in assets_raw
        ]
        return plan


@dataclass
class CreativeTask:
    """Individual creative task — one unit of work for production."""
    task_id: str = field(default_factory=_short_id)
    batch_id: str = ""
    brief_id: str = ""
    asset_index: int = 0
    asset_type: AssetType = AssetType.IMAGE
    description: str = ""
    tool_target: str = ""  # e.g. "canva", "capcut", "manual"
    estimated_minutes: int = 15
    dependencies: list[str] = field(default_factory=list)
    output_filename: str = ""
    status: TaskStatus = TaskStatus.PENDING
    notes: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["asset_type"] = self.asset_type.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> CreativeTask:
        data = dict(data)
        if "asset_type" in data and not isinstance(data["asset_type"], AssetType):
            data["asset_type"] = AssetType(data["asset_type"])
        if "status" in data and not isinstance(data["status"], TaskStatus):
            data["status"] = TaskStatus(data["status"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ProductionBatch:
    """Batch of creative tasks grouped for execution."""
    batch_id: str = field(default_factory=_short_id)
    brief_id: str = ""
    plan_id: str = ""
    tasks: list[CreativeTask] = field(default_factory=list)
    estimated_total_minutes: int = 0
    parallelizable_count: int = 0
    sequential_count: int = 0
    status: CreativeStatus = CreativeStatus.PLANNED
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        d["tasks"] = [t.to_dict() for t in self.tasks]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> ProductionBatch:
        data = dict(data)
        tasks_raw = data.pop("tasks", [])
        if "status" in data and not isinstance(data["status"], CreativeStatus):
            data["status"] = CreativeStatus(data["status"])
        batch = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        batch.tasks = [
            CreativeTask.from_dict(t) if isinstance(t, dict) else t for t in tasks_raw
        ]
        return batch


@dataclass
class ReviewCheckpoint:
    """A single checkpoint in the creative review process."""
    checkpoint_index: int = 0
    label: str = ""  # e.g. "Hook Review", "Visual Consistency", "Brand Safety"
    criteria: list[str] = field(default_factory=list)
    required: bool = True
    auto_pass: bool = False


@dataclass
class CreativeReviewPlan:
    """Review plan for creative work — checkpoints, criteria, verdicts."""
    review_id: str = field(default_factory=_short_id)
    brief_id: str = ""
    checkpoints: list[ReviewCheckpoint] = field(default_factory=list)
    reviewer: str = "operator"
    verdict: ReviewVerdict = ReviewVerdict.PENDING
    notes: str = ""
    changes_needed: list[str] = field(default_factory=list)
    approved_at: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> CreativeReviewPlan:
        data = dict(data)
        checkpoints_raw = data.pop("checkpoints", [])
        if "verdict" in data and not isinstance(data["verdict"], ReviewVerdict):
            data["verdict"] = ReviewVerdict(data["verdict"])
        plan = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        plan.checkpoints = [
            ReviewCheckpoint(**c) if isinstance(c, dict) else c for c in checkpoints_raw
        ]
        return plan


@dataclass
class CreativePackage:
    """Final creative package bundling brief, asset plan, batch, and review."""
    package_id: str = field(default_factory=_short_id)
    brief: Optional[CreativeBriefV2] = None
    asset_plan: Optional[ProductionAssetPlan] = None
    batch: Optional[ProductionBatch] = None
    review_plan: Optional[CreativeReviewPlan] = None
    status: PackageStatus = PackageStatus.DRAFT
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        d = {
            "package_id": self.package_id,
            "status": self.status.value,
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.brief:
            d["brief"] = self.brief.to_dict()
        if self.asset_plan:
            d["asset_plan"] = self.asset_plan.to_dict()
        if self.batch:
            d["batch"] = self.batch.to_dict()
        if self.review_plan:
            d["review_plan"] = self.review_plan.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> CreativePackage:
        data = dict(data)
        if "status" in data and not isinstance(data["status"], PackageStatus):
            data["status"] = PackageStatus(data["status"])
        brief = data.pop("brief", None)
        asset_plan = data.pop("asset_plan", None)
        batch = data.pop("batch", None)
        review_plan = data.pop("review_plan", None)
        pkg = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        if brief:
            pkg.brief = CreativeBriefV2.from_dict(brief) if isinstance(brief, dict) else brief
        if asset_plan:
            pkg.asset_plan = ProductionAssetPlan.from_dict(asset_plan) if isinstance(asset_plan, dict) else asset_plan
        if batch:
            pkg.batch = ProductionBatch.from_dict(batch) if isinstance(batch, dict) else batch
        if review_plan:
            pkg.review_plan = CreativeReviewPlan.from_dict(review_plan) if isinstance(review_plan, dict) else review_plan
        return pkg
