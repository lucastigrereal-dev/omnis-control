import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class SkillRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SkillDefinition:
    skill_id: str = ""
    name: str = ""
    description: str = ""
    tier: str = "core"
    risk: SkillRisk = SkillRisk.LOW
    requires_approval: bool = False
    category: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "tier": self.tier,
            "risk": self.risk.value,
            "requires_approval": self.requires_approval,
            "category": self.category,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SkillDefinition":
        return cls(
            skill_id=data.get("skill_id", data.get("id", "")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            tier=data.get("tier", "core"),
            risk=SkillRisk(data.get("risk", "LOW").upper()),
            requires_approval=data.get("requires_approval", False),
            category=data.get("category", ""),
            tags=data.get("tags", []),
        )


@dataclass
class SkillCall:
    call_id: str = field(default_factory=lambda: _new_id("skc"))
    skill_id: str = ""
    intent: str = ""
    payload: dict = field(default_factory=dict)
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "call_id": self.call_id,
            "skill_id": self.skill_id,
            "intent": self.intent,
            "payload": self.payload,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SkillCall":
        return cls(
            call_id=data.get("call_id", ""),
            skill_id=data.get("skill_id", ""),
            intent=data.get("intent", ""),
            payload=data.get("payload", {}),
            dry_run=data.get("dry_run", True),
            created_at=data.get("created_at", ""),
        )


@dataclass
class SkillSelectorResult:
    result_id: str = field(default_factory=lambda: _new_id("ssr"))
    selected_skill_id: str = ""
    confidence: float = 0.0
    alternatives: list[str] = field(default_factory=list)
    fallback: bool = False
    reason: str = ""

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.8

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "selected_skill_id": self.selected_skill_id,
            "confidence": self.confidence,
            "alternatives": self.alternatives,
            "fallback": self.fallback,
            "reason": self.reason,
        }
