"""Skill Matcher models."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Capability:
    capability_id: str
    sector: str
    command: str
    output: str
    risk_level: str   # low | medium | high
    status: str       # active | inactive
    keywords: list[str]

    def to_dict(self) -> dict:
        return {
            "capability_id": self.capability_id,
            "sector": self.sector,
            "command": self.command,
            "output": self.output,
            "risk_level": self.risk_level,
            "status": self.status,
            "keywords": self.keywords,
        }


@dataclass
class SkillMatchResult:
    capability_id: str
    sector: str
    command: str
    output: str
    risk_level: str
    matched_keywords: list[str]
    confidence: float
    requires_approval: bool  # True if risk_level == "high"

    def to_dict(self) -> dict:
        return {
            "capability_id": self.capability_id,
            "sector": self.sector,
            "command": self.command,
            "output": self.output,
            "risk_level": self.risk_level,
            "matched_keywords": self.matched_keywords,
            "confidence": self.confidence,
            "requires_approval": self.requires_approval,
        }
