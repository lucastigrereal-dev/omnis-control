"""Mission Contract — Pydantic v2 immutable models with content-addressable hash."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalPolicy(str, Enum):
    NONE = "none"
    AUTO = "auto"
    MANUAL = "manual"


class Sector(str, Enum):
    MARKETING = "marketing"
    SALES = "sales"
    APP_FACTORY = "app_factory"
    RESEARCH = "research"
    AUTOMATION = "automation"
    CREATIVE = "creative"
    FINANCE = "finance"
    SECURITY = "security"
    KNOWLEDGE = "knowledge"
    INTELLIGENCE = "intelligence"
    OPERATIONS = "operations"


class BudgetCaps(BaseModel):
    """Limites contratuais de recurso — estouro trava em waiting_approval."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_tokens: int = 50000
    max_cost_usd: float = 2.0
    max_duration_seconds: int = 600
    max_steps: int = 50


class AcceptanceCriterion(BaseModel):
    """Critério de aceite individual."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    description: str
    check_type: str = "manual_review"
    check_target: str = "human"
    required: bool = True


class MissionContract(BaseModel):
    """Contrato imutável de missão — a 'certidão de nascimento'."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str
    objective: str
    sector: Sector
    user_request: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    approval_policy: ApprovalPolicy = ApprovalPolicy.NONE
    budget: BudgetCaps = Field(default_factory=BudgetCaps)
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    expected_deliverables: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    parent_mission_id: Optional[str] = None
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def content_hash(self) -> str:
        """SHA-256 of canonical JSON excluding created_at."""
        data = self.model_dump(mode="json", exclude={"created_at"})
        canonical = json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def canonical_json(self) -> str:
        """JSON canônico que será salvo em disco."""
        data = self.model_dump(mode="json")
        return json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
