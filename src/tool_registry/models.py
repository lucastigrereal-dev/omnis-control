"""Tool Registry models — Pydantic v2. P0.8."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.tool_registry.errors import (
    InvalidToolIdError,
    InvalidStatusError,
    InvalidCategoryError,
    SecretDetectedError,
)

# ── Enums ───────────────────────────────────────────────────────────

class ToolStatus:
    NOT_CONFIGURED = "not_configured"
    MANUAL = "manual"
    READ_ONLY = "read_only"
    DRY_RUN = "dry_run"
    SEMI_AUTOMATIC = "semi_automatic"
    AUTOMATIC = "automatic"
    BLOCKED = "blocked"
    DEPRECATED = "deprecated"

    ALL = frozenset({
        NOT_CONFIGURED, MANUAL, READ_ONLY, DRY_RUN,
        SEMI_AUTOMATIC, AUTOMATIC, BLOCKED, DEPRECATED,
    })


class ToolRiskLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    ALL = frozenset({LOW, MEDIUM, HIGH, CRITICAL})


class ToolCategory:
    PUBLISHING = "publishing"
    MEMORY = "memory"
    AUTOMATION = "automation"
    DESIGN = "design"
    CRM = "crm"
    FINANCE = "finance"
    DEVELOPMENT = "development"
    RESEARCH = "research"
    STORAGE = "storage"
    COMMUNICATION = "communication"
    INFRASTRUCTURE = "infrastructure"
    LLM = "llm"
    BROWSER = "browser"
    SECURITY = "security"

    ALL = frozenset({
        PUBLISHING, MEMORY, AUTOMATION, DESIGN, CRM, FINANCE,
        DEVELOPMENT, RESEARCH, STORAGE, COMMUNICATION, INFRASTRUCTURE,
        LLM, BROWSER, SECURITY,
    })


# ── Slug validation ─────────────────────────────────────────────────

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

# Patterns que indicam possivel secret real
_SECRET_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"^EA[A-Za-z0-9]{20,}",         # Facebook/Instagram token
        r"^sk-[A-Za-z0-9]{20,}",        # OpenAI/LLM key
        r"^[A-Za-z0-9+/=]{40,}",        # Base64 longa
        r"^ghp_[A-Za-z0-9]{20,}",       # GitHub PAT
        r"^ya29\.[A-Za-z0-9_-]{20,}",   # Google OAuth
        r"^AKIA[A-Z0-9]{16}",           # AWS key
    ]
]


def validate_tool_id(tool_id: str) -> str:
    """Valida slug: lowercase, numeros, hifen, underscore. Min 3 chars."""
    if not tool_id or not _SLUG_RE.match(tool_id):
        raise InvalidToolIdError(
            f"tool_id invalido: '{tool_id}'. Use apenas lowercase, numeros, hifen, underscore. Min 3 chars."
        )
    if len(tool_id) < 3:
        raise InvalidToolIdError(f"tool_id muito curto: '{tool_id}'. Minimo 3 caracteres.")
    return tool_id


def _looks_like_secret(value: str) -> bool:
    """Heuristica: verifica se string parece um token/secret."""
    if len(value) < 20:
        return False
    for pat in _SECRET_PATTERNS:
        if pat.match(value):
            return True
    return False


# ── ToolRecord ──────────────────────────────────────────────────────

class ToolRecord(BaseModel):
    """Registro de uma ferramenta/conector no OMNIS."""

    model_config = ConfigDict(extra="forbid")

    tool_id: str
    name: str
    category: str
    status: str = ToolStatus.NOT_CONFIGURED
    risk_level: str = ToolRiskLevel.LOW
    description: str = ""
    capabilities: List[str] = Field(default_factory=list)
    required_credentials: List[str] = Field(default_factory=list)
    available_commands: List[str] = Field(default_factory=list)
    used_by_modules: List[str] = Field(default_factory=list)
    used_by_skills: List[str] = Field(default_factory=list)
    config_paths: List[str] = Field(default_factory=list)
    healthcheck: Optional[str] = None
    last_validated_at: Optional[str] = None
    validation_status: Optional[str] = None
    limitations: List[str] = Field(default_factory=list)
    next_action: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __init__(self, **data):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if "created_at" not in data or not data["created_at"]:
            data["created_at"] = now
        if "updated_at" not in data or not data["updated_at"]:
            data["updated_at"] = now
        super().__init__(**data)

    @field_validator("tool_id")
    @classmethod
    def _check_tool_id(cls, v: str) -> str:
        return validate_tool_id(v)

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        if v not in ToolStatus.ALL:
            raise InvalidStatusError(
                f"Status invalido: '{v}'. Validos: {sorted(ToolStatus.ALL)}"
            )
        return v

    @field_validator("category")
    @classmethod
    def _check_category(cls, v: str) -> str:
        if v not in ToolCategory.ALL:
            raise InvalidCategoryError(
                f"Categoria invalida: '{v}'. Validas: {sorted(ToolCategory.ALL)}"
            )
        return v

    @field_validator("required_credentials")
    @classmethod
    def _check_credentials(cls, v: List[str]) -> List[str]:
        for cred in v:
            if _looks_like_secret(cred):
                raise SecretDetectedError(
                    f"Credencial '{cred[:8]}...' parece ser valor real de secret. "
                    f"required_credentials guarda NOMES, nunca valores."
                )
        return v

    @field_validator("risk_level")
    @classmethod
    def _check_risk(cls, v: str) -> str:
        if v not in ToolRiskLevel.ALL:
            raise InvalidStatusError(
                f"Risk level invalido: '{v}'. Validos: {sorted(ToolRiskLevel.ALL)}"
            )
        return v
