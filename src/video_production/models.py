"""Video Production Plan models."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class SlotStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    PRODUCED = "produced"
    SKIPPED = "skipped"


class PlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DONE = "done"
    ARCHIVED = "archived"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ProductionSlot:
    slot_id: str
    date: str            # YYYY-MM-DD
    format: str          # reel | carousel | static | story
    status: SlotStatus = SlotStatus.PENDING
    asset_id: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "slot_id": self.slot_id,
            "date": self.date,
            "format": self.format,
            "status": self.status.value,
            "asset_id": self.asset_id,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProductionSlot":
        data = dict(data)
        data["status"] = SlotStatus(data.get("status", "pending"))
        return cls(**data)


@dataclass
class VideoProductionPlan:
    plan_id: str
    account_handle: str
    format: str
    quantity: int
    days_ahead: int
    status: PlanStatus = PlanStatus.DRAFT
    slots: list[ProductionSlot] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        account_handle: str,
        format: str,
        quantity: int,
        days_ahead: int,
    ) -> "VideoProductionPlan":
        return cls(
            plan_id=f"vplan_{uuid.uuid4().hex[:8]}",
            account_handle=account_handle.lstrip("@").lower(),
            format=format,
            quantity=quantity,
            days_ahead=days_ahead,
        )

    def pending_count(self) -> int:
        return sum(1 for s in self.slots if s.status == SlotStatus.PENDING)

    def assigned_count(self) -> int:
        return sum(1 for s in self.slots if s.status == SlotStatus.ASSIGNED)

    def produced_count(self) -> int:
        return sum(1 for s in self.slots if s.status == SlotStatus.PRODUCED)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "account_handle": self.account_handle,
            "format": self.format,
            "quantity": self.quantity,
            "days_ahead": self.days_ahead,
            "status": self.status.value,
            "slots": [s.to_dict() for s in self.slots],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VideoProductionPlan":
        data = dict(data)
        data["status"] = PlanStatus(data.get("status", "draft"))
        slots_raw = data.pop("slots", [])
        obj = cls(**data)
        obj.slots = [ProductionSlot.from_dict(s) for s in slots_raw]
        return obj
