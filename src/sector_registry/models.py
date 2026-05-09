"""Sector Registry models."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Sector:
    sector_id: str
    name: str
    keywords: list[str]
    default_outputs: list[str]
    risk_level: str  # low | medium | high

    def to_dict(self) -> dict:
        return {
            "sector_id": self.sector_id,
            "name": self.name,
            "keywords": self.keywords,
            "default_outputs": self.default_outputs,
            "risk_level": self.risk_level,
        }


@dataclass
class SectorMatchResult:
    sector_id: str
    sector_name: str
    matched_keywords: list[str]
    confidence: float  # 0.0–1.0
    risk_level: str
    default_outputs: list[str]

    def to_dict(self) -> dict:
        return {
            "sector_id": self.sector_id,
            "sector_name": self.sector_name,
            "matched_keywords": self.matched_keywords,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "default_outputs": self.default_outputs,
        }
