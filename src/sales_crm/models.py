"""P10 Sales/CRM — deterministic models (dataclasses, zero Pydantic)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any


# ═══════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════

class PipelineStage(Enum):
    """Sales pipeline stages — linear progression."""
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

    @classmethod
    def active_stages(cls) -> list[PipelineStage]:
        return [s for s in cls if s not in {cls.CLOSED_WON, cls.CLOSED_LOST}]

    @classmethod
    def terminal_stages(cls) -> list[PipelineStage]:
        return [cls.CLOSED_WON, cls.CLOSED_LOST]


class LeadSource(Enum):
    """Where the lead originated."""
    INSTAGRAM = "instagram"
    DIRECT_CONTACT = "direct_contact"
    REFERRAL = "referral"
    INBOUND = "inbound"
    MANUAL_PROSPECTING = "manual_prospecting"
    UNKNOWN = "unknown"


class LeadStatus(Enum):
    """Lead qualification status."""
    NEW = "new"
    ATTEMPTED_CONTACT = "attempted_contact"
    ENGAGED = "engaged"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"


class ActivityType(Enum):
    """Types of sales activities — all dry-run."""
    CALL = "call"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    DM = "dm"
    MEETING = "meeting"
    FOLLOW_UP = "follow_up"
    NOTE = "note"


class ObjectionCategory(Enum):
    """Common objection categories in hotel/restaurant sales."""
    PRICE = "price"
    TIMING = "timing"
    COMPETITOR = "competitor"
    NEED = "need"
    AUTHORITY = "authority"
    TRUST = "trust"
    BUDGET = "budget"
    OTHER = "other"


class DealPriority(Enum):
    """Deal priority for pipeline triage."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class FollowUpStatus(Enum):
    """Follow-up task lifecycle."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProposalStatus(Enum):
    """Proposal lifecycle."""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

VALID_PACKAGES = frozenset({"starter", "growth", "premium"})
VALID_PACKAGE_PRICES = frozenset({"starter": 350, "growth": 990, "premium": 1200}.items())


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_id(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


# ═══════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════

@dataclass
class Lead:
    """A potential customer — hotel, restaurant, or tourism business."""

    id: str
    name: str
    business_name: str | None
    contact_phone: str | None
    contact_email: str | None
    instagram_handle: str | None
    source: LeadSource
    status: LeadStatus
    score: float = 0.0
    tags: list[str] = field(default_factory=list)
    notes: str | None = None
    city: str | None = None
    state: str | None = None
    niche: str | None = None
    follower_count: int | None = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    dry_run: bool = True

    @classmethod
    def new(
        cls,
        name: str,
        source: LeadSource = LeadSource.UNKNOWN,
        business_name: str | None = None,
        contact_phone: str | None = None,
        contact_email: str | None = None,
        instagram_handle: str | None = None,
        city: str | None = None,
        state: str | None = None,
        niche: str | None = None,
        follower_count: int | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> Lead:
        if not name.strip():
            raise ValueError("Lead name is required.")
        return cls(
            id=_short_id("lead_"),
            name=name.strip(),
            business_name=business_name.strip() if business_name else None,
            contact_phone=contact_phone.strip() if contact_phone else None,
            contact_email=contact_email.strip() if contact_email else None,
            instagram_handle=instagram_handle.strip() if instagram_handle else None,
            source=source,
            status=LeadStatus.NEW,
            score=0.0,
            tags=tags or [],
            notes=notes,
            city=city.strip() if city else None,
            state=state.strip() if state else None,
            niche=niche.strip() if niche else None,
            follower_count=follower_count,
        )

    @property
    def has_contact_info(self) -> bool:
        return bool(self.contact_phone or self.contact_email or self.instagram_handle)

    @property
    def is_qualified(self) -> bool:
        return self.status == LeadStatus.QUALIFIED

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "business_name": self.business_name,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "instagram_handle": self.instagram_handle,
            "source": self.source.value,
            "status": self.status.value,
            "score": self.score,
            "tags": self.tags,
            "notes": self.notes,
            "city": self.city,
            "state": self.state,
            "niche": self.niche,
            "follower_count": self.follower_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Lead:
        return cls(
            id=data["id"],
            name=data["name"],
            business_name=data.get("business_name"),
            contact_phone=data.get("contact_phone"),
            contact_email=data.get("contact_email"),
            instagram_handle=data.get("instagram_handle"),
            source=LeadSource(data.get("source", "unknown")),
            status=LeadStatus(data.get("status", "new")),
            score=data.get("score", 0.0),
            tags=data.get("tags", []),
            notes=data.get("notes"),
            city=data.get("city"),
            state=data.get("state"),
            niche=data.get("niche"),
            follower_count=data.get("follower_count"),
            created_at=data.get("created_at", _now_iso()),
            updated_at=data.get("updated_at", _now_iso()),
            dry_run=data.get("dry_run", True),
        )

    def to_json(self, path: str | Path) -> Path:
        p = Path(path)
        p.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return p

    @classmethod
    def from_json(cls, path: str | Path) -> Lead:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)


@dataclass
class Deal:
    """A deal linked to a lead — tracks value, stage, and probability."""

    id: str
    lead_id: str
    package: str
    value_brl: float
    stage: PipelineStage
    priority: DealPriority
    probability: float
    expected_close_date: str | None
    tags: list[str] = field(default_factory=list)
    notes: str | None = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    dry_run: bool = True

    @classmethod
    def new(
        cls,
        lead_id: str,
        package: str = "growth",
        stage: PipelineStage = PipelineStage.PROSPECTING,
        priority: DealPriority = DealPriority.MEDIUM,
        probability: float | None = None,
        expected_close_date: str | None = None,
        tags: list[str] | None = None,
        notes: str | None = None,
    ) -> Deal:
        if package not in VALID_PACKAGES:
            raise ValueError(
                f"Invalid package '{package}'. Valid: {sorted(VALID_PACKAGES)}"
            )
        prices = {"starter": 350, "growth": 990, "premium": 1200}
        value = prices[package]
        if probability is None:
            probability = cls._default_probability(stage)
        return cls(
            id=_short_id("deal_"),
            lead_id=lead_id,
            package=package,
            value_brl=float(value),
            stage=stage,
            priority=priority,
            probability=probability,
            expected_close_date=expected_close_date,
            tags=tags or [],
            notes=notes,
        )

    @staticmethod
    def _default_probability(stage: PipelineStage) -> float:
        mapping = {
            PipelineStage.PROSPECTING: 0.10,
            PipelineStage.QUALIFICATION: 0.30,
            PipelineStage.PROPOSAL: 0.50,
            PipelineStage.NEGOTIATION: 0.70,
            PipelineStage.CLOSED_WON: 1.0,
            PipelineStage.CLOSED_LOST: 0.0,
        }
        return mapping[stage]

    @property
    def expected_value(self) -> float:
        return self.value_brl * self.probability

    @property
    def is_active(self) -> bool:
        return self.stage not in PipelineStage.terminal_stages()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "package": self.package,
            "value_brl": self.value_brl,
            "stage": self.stage.value,
            "priority": self.priority.value,
            "probability": self.probability,
            "expected_close_date": self.expected_close_date,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Deal:
        return cls(
            id=data["id"],
            lead_id=data["lead_id"],
            package=data.get("package", "growth"),
            value_brl=data.get("value_brl", 0),
            stage=PipelineStage(data.get("stage", "prospecting")),
            priority=DealPriority(data.get("priority", "medium")),
            probability=data.get("probability", 0.10),
            expected_close_date=data.get("expected_close_date"),
            tags=data.get("tags", []),
            notes=data.get("notes"),
            created_at=data.get("created_at", _now_iso()),
            updated_at=data.get("updated_at", _now_iso()),
            dry_run=data.get("dry_run", True),
        )


@dataclass
class SalesActivity:
    """A logged sales activity — all dry-run, no real sending."""

    id: str
    lead_id: str | None
    deal_id: str | None
    activity_type: ActivityType
    description: str
    outcome: str | None
    performed_at: str = field(default_factory=_now_iso)
    dry_run: bool = True
    approval_required: bool = False
    approved: bool = False
    risk_flags: list[str] = field(default_factory=list)

    @classmethod
    def new(
        cls,
        activity_type: ActivityType,
        description: str,
        lead_id: str | None = None,
        deal_id: str | None = None,
        outcome: str | None = None,
    ) -> SalesActivity:
        approval = activity_type in {
            ActivityType.CALL,
            ActivityType.WHATSAPP,
            ActivityType.EMAIL,
            ActivityType.DM,
        }
        risk_flags: list[str] = []
        if approval:
            risk_flags.append("external_contact_blocked")
        return cls(
            id=_short_id("act_"),
            lead_id=lead_id,
            deal_id=deal_id,
            activity_type=activity_type,
            description=description,
            outcome=outcome,
            approval_required=approval,
            approved=False,
            risk_flags=risk_flags,
        )

    @property
    def is_external(self) -> bool:
        return self.activity_type in {
            ActivityType.CALL,
            ActivityType.WHATSAPP,
            ActivityType.EMAIL,
            ActivityType.DM,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "deal_id": self.deal_id,
            "activity_type": self.activity_type.value,
            "description": self.description,
            "outcome": self.outcome,
            "performed_at": self.performed_at,
            "dry_run": self.dry_run,
            "approval_required": self.approval_required,
            "approved": self.approved,
            "risk_flags": self.risk_flags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SalesActivity:
        return cls(
            id=data["id"],
            lead_id=data.get("lead_id"),
            deal_id=data.get("deal_id"),
            activity_type=ActivityType(data["activity_type"]),
            description=data["description"],
            outcome=data.get("outcome"),
            performed_at=data.get("performed_at", _now_iso()),
            dry_run=data.get("dry_run", True),
            approval_required=data.get("approval_required", False),
            approved=data.get("approved", False),
            risk_flags=data.get("risk_flags", []),
        )


@dataclass
class ObjectionRecord:
    """A recorded objection during a sales conversation."""

    id: str
    lead_id: str | None
    deal_id: str | None
    category: ObjectionCategory
    description: str
    response: str | None
    resolved: bool = False
    resolved_at: str | None = None
    created_at: str = field(default_factory=_now_iso)
    dry_run: bool = True

    @classmethod
    def new(
        cls,
        category: ObjectionCategory,
        description: str,
        lead_id: str | None = None,
        deal_id: str | None = None,
        response: str | None = None,
    ) -> ObjectionRecord:
        return cls(
            id=_short_id("obj_"),
            lead_id=lead_id,
            deal_id=deal_id,
            category=category,
            description=description,
            response=response,
        )

    def resolve(self, response: str | None = None) -> None:
        self.resolved = True
        self.resolved_at = _now_iso()
        if response:
            self.response = response

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "deal_id": self.deal_id,
            "category": self.category.value,
            "description": self.description,
            "response": self.response,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ObjectionRecord:
        return cls(
            id=data["id"],
            lead_id=data.get("lead_id"),
            deal_id=data.get("deal_id"),
            category=ObjectionCategory(data["category"]),
            description=data["description"],
            response=data.get("response"),
            resolved=data.get("resolved", False),
            resolved_at=data.get("resolved_at"),
            created_at=data.get("created_at", _now_iso()),
            dry_run=data.get("dry_run", True),
        )


@dataclass
class ProposalRecord:
    """A proposal sent (or to be sent) to a lead."""

    id: str
    lead_id: str | None
    deal_id: str | None
    package: str
    value_brl: float
    status: ProposalStatus
    content_summary: str | None
    sent_at: str | None
    valid_until: str | None
    created_at: str = field(default_factory=_now_iso)
    dry_run: bool = True
    approval_required: bool = True

    @classmethod
    def new(
        cls,
        package: str,
        lead_id: str | None = None,
        deal_id: str | None = None,
        content_summary: str | None = None,
        valid_until: str | None = None,
    ) -> ProposalRecord:
        if package not in VALID_PACKAGES:
            raise ValueError(
                f"Invalid package '{package}'. Valid: {sorted(VALID_PACKAGES)}"
            )
        prices = {"starter": 350, "growth": 990, "premium": 1200}
        return cls(
            id=_short_id("prop_"),
            lead_id=lead_id,
            deal_id=deal_id,
            package=package,
            value_brl=float(prices[package]),
            status=ProposalStatus.DRAFT,
            content_summary=content_summary,
            sent_at=None,
            valid_until=valid_until,
        )

    @property
    def is_sent(self) -> bool:
        return self.status in {ProposalStatus.SENT, ProposalStatus.VIEWED,
                                ProposalStatus.ACCEPTED, ProposalStatus.DECLINED}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "deal_id": self.deal_id,
            "package": self.package,
            "value_brl": self.value_brl,
            "status": self.status.value,
            "content_summary": self.content_summary,
            "sent_at": self.sent_at,
            "valid_until": self.valid_until,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
            "approval_required": self.approval_required,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProposalRecord:
        return cls(
            id=data["id"],
            lead_id=data.get("lead_id"),
            deal_id=data.get("deal_id"),
            package=data.get("package", "growth"),
            value_brl=data.get("value_brl", 0),
            status=ProposalStatus(data.get("status", "draft")),
            content_summary=data.get("content_summary"),
            sent_at=data.get("sent_at"),
            valid_until=data.get("valid_until"),
            created_at=data.get("created_at", _now_iso()),
            dry_run=data.get("dry_run", True),
            approval_required=data.get("approval_required", True),
        )


@dataclass
class FollowUpTask:
    """A scheduled follow-up task for a lead or deal."""

    id: str
    lead_id: str | None
    deal_id: str | None
    description: str
    scheduled_at: str
    status: FollowUpStatus
    completed_at: str | None
    notes: str | None
    created_at: str = field(default_factory=_now_iso)
    dry_run: bool = True

    @classmethod
    def new(
        cls,
        description: str,
        scheduled_at: str,
        lead_id: str | None = None,
        deal_id: str | None = None,
        notes: str | None = None,
    ) -> FollowUpTask:
        return cls(
            id=_short_id("fup_"),
            lead_id=lead_id,
            deal_id=deal_id,
            description=description,
            scheduled_at=scheduled_at,
            status=FollowUpStatus.PENDING,
            completed_at=None,
            notes=notes,
        )

    @property
    def is_overdue(self) -> bool:
        if self.status in {FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED}:
            return False
        return self.scheduled_at < _now_iso()

    def complete(self, notes: str | None = None) -> None:
        self.status = FollowUpStatus.COMPLETED
        self.completed_at = _now_iso()
        if notes:
            self.notes = notes

    def cancel(self, notes: str | None = None) -> None:
        self.status = FollowUpStatus.CANCELLED
        if notes:
            self.notes = notes

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "deal_id": self.deal_id,
            "description": self.description,
            "scheduled_at": self.scheduled_at,
            "status": self.status.value,
            "completed_at": self.completed_at,
            "notes": self.notes,
            "created_at": self.created_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FollowUpTask:
        return cls(
            id=data["id"],
            lead_id=data.get("lead_id"),
            deal_id=data.get("deal_id"),
            description=data["description"],
            scheduled_at=data["scheduled_at"],
            status=FollowUpStatus(data.get("status", "pending")),
            completed_at=data.get("completed_at"),
            notes=data.get("notes"),
            created_at=data.get("created_at", _now_iso()),
            dry_run=data.get("dry_run", True),
        )


@dataclass
class SalesPipeline:
    """Aggregated view of the sales pipeline — stages + deals + summary."""

    id: str
    name: str
    description: str
    deals: list[Deal] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    dry_run: bool = True

    @classmethod
    def new(
        cls,
        name: str,
        description: str,
        deals: list[Deal] | None = None,
    ) -> SalesPipeline:
        return cls(
            id=_short_id("pipe_"),
            name=name,
            description=description,
            deals=deals or [],
        )

    @property
    def active_deals(self) -> list[Deal]:
        return [d for d in self.deals if d.is_active]

    @property
    def total_value(self) -> float:
        return sum(d.value_brl for d in self.deals)

    @property
    def weighted_value(self) -> float:
        return sum(d.expected_value for d in self.deals)

    @property
    def deal_count(self) -> int:
        return len(self.deals)

    @property
    def active_count(self) -> int:
        return len(self.active_deals)

    def count_by_stage(self, stage: PipelineStage) -> int:
        return sum(1 for d in self.deals if d.stage == stage)

    def value_by_stage(self, stage: PipelineStage) -> float:
        return sum(d.value_brl for d in self.deals if d.stage == stage)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "deals": [d.to_dict() for d in self.deals],
            "total_value": self.total_value,
            "weighted_value": self.weighted_value,
            "deal_count": self.deal_count,
            "active_count": self.active_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "dry_run": self.dry_run,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SalesPipeline:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            deals=[Deal.from_dict(d) for d in data.get("deals", [])],
            created_at=data.get("created_at", _now_iso()),
            updated_at=data.get("updated_at", _now_iso()),
            dry_run=data.get("dry_run", True),
        )
