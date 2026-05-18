"""Backlog Manager — file-backed queue operations."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Optional

from .models import BacklogItem, BacklogQueue, ItemStatus, ItemType


class BacklogManager:
    """Manage a local backlog queue with JSON file persistence."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir or Path(os.getcwd()) / "data")
        self.file_path = self.data_dir / "backlog.json"
        self.queue = BacklogQueue(name="omnis-backlog")
        self._load()

    def _load(self) -> None:
        if self.file_path.exists():
            try:
                raw = json.loads(self.file_path.read_text(encoding="utf-8"))
                self.queue = BacklogQueue.from_dict(raw)
            except (json.JSONDecodeError, KeyError):
                self.queue = BacklogQueue(name="omnis-backlog")

    def _save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(json.dumps(self.queue.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    def enqueue(self, item_type: ItemType, title: str, description: str = "",
                priority: int = 3, tags: Optional[list[str]] = None,
                metadata: Optional[dict] = None) -> BacklogItem:
        item = BacklogItem(
            item_id=str(uuid.uuid4())[:8],
            item_type=item_type,
            title=title,
            description=description,
            priority=priority,
            tags=tags or [],
            metadata=metadata or {},
        )
        self.queue.items.append(item)
        self._save()
        return item

    def dequeue(self) -> Optional[BacklogItem]:
        item = self.queue.next()
        if item:
            item.status = ItemStatus.IN_PROGRESS
            item.updated_at = BacklogItem.__dataclass_fields__["updated_at"].default_factory()
            self._save()
        return item

    def complete(self, item_id: str) -> Optional[BacklogItem]:
        item = self._find(item_id)
        if item:
            item.status = ItemStatus.COMPLETED
            item.updated_at = self._now()
            self._save()
        return item

    def cancel(self, item_id: str) -> Optional[BacklogItem]:
        item = self._find(item_id)
        if item:
            item.status = ItemStatus.CANCELLED
            item.updated_at = self._now()
            self._save()
        return item

    def block(self, item_id: str, reason: str = "") -> Optional[BacklogItem]:
        item = self._find(item_id)
        if item:
            item.status = ItemStatus.BLOCKED
            item.metadata["block_reason"] = reason
            item.updated_at = self._now()
            self._save()
        return item

    def unblock(self, item_id: str) -> Optional[BacklogItem]:
        item = self._find(item_id)
        if item and item.status == ItemStatus.BLOCKED:
            item.status = ItemStatus.PENDING
            item.metadata.pop("block_reason", None)
            item.updated_at = self._now()
            self._save()
        return item

    def get(self, item_id: str) -> Optional[BacklogItem]:
        return self._find(item_id)

    def list_by_status(self, status: Optional[ItemStatus] = None) -> list[BacklogItem]:
        if status is None:
            return self.queue.items
        return [i for i in self.queue.items if i.status == status]

    def list_by_type(self, item_type: ItemType) -> list[BacklogItem]:
        return [i for i in self.queue.items if i.item_type == item_type]

    def list_by_tag(self, tag: str) -> list[BacklogItem]:
        return [i for i in self.queue.items if tag in i.tags]

    def prioritize(self, item_id: str, new_priority: int) -> Optional[BacklogItem]:
        item = self._find(item_id)
        if item:
            item.priority = max(1, min(5, new_priority))
            item.updated_at = self._now()
            self._save()
        return item

    def count(self) -> dict:
        return {
            "total": len(self.queue.items),
            "pending": len(self.queue.pending),
            "in_progress": len(self.queue.in_progress),
            "blocked": len(self.queue.blocked),
            "completed": len([i for i in self.queue.items if i.status == ItemStatus.COMPLETED]),
            "cancelled": len([i for i in self.queue.items if i.status == ItemStatus.CANCELLED]),
        }

    def _find(self, item_id: str) -> Optional[BacklogItem]:
        for item in self.queue.items:
            if item.item_id == item_id:
                return item
        return None

    @staticmethod
    def _now() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
