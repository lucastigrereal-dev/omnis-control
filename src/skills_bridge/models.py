import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


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


@dataclass(init=False)
class SkillCall:
    call_id: str = field(default_factory=lambda: _new_id("skc"))
    skill_id: str = ""
    intent: SkillIntent | str = SkillIntent.UNKNOWN
    payload: dict[str, object] = field(default_factory=dict)
    dry_run: bool = True
    risk_level: str = "LOW"
    expected_artifacts: list[str] = field(default_factory=list)
    requires_approval: bool = False
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def __init__(
        self,
        call_id: str | None = None,
        skill_id: str = "",
        intent: SkillIntent | str = SkillIntent.UNKNOWN,
        payload: dict[str, object] | None = None,
        input_payload: dict[str, object] | None = None,
        dry_run: bool = True,
        risk_level: str = "LOW",
        expected_artifacts: list[str] | None = None,
        requires_approval: bool = False,
        tags: list[str] | None = None,
        created_at: str | None = None,
    ):
        self.call_id = call_id or _new_id("skc")
        self.skill_id = skill_id
        self.intent = intent
        self.payload = payload if payload is not None else (input_payload or {})
        self.dry_run = dry_run
        self.risk_level = risk_level
        self.expected_artifacts = expected_artifacts or []
        self.requires_approval = requires_approval
        self.tags = tags or []
        self.created_at = created_at or _now_iso()
        self.__post_init__()

    def __post_init__(self) -> None:
        if isinstance(self.intent, str):
            try:
                self.intent = SkillIntent(self.intent)
            except ValueError:
                self.intent = SkillIntent.UNKNOWN

    @property
    def input_payload(self) -> dict[str, object]:
        return self.payload

    @input_payload.setter
    def input_payload(self, value: dict[str, object]) -> None:
        self.payload = value

    def to_dict(self) -> dict[str, object]:
        return {
            "call_id": self.call_id,
            "skill_id": self.skill_id,
            "intent": self.intent.value if isinstance(self.intent, SkillIntent) else str(self.intent),
            "payloar": self.payload,
            "dry_run": self.dry_run,
            "risk_level": self.risk_level,
            "expected_artifacts": self.expected_artifacts,
            "requires_approval": self.requires_approval,
            "tags": self.tags,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "SkillCall":
        return cls(
            call_id=data.get("call_id", ""),
            skill_id=data.get("skill_id", ""),
            intent=data.get("intent", "unknown"),
            payload=data.get("payloar", data.get("payload", {})),
            dry_run=data.get("dry_run", True),
            risk_level=data.get("risk_level", "LOW"),
            requires_approval=data.get("requires_approval", False),
            tags=data.get("tags", []),
        )


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

    def to_dict(self) -> dict[str, object]:
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


# ── skill_router_bridge merged models ────────────────────────────────────

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
    intents: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "tier": self.tier,
            "risk": self.risk.value,
            "requires_approval": self.requires_approval,
            "category": self.category,
            "tags": self.tags,
            "intents": self.intents,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "SkillDefinition":
        return cls(
            skill_id=data.get("skill_id", data.get("id", "")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            tier=data.get("tier", "core"),
            risk=SkillRisk(data.get("risk", "LOW").upper()),
            requires_approval=data.get("requires_approval", False),
            category=data.get("category", ""),
            tags=data.get("tags", []),
            intents=data.get("intents", []),
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

    def to_dict(self) -> dict[str, object]:
        return {
            "result_id": self.result_id,
            "selected_skill_id": self.selected_skill_id,
            "confidence": self.confidence,
            "alternatives": self.alternatives,
            "fallback": self.fallback,
            "reason": self.reason,
        }
