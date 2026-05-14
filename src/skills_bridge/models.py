import uuid
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class SkillIntent(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ANALYZE = "analyze"
    PUBLISH = "publish"
    NOTIFY = "notify"
    GENERATE = "generate"
    UNKNOWN = "unknown"


@dataclass
class SkillCall:
    call_id: str = field(default_factory=lambda: _new_id("skc"))
    skill_id: str = ""
    intent: SkillIntent = SkillIntent.UNKNOWN
    input_payload: dict = field(default_factory=dict)
    dry_run: bool = True
    risk_level: str = "LOW"
    expected_artifacts: list[str] = field(default_factory=list)
    requires_approval: bool = False
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "call_id": self.call_id,
            "skill_id": self.skill_id,
            "intent": self.intent.value,
            "input_payload": self.input_payload,
            "dry_run": self.dry_run,
            "risk_level": self.risk_level,
            "expected_artifacts": self.expected_artifacts,
            "requires_approval": self.requires_approval,
            "tags": self.tags,
            "created_at": self.created_at,
        }


@dataclass
class SkillSelection:
    selection_id: str = field(default_factory=lambda: _new_id("sks"))
    skill_id: str = ""
    skill_name: str = ""
    intent: SkillIntent = SkillIntent.UNKNOWN
    confidence: float = 0.0
    fallback_skill_id: str = ""
    requires_manual_review: bool = False
    reason: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "selection_id": self.selection_id,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "intent": self.intent.value,
            "confidence": self.confidence,
            "fallback_skill_id": self.fallback_skill_id,
            "requires_manual_review": self.requires_manual_review,
            "reason": self.reason,
            "tags": self.tags,
            "created_at": self.created_at,
        }
