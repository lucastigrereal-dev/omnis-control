"""Dataclasses da Capability Forge."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional


class CreationState(Enum):
    DISCOVERY = auto()
    GAP_CONFIRMED = auto()
    SPEC_READY = auto()
    BUILD = auto()
    BUILD_OK = auto()
    TESTS_PASSED = auto()
    TESTS_FAILED = auto()
    SCORE_OK = auto()
    SCORE_LOW = auto()
    APPROVED = auto()
    DUPLICATE_FOUND = auto()


@dataclass
class SkillSpec:
    """Especificacao de uma skill a ser construida."""
    name: str
    sector: str
    description: str
    problem_statement: str = ""
    inputs_schema: Dict[str, Any] = field(default_factory=dict)
    outputs_schema: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"
    owner: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class CreationContext:
    """Contexto acumulado durante criacao de uma skill."""
    gap_description: str
    sector: str
    requested_name: str = ""
    state: CreationState = CreationState.DISCOVERY
    spec: Optional[SkillSpec] = None
    logs: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    scorecard: Optional[Dict[str, Any]] = None


@dataclass
class RegistryEntry:
    """Entrada no registry de skills."""
    id: str
    name: str
    version: str = "0.1.0"
    description: str = ""
    status: str = "generated"
    risk_level: str = "low"
    owner: str = ""
    tags: List[str] = field(default_factory=list)
    path: Optional[Path] = None
    manifest_path: Optional[Path] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    usage_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillManifest:
    """Manifesto de skill (SKILL.md estruturado)."""
    name: str
    description: str
    sector: str
    mode: str = "readonly"
    risk: str = "low"
    requires: List[str] = field(default_factory=list)
