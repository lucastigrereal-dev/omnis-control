"""P17 Delivery Portal — deterministic models (stdlib dataclasses, in-memory only)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from src.publisher_argos.models import PublisherHandoff
from src.sales_crm.models import Deal


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_id(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


VALID_FEEDBACK_TYPES = {"approved", "adjustment", "complaint", "ack"}


class DeliveryStatus(str, Enum):
    """Control Tower defined — exactly 5 states."""

    PENDING_DELIVERY = "pending_delivery"
    DELIVERED = "delivered"
    VIEWED = "viewed"
    FEEDBACK_RECEIVED = "feedback_received"
    CLOSED = "closed"


# Valid state transitions (current → allowed targets)
_VALID_TRANSITIONS: dict[DeliveryStatus, set[DeliveryStatus]] = {
    DeliveryStatus.PENDING_DELIVERY: {DeliveryStatus.DELIVERED},
    DeliveryStatus.DELIVERED: {DeliveryStatus.VIEWED},
    DeliveryStatus.VIEWED: {DeliveryStatus.FEEDBACK_RECEIVED},
    DeliveryStatus.FEEDBACK_RECEIVED: {DeliveryStatus.CLOSED},
    DeliveryStatus.CLOSED: set(),
}


def is_valid_transition(current: DeliveryStatus, target: DeliveryStatus) -> bool:
    return target in _VALID_TRANSITIONS.get(current, set())


@dataclass
class FeedbackItem:
    """A single feedback record from the client about a delivery."""

    feedback_id: str = ""
    delivery_id: str = ""
    feedback_type: str = "ack"
    comment: str = ""
    requires_revision: bool = False
    recorded_at: str = field(default_factory=_now_iso)
    recorded_by: str = "local_user"

    def __post_init__(self):
        if self.feedback_type not in VALID_FEEDBACK_TYPES:
            raise ValueError(
                f"Invalid feedback_type '{self.feedback_type}'. "
                f"Valid: {sorted(VALID_FEEDBACK_TYPES)}"
            )

    @classmethod
    def new(
        cls,
        delivery_id: str,
        feedback_type: str = "ack",
        comment: str = "",
        requires_revision: bool = False,
        recorded_by: str = "local_user",
    ) -> FeedbackItem:
        return cls(
            feedback_id=_short_id("fbk_"),
            delivery_id=delivery_id,
            feedback_type=feedback_type,
            comment=comment,
            requires_revision=requires_revision,
            recorded_at=_now_iso(),
            recorded_by=recorded_by,
        )

    def to_dict(self) -> dict:
        return {
            "feedback_id": self.feedback_id,
            "delivery_id": self.delivery_id,
            "feedback_type": self.feedback_type,
            "comment": self.comment,
            "requires_revision": self.requires_revision,
            "recorded_at": self.recorded_at,
            "recorded_by": self.recorded_by,
        }

    @classmethod
    def from_dict(cls, data: dict) -> FeedbackItem:
        return cls(
            feedback_id=data.get("feedback_id", ""),
            delivery_id=data.get("delivery_id", ""),
            feedback_type=data.get("feedback_type", "ack"),
            comment=data.get("comment", ""),
            requires_revision=data.get("requires_revision", False),
            recorded_at=data.get("recorded_at", ""),
            recorded_by=data.get("recorded_by", "local_user"),
        )


@dataclass
class DeliveryPackage:
    """Encapsulates a PublisherHandoff + Deal into a trackable delivery."""

    package_id: str = ""
    delivery_id: str = ""
    status: DeliveryStatus = DeliveryStatus.PENDING_DELIVERY
    handoff: PublisherHandoff = field(default_factory=PublisherHandoff)
    deal: Deal = field(default_factory=lambda: Deal.new(lead_id=""))
    feedback: list[FeedbackItem] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    created_by: str = "local_user"
    dry_run: bool = True
    approval_required: bool = True

    @classmethod
    def new(
        cls,
        handoff: PublisherHandoff,
        deal: Deal,
        *,
        created_by: str = "local_user",
        dry_run: bool = True,
        approval_required: bool = True,
    ) -> DeliveryPackage:
        return cls(
            package_id=_short_id("pkg_"),
            delivery_id=_short_id("dlv_"),
            status=DeliveryStatus.PENDING_DELIVERY,
            handoff=handoff,
            deal=deal,
            feedback=[],
            created_at=_now_iso(),
            created_by=created_by,
            dry_run=dry_run,
            approval_required=approval_required,
        )

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "delivery_id": self.delivery_id,
            "status": self.status.value,
            "handoff": self.handoff.to_dict(),
            "deal": self.deal.to_dict(),
            "feedback": [f.to_dict() for f in self.feedback],
            "created_at": self.created_at,
            "created_by": self.created_by,
            "dry_run": self.dry_run,
            "approval_required": self.approval_required,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DeliveryPackage:
        feedback_items = [
            FeedbackItem.from_dict(f) for f in data.get("feedback", [])
        ]
        handoff_data = data.get("handoff", {})
        handoff = PublisherHandoff(
            id=handoff_data.get("handoff_id", ""),
            source_module=handoff_data.get("source_module", "publisher_argos"),
            target_system=handoff_data.get("target_system", "ARGOS"),
            approval_required=handoff_data.get("approval_required", True),
            approved_by=handoff_data.get("approved_by"),
            dry_run=handoff_data.get("dry_run", True),
            notes=handoff_data.get("notes", ""),
        )
        deal = Deal.from_dict(data.get("deal", {}))
        return cls(
            package_id=data.get("package_id", ""),
            delivery_id=data.get("delivery_id", ""),
            status=DeliveryStatus(data.get("status", "pending_delivery")),
            handoff=handoff,
            deal=deal,
            feedback=feedback_items,
            created_at=data.get("created_at", ""),
            created_by=data.get("created_by", "local_user"),
            dry_run=data.get("dry_run", True),
            approval_required=data.get("approval_required", True),
        )
