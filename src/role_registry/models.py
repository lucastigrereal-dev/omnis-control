"""Models for Role Registry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Role:
    role_id: str
    name: str
    sectors: List[str]
    responsibilities: List[str]
    outputs: List[str]
    risk_level: str

    def matches_sector(self, sector: str) -> bool:
        return sector in self.sectors

    def matches_output(self, output: str) -> bool:
        return output in self.outputs


@dataclass
class RoleMatchResult:
    role_id: str
    name: str
    sectors: List[str]
    outputs: List[str]
    risk_level: str
    reason: str
