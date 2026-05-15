"""Learning Writeback — file-backed append-only JSONL for mission learnings."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LearningEntry(BaseModel):
    """A single learning entry — insight captured during or after mission execution."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    source: str = ""
    insight: str
    confidence: Confidence = Confidence.MEDIUM
    tags: list[str] = Field(default_factory=list)
    mission_id: str = ""
    step_id: str = ""
    evidence: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_jsonl(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"), ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str,
        )

    @classmethod
    def from_jsonl(cls, line: str) -> "LearningEntry":
        data = json.loads(line)
        return cls(**data)


class LearningJournal:
    """File-backed append-only journal — stores learnings as JSONL in mission directory."""

    def __init__(self, mission_dir: str) -> None:
        self.mission_dir = Path(mission_dir)
        self.journal_path = self.mission_dir / "learnings.jsonl"

    def record(
        self,
        insight: str,
        source: str = "",
        confidence: Confidence = Confidence.MEDIUM,
        tags: Optional[list[str]] = None,
        mission_id: str = "",
        step_id: str = "",
        evidence: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LearningEntry:
        entry = LearningEntry(
            source=source,
            insight=insight,
            confidence=confidence,
            tags=tags or [],
            mission_id=mission_id,
            step_id=step_id,
            evidence=evidence,
            metadata=metadata or {},
        )
        with open(self.journal_path, "a", encoding="utf-8") as f:
            f.write(entry.to_jsonl() + "\n")
        return entry

    def read_all(self) -> List[LearningEntry]:
        if not self.journal_path.exists():
            return []
        entries: List[LearningEntry] = []
        with open(self.journal_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entries.append(LearningEntry.from_jsonl(stripped))
                except (json.JSONDecodeError, Exception):
                    continue
        return entries

    def filter_by_tag(self, tag: str) -> List[LearningEntry]:
        return [e for e in self.read_all() if tag in e.tags]

    def filter_by_confidence(self, confidence: Confidence) -> List[LearningEntry]:
        return [e for e in self.read_all() if e.confidence == confidence]

    def search(self, keyword: str) -> List[LearningEntry]:
        kw = keyword.lower()
        return [e for e in self.read_all() if kw in e.insight.lower()]

    def count(self) -> int:
        return len(self.read_all())

    def summary(self) -> Dict[str, Any]:
        entries = self.read_all()
        return {
            "total": len(entries),
            "by_confidence": {
                c.value: len([e for e in entries if e.confidence == c])
                for c in Confidence
            },
            "all_tags": sorted({t for e in entries for t in e.tags}),
        }
