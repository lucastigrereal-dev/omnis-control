"""Stored idea to PRD service for W132."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.app_factory.errors import PRDGenerationError
from src.app_factory.idea_store import IdeaStore
from src.app_factory.models import AppArtifact
from src.app_factory.planner import AppFactoryPlanner


@dataclass
class PRDGenerationResult:
    idea_id: str
    artifact: AppArtifact
    persisted: bool
    output_path: str


class StoredIdeaPRDGenerator:
    """Generate deterministic PRDs from ideas already stored in IdeaStore."""

    def __init__(
        self,
        store: Optional[IdeaStore] = None,
        planner: Optional[AppFactoryPlanner] = None,
        output_path: Optional[Path] = None,
    ) -> None:
        self.store = store or IdeaStore(dry_run=True)
        self.planner = planner or AppFactoryPlanner()
        self.output_path = Path(output_path) if output_path else None

    def generate(self, idea_id: str, dry_run: bool = True) -> PRDGenerationResult:
        idea = self.store.get(idea_id)
        if idea is None:
            raise PRDGenerationError(f"Idea not found: {idea_id}")

        artifact = self.planner.plan(idea, dry_run=True)
        persisted = False
        if not dry_run and self.output_path is not None:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "idea_id": idea.idea_id,
                "artifact_id": artifact.artifact_id,
                "blueprint_id": artifact.blueprint_id,
                "prd_markdown": artifact.prd_markdown,
            }
            with open(self.output_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            persisted = True

        return PRDGenerationResult(
            idea_id=idea.idea_id,
            artifact=artifact,
            persisted=persisted,
            output_path=str(self.output_path) if self.output_path else "",
        )
