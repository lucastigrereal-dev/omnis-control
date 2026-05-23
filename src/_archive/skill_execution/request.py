import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class SkillExecutionRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SkillExecutionRequest:
    request_id: str = field(default_factory=lambda: _new_id("ser"))
    skill_id: str = ""
    intent: str = ""
    payload: dict = field(default_factory=dict)
    dry_run: bool = True
    risk_level: SkillExecutionRisk = SkillExecutionRisk.LOW
    requires_approval: bool = False
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    source_system: str = "omnis"
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    @property
    def is_safe(self) -> bool:
        return self.dry_run and self.risk_level in (SkillExecutionRisk.LOW, SkillExecutionRisk.MEDIUM)

    @property
    def needs_human_approval(self) -> bool:
        return self.requires_approval or self.risk_level in (SkillExecutionRisk.HIGH, SkillExecutionRisk.CRITICAL)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "skill_id": self.skill_id,
            "intent": self.intent,
            "payload": self.payload,
            "dry_run": self.dry_run,
            "risk_level": self.risk_level.value,
            "requires_approval": self.requires_approval,
            "allowed_paths": self.allowed_paths,
            "forbidden_paths": self.forbidden_paths,
            "expected_outputs": self.expected_outputs,
            "source_system": self.source_system,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SkillExecutionRequest":
        return cls(
            request_id=data.get("request_id", ""),
            skill_id=data.get("skill_id", ""),
            intent=data.get("intent", ""),
            payload=data.get("payload", {}),
            dry_run=data.get("dry_run", True),
            risk_level=SkillExecutionRisk(data.get("risk_level", "LOW")),
            requires_approval=data.get("requires_approval", False),
            allowed_paths=data.get("allowed_paths", []),
            forbidden_paths=data.get("forbidden_paths", []),
            expected_outputs=data.get("expected_outputs", []),
            source_system=data.get("source_system", "omnis"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
        )
