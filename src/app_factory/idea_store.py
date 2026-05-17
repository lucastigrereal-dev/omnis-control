"""IdeaStore - file-backed JSONL storage for AppIdea instances."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.app_factory.errors import InvalidAppIdeaError
from src.app_factory.models import AppIdea
from src.omnis_os.event_bus import EventBus

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "app_factory"


class IdeaStore:
    """File-backed JSONL storage for AppIdea instances.

    dry_run=True by default: validates and logs intent but does not write.
    """

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        dry_run: bool = True,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
        self.dry_run = dry_run
        self.bus = event_bus or EventBus(dry_run=True)
        self._file_path = self.data_dir / "ideas.jsonl"

    def save(self, idea: AppIdea) -> AppIdea:
        """Validate idea, then persist to JSONL if not dry_run."""
        issues = idea.validate()
        if issues:
            raise InvalidAppIdeaError(f"Invalid AppIdea: {'; '.join(issues)}")

        self.bus.emit_new("idea_validated", "app_factory", data={"idea_id": idea.idea_id})

        if not self.dry_run:
            self._append(idea)
            self.bus.emit_new("idea_stored", "app_factory", data={"idea_id": idea.idea_id})

        return idea

    def get(self, idea_id: str) -> Optional[AppIdea]:
        """Retrieve a single idea by ID."""
        for idea in self._read_all():
            if idea.idea_id == idea_id:
                return idea
        return None

    def list_all(self) -> list[AppIdea]:
        """Return all stored ideas."""
        return self._read_all()

    def list_by_status(self, status: str) -> list[AppIdea]:
        """Return ideas filtered by status."""
        return [i for i in self._read_all() if i.status == status]

    def exists(self, idea_id: str) -> bool:
        return self.get(idea_id) is not None

    def _append(self, idea: AppIdea) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self._file_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(idea.to_dict(), ensure_ascii=False) + "\n")

    def _read_all(self) -> list[AppIdea]:
        if not self._file_path.exists():
            return []
        ideas: list[AppIdea] = []
        with open(self._file_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ideas.append(AppIdea.from_dict(json.loads(line)))
                except (json.JSONDecodeError, KeyError):
                    continue
        return ideas
