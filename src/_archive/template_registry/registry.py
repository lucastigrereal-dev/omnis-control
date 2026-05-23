"""TemplateRegistry manager — load, save, search, promote, version."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import TemplateEntry, TemplateCategory, TemplateStatus


class TemplateRegistry:
    """Central registry for all templates across categories."""

    def __init__(self, registry_path: Path, templates_dir: Path):
        self.registry_path = Path(registry_path)
        self.templates_dir = Path(templates_dir)
        self._entries: dict[str, TemplateEntry] = {}

    # ---------------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------------

    def load(self) -> None:
        """Load registry from JSON file."""
        if self.registry_path.is_file():
            raw = json.loads(self.registry_path.read_text(encoding="utf-8"))
            self._entries = {
                tid: TemplateEntry.from_dict(d)
                for tid, d in raw.get("templates", {}).items()
            }
        else:
            self._entries = {}

    def save(self) -> None:
        """Persist registry to JSON file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "total": len(self._entries),
            "templates": {tid: e.to_dict() for tid, e in self._entries.items()},
        }
        self.registry_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ---------------------------------------------------------------
    # CRUD
    # ---------------------------------------------------------------

    def add(self, entry: TemplateEntry) -> None:
        if entry.template_id in self._entries:
            raise KeyError(f"Template '{entry.template_id}' already exists. Use update().")
        self._entries[entry.template_id] = entry

    def get(self, template_id: str) -> Optional[TemplateEntry]:
        return self._entries.get(template_id)

    def update(self, template_id: str, **kwargs) -> TemplateEntry:
        entry = self._entries[template_id]
        for k, v in kwargs.items():
            if hasattr(entry, k):
                setattr(entry, k, v)
        entry.touch()
        return entry

    def remove(self, template_id: str) -> None:
        self._entries.pop(template_id, None)

    def list_all(self) -> list[TemplateEntry]:
        return list(self._entries.values())

    # ---------------------------------------------------------------
    # Query
    # ---------------------------------------------------------------

    def by_category(self, category: TemplateCategory) -> list[TemplateEntry]:
        return [e for e in self._entries.values() if e.category == category]

    def by_status(self, status: TemplateStatus) -> list[TemplateEntry]:
        return [e for e in self._entries.values() if e.status == status]

    def by_tag(self, tag: str) -> list[TemplateEntry]:
        tag_lower = tag.lower()
        return [e for e in self._entries.values() if tag_lower in (t.lower() for t in e.tags)]

    def search(self, query: str) -> list[TemplateEntry]:
        q = query.lower()
        results = []
        for e in self._entries.values():
            if (
                q in e.name.lower()
                or q in e.description.lower()
                or any(q in t.lower() for t in e.tags)
            ):
                results.append(e)
        return results

    def top_by_score(self, category: Optional[TemplateCategory] = None, limit: int = 10) -> list[TemplateEntry]:
        entries = self.by_category(category) if category else list(self._entries.values())
        scored = [e for e in entries if e.score is not None]
        scored.sort(key=lambda e: e.score, reverse=True)
        return scored[:limit]

    @property
    def count(self) -> int:
        return len(self._entries)

    # ---------------------------------------------------------------
    # Lifecycle actions
    # ---------------------------------------------------------------

    def promote(self, template_id: str) -> TemplateEntry:
        """Promote output to template status."""
        entry = self._entries[template_id]
        entry.status = TemplateStatus.APPROVED
        entry.touch()
        return entry

    def approve(self, template_id: str) -> TemplateEntry:
        entry = self._entries[template_id]
        entry.status = TemplateStatus.ACTIVE
        entry.touch()
        return entry

    def deprecate(self, template_id: str) -> TemplateEntry:
        entry = self._entries[template_id]
        entry.status = TemplateStatus.DEPRECATED
        entry.deprecated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        entry.touch()
        return entry

    def bump_version(self, template_id: str) -> TemplateEntry:
        entry = self._entries[template_id]
        entry.bump_version()
        return entry

    # ---------------------------------------------------------------
    # Stats
    # ---------------------------------------------------------------

    def stats(self) -> dict:
        cats = {}
        for e in self._entries.values():
            c = e.category.value
            cats[c] = cats.get(c, 0) + 1
        statuses = {}
        for e in self._entries.values():
            s = e.status.value
            statuses[s] = statuses.get(s, 0) + 1
        return {
            "total": len(self._entries),
            "by_category": cats,
            "by_status": statuses,
            "top_scored": [e.template_id for e in self.top_by_score(limit=5)],
            "most_used": sorted(self._entries.values(), key=lambda e: e.usage_count, reverse=True)[:5],
        }
