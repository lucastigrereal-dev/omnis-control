"""Backlog data models."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ItemType(str, Enum):
    MISSION = "mission"
    REVIEW = "review"
    APPROVAL = "approval"
    ASSET = "asset"


class ItemStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class BacklogItem:
    item_id: str
    item_type: ItemType
    title: str
    description: str = ""
    priority: int = 3  # 1 (highest) to 5 (lowest)
    status: ItemStatus = ItemStatus.PENDING
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

    def to_dict(self) -> dict:
        d = asdict(self)
        d["item_type"] = self.item_type.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> BacklogItem:
        return cls(
            item_id=d["item_id"],
            item_type=ItemType(d["item_type"]),
            title=d["title"],
            description=d.get("description", ""),
            priority=d.get("priority", 3),
            status=ItemStatus(d.get("status", "pending")),
            tags=d.get("tags", []),
            metadata=d.get("metadata", {}),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )


@dataclass
class BacklogQueue:
    name: str
    items: list[BacklogItem] = field(default_factory=list)

    @property
    def pending(self) -> list[BacklogItem]:
        return [i for i in self.items if i.status == ItemStatus.PENDING]

    @property
    def in_progress(self) -> list[BacklogItem]:
        return [i for i in self.items if i.status == ItemStatus.IN_PROGRESS]

    @property
    def blocked(self) -> list[BacklogItem]:
        return [i for i in self.items if i.status == ItemStatus.BLOCKED]

    def by_priority(self, items: Optional[list[BacklogItem]] = None) -> list[BacklogItem]:
        return sorted(items if items is not None else self.items, key=lambda i: (i.priority, i.created_at))

    def next(self) -> Optional[BacklogItem]:
        pending = self.by_priority(self.pending)
        return pending[0] if pending else None

    def to_dict(self) -> dict:
        return {"name": self.name, "items": [i.to_dict() for i in self.items]}

    @classmethod
    def from_dict(cls, d: dict) -> BacklogQueue:
        return cls(
            name=d["name"],
            items=[BacklogItem.from_dict(i) for i in d.get("items", [])],
        )
