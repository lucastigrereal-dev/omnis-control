"""Mission Report models."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class MissionReport:
    report_id: str
    mission_id: str
    intent: str
    account_handle: str
    outcome: str           # completed | cancelled | deferred
    notes: str
    published_url: str
    closed_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        mission_id: str,
        intent: str,
        account_handle: str,
        outcome: str,
        notes: str = "",
        published_url: str = "",
    ) -> "MissionReport":
        return cls(
            report_id=f"mr_{uuid.uuid4().hex[:8]}",
            mission_id=mission_id,
            intent=intent,
            account_handle=account_handle,
            outcome=outcome,
            notes=notes,
            published_url=published_url,
        )

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "mission_id": self.mission_id,
            "intent": self.intent,
            "account_handle": self.account_handle,
            "outcome": self.outcome,
            "notes": self.notes,
            "published_url": self.published_url,
            "closed_at": self.closed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MissionReport":
        return cls(**data)
