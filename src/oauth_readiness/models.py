"""OAuth Readiness models — Pydantic v2. P1.2a."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OAuthReadinessStatus:
    READY = "ready"
    BLOCKED = "blocked"
    HUMAN_REQUIRED = "human_required"
    NOT_CONFIGURED = "not_configured"
    FAILED = "failed"

    ALL = frozenset({READY, BLOCKED, HUMAN_REQUIRED, NOT_CONFIGURED, FAILED})


class OAuthReadinessCheck(BaseModel):
    """Resultado de um check individual de readiness."""

    model_config = ConfigDict(extra="forbid")

    check_id: str
    label: str
    passed: bool
    required: bool = True
    status: str = ""
    detail: str = ""
    recommendation: str = ""

    def __init__(self, **data):
        if "status" not in data or not data["status"]:
            data["status"] = OAuthReadinessStatus.READY if data.get("passed") else OAuthReadinessStatus.BLOCKED
        super().__init__(**data)


class OAuthReadinessReport(BaseModel):
    """Relatorio agregado dos 12 checks de readiness."""

    model_config = ConfigDict(extra="forbid")

    overall_status: str = OAuthReadinessStatus.NOT_CONFIGURED
    total_checks: int = 12
    passed: int = 0
    failed: int = 0
    blocked_by_required: int = 0
    checks: List[OAuthReadinessCheck] = Field(default_factory=list)
    can_proceed: bool = False
    next_action: str = ""
    checked_at: str = ""

    def __init__(self, **data):
        if "checked_at" not in data or not data.get("checked_at"):
            data["checked_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        super().__init__(**data)
