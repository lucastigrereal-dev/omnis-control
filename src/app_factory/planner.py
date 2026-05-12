"""AppFactoryPlanner — deterministic pipeline: Idea → Requirements → Blueprint → Artifact."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.app_factory.errors import InvalidAppIdeaError, PlannerError
from src.app_factory.models import (
    AppArtifact,
    AppBlueprint,
    AppIdea,
    AppRequirement,
    STATUS_DRAFT,
    STATUS_FAILED,
    STATUS_GENERATED,
    STATUS_PLANNED,
)
from src.app_factory.prd_generator import generate_prd
from src.app_factory.structure_generator import generate_project_structure

_DEFAULT_PLAN_LOG = Path(__file__).resolve().parent.parent.parent / "data" / "app_factory_plans.jsonl"


class AppFactoryPlanner:
    """Deterministic pipeline that transforms an AppIdea into a full AppArtifact.

    Pipeline stages:
      1. Validate AppIdea
      2. Extract AppRequirements (deterministic keyword rules)
      3. Design AppBlueprint (architectural patterns)
      4. Generate PRD markdown (template-based)
      5. Generate project structure plan (template-based)
      6. Package everything into AppArtifact
    """

    def __init__(self, log_path: Optional[Path] = None) -> None:
        self.log_path = Path(log_path) if log_path else _DEFAULT_PLAN_LOG
        self._history: list[dict] = []

    # ── Public API ─────────────────────────────────────────────────────────

    def plan(self, idea: AppIdea, dry_run: bool = True) -> AppArtifact:
        """Execute the full planning pipeline and return an AppArtifact.

        When dry_run=True, results are only returned, not persisted.
        """
        self._validate(idea)

        req = AppRequirement.from_idea(idea)
        blueprint = AppBlueprint.from_requirement(req)
        prd_md = generate_prd(blueprint, req, idea)
        structure = generate_project_structure(blueprint, req)

        artifact = AppArtifact.from_blueprint(blueprint, prd_md, structure)

        if not dry_run:
            self._persist(idea, req, blueprint, artifact)
            idea.status = STATUS_GENERATED
        else:
            idea.status = STATUS_PLANNED

        self._history.append(artifact.to_dict())
        return artifact

    def plan_batch(self, ideas: list[AppIdea], dry_run: bool = True) -> list[AppArtifact]:
        """Plan multiple ideas. Stops on first invalid idea."""
        artifacts: list[AppArtifact] = []
        for idea in ideas:
            artifacts.append(self.plan(idea, dry_run=dry_run))
        return artifacts

    def get_history(self) -> list[dict]:
        """Return in-memory history of generated artifacts."""
        return list(self._history)

    def load_history(self) -> list[dict]:
        """Load planning history from JSONL log."""
        if not self.log_path.exists():
            return []
        items: list[dict] = []
        with open(self.log_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return items

    # ── Internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _validate(idea: AppIdea) -> None:
        issues = idea.validate()
        if issues:
            raise InvalidAppIdeaError(f"Invalid AppIdea: {'; '.join(issues)}")

    def _persist(self, idea: AppIdea, req: AppRequirement, blueprint: AppBlueprint, artifact: AppArtifact) -> None:
        os.makedirs(self.log_path.parent, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "idea": idea.to_dict(),
            "requirement": req.to_dict(),
            "blueprint": blueprint.to_dict(),
            "artifact_id": artifact.artifact_id,
        }
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
