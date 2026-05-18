"""Quality Gate data models."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


@dataclass
class ScoredDimension:
    name: str
    score: float  # 0.0–10.0
    weight: float = 1.0
    verdict: str = ""
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class QualityReport:
    output_id: str
    output_type: str  # caption, carrossel, reel, dm, app
    dimensions: list[ScoredDimension] = field(default_factory=list)
    overall_score: float = 0.0
    max_score: float = 10.0
    grade: str = "N/A"  # A, B, C, D, F
    recommendation: str = ""
    ready_for_use: bool = False
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

    def to_dict(self) -> dict:
        d = asdict(self)
        d["dimensions"] = [dim.to_dict() for dim in self.dimensions]
        return d

    @property
    def passed_dimensions(self) -> int:
        return sum(1 for d in self.dimensions if d.score >= 5.5)

    @property
    def failed_dimensions(self) -> int:
        return sum(1 for d in self.dimensions if d.score < 5.5)


@dataclass
class QualityScore:
    """Aggregate score container for serialization."""
    output_id: str
    overall: float
    grade: str
    dimensions: dict[str, float]  # name -> score
    ready: bool
