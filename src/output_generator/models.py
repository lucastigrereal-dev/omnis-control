"""Output Generator models — deterministic, no-LLM, no-network."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class GeneratorStatus(str, Enum):
    ACTIVE = "active"
    PLANNED = "planned"


class SelectionStatus(str, Enum):
    SELECTED = "selected"
    NO_GENERATOR = "no_generator"
    PLANNED_ONLY = "planned_only"
    BLOCKED = "blocked"


@dataclass
class OutputGeneratorDefinition:
    generator_id: str
    name: str
    output_types: list[str] = field(default_factory=list)
    mode: str = "deterministic"
    risk_level: str = "low"
    status: GeneratorStatus = GeneratorStatus.ACTIVE
    description: str = ""


@dataclass
class OutputGeneratorSelection:
    output_type: str
    selected_generator_id: str | None = None
    status: SelectionStatus = SelectionStatus.NO_GENERATOR
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "output_type": self.output_type,
            "selected_generator_id": self.selected_generator_id,
            "status": self.status.value,
            "warnings": self.warnings,
            "blockers": self.blockers,
        }
