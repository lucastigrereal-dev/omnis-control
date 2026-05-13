"""P19 Campaign Manager — deterministic dataclass models.

Zero LLM. Zero network. Zero database. Stdlib only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from src.campaign_manager.errors import BudgetError, StateTransitionError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# CampaignStatus Enum — exactly 6 states per Control Tower
# ---------------------------------------------------------------------------


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ANALYZED = "analyzed"
    ARCHIVED = "archived"


# ---------------------------------------------------------------------------
# Valid state transitions (Control Tower approved)
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[CampaignStatus, frozenset[CampaignStatus]] = {
    CampaignStatus.DRAFT: frozenset({CampaignStatus.PLANNED, CampaignStatus.ARCHIVED}),
    CampaignStatus.PLANNED: frozenset({CampaignStatus.IN_PROGRESS, CampaignStatus.ARCHIVED}),
    CampaignStatus.IN_PROGRESS: frozenset({CampaignStatus.COMPLETED, CampaignStatus.ARCHIVED}),
    CampaignStatus.COMPLETED: frozenset({CampaignStatus.ANALYZED, CampaignStatus.ARCHIVED}),
    CampaignStatus.ANALYZED: frozenset({CampaignStatus.ARCHIVED}),
    CampaignStatus.ARCHIVED: frozenset(),
}

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass
class BudgetTracker:
    """Tracks campaign budget: allocated, spent, and breakdown by category."""

    budget_id: str
    campaign_ref: str
    total_budget_brl: float
    allocated_brl: float
    spent_brl: float
    breakdown: list[dict] = field(default_factory=list)
    currency: str = "BRL"
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        campaign_ref: str,
        total_budget_brl: float,
        breakdown: Optional[list[dict]] = None,
        currency: str = "BRL",
    ) -> "BudgetTracker":
        if total_budget_brl <= 0:
            raise BudgetError("total_budget_brl must be > 0")
        return cls(
            budget_id=_new_id("bud_"),
            campaign_ref=campaign_ref,
            total_budget_brl=total_budget_brl,
            allocated_brl=total_budget_brl,
            spent_brl=0.0,
            breakdown=breakdown or [],
            currency=currency,
        )

    def to_dict(self) -> dict:
        return {
            "budget_id": self.budget_id,
            "campaign_ref": self.campaign_ref,
            "total_budget_brl": self.total_budget_brl,
            "allocated_brl": self.allocated_brl,
            "spent_brl": self.spent_brl,
            "breakdown": list(self.breakdown),
            "currency": self.currency,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BudgetTracker":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @property
    def remaining_brl(self) -> float:
        return self.total_budget_brl - self.spent_brl

    @property
    def is_over_budget(self) -> bool:
        return self.spent_brl > self.total_budget_brl


@dataclass
class ROICalculation:
    """ROI calculation: projected and actual revenue/cost/ROI%."""

    roi_id: str
    campaign_ref: str
    projected_revenue_brl: float
    projected_cost_brl: float
    projected_roi_percent: Optional[float] = None
    actual_revenue_brl: Optional[float] = None
    actual_cost_brl: Optional[float] = None
    actual_roi_percent: Optional[float] = None
    formula: str = "(revenue - cost) / cost * 100"
    calculated_at: Optional[str] = None
    notes: str = ""

    @classmethod
    def new(
        cls,
        campaign_ref: str,
        projected_revenue_brl: float,
        projected_cost_brl: float = 0.0,
        notes: str = "",
    ) -> "ROICalculation":
        projected_roi = None
        if projected_cost_brl > 0:
            projected_roi = round(
                (projected_revenue_brl - projected_cost_brl) / projected_cost_brl * 100, 2
            )
        return cls(
            roi_id=_new_id("roi_"),
            campaign_ref=campaign_ref,
            projected_revenue_brl=projected_revenue_brl,
            projected_cost_brl=projected_cost_brl,
            projected_roi_percent=projected_roi,
            notes=notes,
        )

    def to_dict(self) -> dict:
        return {
            "roi_id": self.roi_id,
            "campaign_ref": self.campaign_ref,
            "projected_revenue_brl": self.projected_revenue_brl,
            "projected_cost_brl": self.projected_cost_brl,
            "projected_roi_percent": self.projected_roi_percent,
            "actual_revenue_brl": self.actual_revenue_brl,
            "actual_cost_brl": self.actual_cost_brl,
            "actual_roi_percent": self.actual_roi_percent,
            "formula": self.formula,
            "calculated_at": self.calculated_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ROICalculation":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @property
    def roi_label(self) -> str:
        if self.actual_roi_percent is not None:
            roi = self.actual_roi_percent
        elif self.projected_roi_percent is not None:
            roi = self.projected_roi_percent
        else:
            return "N/A"
        return f"{roi:.1f}%"


@dataclass
class Campaign:
    """Central entity: orchestrated campaign connecting marketing, publishing, and analytics."""

    campaign_id: str
    campaign_name: str
    brief_ref: str
    status: CampaignStatus
    channels: list[dict] = field(default_factory=list)
    budget: Optional[BudgetTracker] = None
    roi: Optional[ROICalculation] = None
    metrics_plan: dict = field(default_factory=dict)
    timeline: dict = field(default_factory=dict)
    publish_queue_plan_ref: Optional[str] = None
    dry_run: bool = True
    approval_required: bool = True
    retry_count: int = 0
    error_message: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    @classmethod
    def new(
        cls,
        campaign_name: str,
        brief_ref: str,
        channels: Optional[list[dict]] = None,
        budget: Optional[BudgetTracker] = None,
        roi: Optional[ROICalculation] = None,
        metrics_plan: Optional[dict] = None,
        deadline: Optional[str] = None,
        tags: Optional[list[str]] = None,
        dry_run: bool = True,
        approval_required: bool = True,
    ) -> "Campaign":
        if not channels:
            raise BudgetError("brief must define at least 1 channel")

        tl = {
            "created_at": _now_iso(),
            "deadline": deadline,
            "started_at": None,
            "completed_at": None,
            "analyzed_at": None,
            "archived_at": None,
        }

        return cls(
            campaign_id=_new_id("cmp_"),
            campaign_name=campaign_name,
            brief_ref=brief_ref,
            status=CampaignStatus.DRAFT,
            channels=channels or [],
            budget=budget,
            roi=roi,
            metrics_plan=metrics_plan or {},
            timeline=tl,
            tags=tags or [],
            dry_run=dry_run,
            approval_required=approval_required,
        )

    def to_dict(self) -> dict:
        return {
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "brief_ref": self.brief_ref,
            "status": self.status.value,
            "channels": list(self.channels),
            "budget": self.budget.to_dict() if self.budget else None,
            "roi": self.roi.to_dict() if self.roi else None,
            "metrics_plan": dict(self.metrics_plan),
            "timeline": dict(self.timeline),
            "publish_queue_plan_ref": self.publish_queue_plan_ref,
            "dry_run": self.dry_run,
            "approval_required": self.approval_required,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Campaign":
        fields = {}
        for k in cls.__dataclass_fields__:
            if k in data:
                fields[k] = data[k]

        if "status" in fields and isinstance(fields["status"], str):
            fields["status"] = CampaignStatus(fields["status"])
        if "budget" in fields and isinstance(fields["budget"], dict):
            fields["budget"] = BudgetTracker.from_dict(fields["budget"])
        if "roi" in fields and isinstance(fields["roi"], dict):
            fields["roi"] = ROICalculation.from_dict(fields["roi"])

        return cls(**fields)

    def transition_to(self, target: CampaignStatus) -> None:
        valid = VALID_TRANSITIONS.get(self.status, frozenset())
        if target not in valid:
            raise StateTransitionError(
                f"invalid transition from {self.status.value} to {target.value}"
            )

        now = _now_iso()
        if target == CampaignStatus.IN_PROGRESS:
            self.timeline["started_at"] = now
        elif target == CampaignStatus.COMPLETED:
            self.timeline["completed_at"] = now
        elif target == CampaignStatus.ANALYZED:
            self.timeline["analyzed_at"] = now
        elif target == CampaignStatus.ARCHIVED:
            self.timeline["archived_at"] = now

        self.status = target
