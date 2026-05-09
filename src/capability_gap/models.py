"""Capability Gap models."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


GAP_STATUS_OPEN = "open"
GAP_STATUS_PLANNED = "planned"
GAP_STATUS_DISMISSED = "dismissed"
GAP_STATUS_COVERED = "covered"


@dataclass
class CapabilityGap:
    gap_id: str
    request: str
    sector: str
    missing_capability: str
    desired_output: str
    risk_level: str
    status: str
    recommendation: str
    created_at: str = field(default_factory=_now_iso)
    decided_at: Optional[str] = None

    @classmethod
    def new(
        cls,
        request: str,
        sector: str,
        missing_capability: str,
        desired_output: str,
        risk_level: str = "medium",
        recommendation: str = "",
    ) -> "CapabilityGap":
        return cls(
            gap_id=f"gap_{uuid.uuid4().hex[:8]}",
            request=request,
            sector=sector,
            missing_capability=missing_capability,
            desired_output=desired_output,
            risk_level=risk_level,
            status=GAP_STATUS_OPEN,
            recommendation=recommendation or f"Create capability for: {missing_capability}",
        )

    def to_dict(self) -> dict:
        return {
            "gap_id": self.gap_id,
            "request": self.request,
            "sector": self.sector,
            "missing_capability": self.missing_capability,
            "desired_output": self.desired_output,
            "risk_level": self.risk_level,
            "status": self.status,
            "recommendation": self.recommendation,
            "created_at": self.created_at,
            "decided_at": self.decided_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CapabilityGap":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class GapDetectionResult:
    request: str
    status: str          # "covered" | "gap_detected" | "unknown_sector"
    sector_id: str
    matched_capabilities: list[str]
    gaps: list[CapabilityGap] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "request": self.request,
            "status": self.status,
            "sector_id": self.sector_id,
            "matched_capabilities": self.matched_capabilities,
            "gaps": [g.to_dict() for g in self.gaps],
        }
