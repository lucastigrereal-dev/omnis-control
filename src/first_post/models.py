"""First Post Preflight models — Pydantic v2. P1.3a."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PreflightStatus:
    READY = "ready"
    BLOCKED = "blocked"
    PARTIAL = "partial"
    EMPTY = "empty"
    FAILED = "failed"

    ALL = frozenset({READY, BLOCKED, PARTIAL, EMPTY, FAILED})


class PreflightCheck(BaseModel):
    """Resultado de um check individual do preflight."""

    model_config = ConfigDict(extra="forbid")

    check_id: str
    label: str
    passed: bool
    required: bool = True
    detail: str = ""
    recommendation: str = ""


class PreflightReport(BaseModel):
    """Relatorio agregado do preflight — 8 checks antes de publicar."""

    model_config = ConfigDict(extra="forbid")

    overall_status: str = PreflightStatus.EMPTY
    total_checks: int = 8
    passed: int = 0
    failed: int = 0
    blocked: int = 0
    checks: List[PreflightCheck] = Field(default_factory=list)
    can_publish: bool = False
    ready_items: int = 0
    next_action: str = ""
    checked_at: str = ""

    def __init__(self, **data):
        if "checked_at" not in data or not data.get("checked_at"):
            data["checked_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        super().__init__(**data)


class PostPackage(BaseModel):
    """Pacote de conteudo pronto para publicacao (dry-run, nunca publica)."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = ""
    queue_id: str = ""
    account_handle: str = ""
    format: str = ""
    caption_text: str = ""
    cta: str = ""
    hashtags: List[str] = Field(default_factory=list)
    asset_id: Optional[str] = None
    asset_file: str = ""
    warnings: List[str] = Field(default_factory=list)
    ready: bool = False
    created_at: str = ""

    def __init__(self, **data):
        if "created_at" not in data or not data.get("created_at"):
            data["created_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        super().__init__(**data)
