"""Mission Builder models — read-only plan + package manifest."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class MissionPlan:
    mission_id: str
    request_text: str
    intent: str               # carousel | reels | campaign | post | story | unknown
    deliverable: str          # carousel_package | reels_package | ...
    description: str
    account_handle: str
    format: str
    objective: str
    estimated_slots: int
    steps: list[str] = field(default_factory=list)
    context_keys: list[str] = field(default_factory=list)
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        request_text: str,
        intent: str,
        deliverable: str,
        description: str,
        account_handle: str,
        format: str,
        objective: str,
        estimated_slots: int,
        steps: Optional[list[str]] = None,
    ) -> "MissionPlan":
        return cls(
            mission_id=f"mb_{uuid.uuid4().hex[:8]}",
            request_text=request_text,
            intent=intent,
            deliverable=deliverable,
            description=description,
            account_handle=account_handle,
            format=format,
            objective=objective,
            estimated_slots=estimated_slots,
            steps=steps or [],
        )

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "request_text": self.request_text,
            "intent": self.intent,
            "deliverable": self.deliverable,
            "description": self.description,
            "account_handle": self.account_handle,
            "format": self.format,
            "objective": self.objective,
            "estimated_slots": self.estimated_slots,
            "steps": self.steps,
            "context_keys": self.context_keys,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MissionPlan":
        return cls(**data)


@dataclass
class MissionPackageManifest:
    mission_id: str
    request_text: str
    intent: str
    deliverable: str
    account_handle: str
    package_dir: str
    files: list[str] = field(default_factory=list)
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "request_text": self.request_text,
            "intent": self.intent,
            "deliverable": self.deliverable,
            "account_handle": self.account_handle,
            "package_dir": self.package_dir,
            "files": self.files,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }
