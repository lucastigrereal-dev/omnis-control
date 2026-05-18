"""Local Search Engine models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SourceType(str, Enum):
    MISSION = "mission"
    TEMPLATE = "template"
    SKILL = "skill"
    LOG = "log"
    REPORT = "report"
    DOC = "doc"
    SCRIPT = "script"


@dataclass
class SearchResult:
    source_type: SourceType
    source_path: str
    title: str
    snippet: str
    score: float = 0.0
    tags: list[str] = field(default_factory=list)
    mission_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "source_type": self.source_type.value,
            "source_path": self.source_path,
            "title": self.title,
            "snippet": self.snippet,
            "score": self.score,
            "tags": self.tags,
            "mission_id": self.mission_id,
        }


@dataclass
class SearchQuery:
    query: str
    source_types: list[SourceType] = field(default_factory=list)
    max_results: int = 20
    min_score: float = 0.0

    @property
    def terms(self) -> list[str]:
        return [t.lower() for t in self.query.split() if len(t) > 1]
