"""Gap Store — append-only JSONL persistence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.capability_gap.models import CapabilityGap

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_GAPS_LOG = BASE / "data" / "capability_gaps.jsonl"


class GapStore:
    def __init__(self, path: Path = DEFAULT_GAPS_LOG):
        self.path = Path(path)

    def save(self, gap: CapabilityGap) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(gap.to_dict(), ensure_ascii=False) + "\n")

    def list_all(self, limit: int = 50) -> list[CapabilityGap]:
        if not self.path.exists():
            return []
        gaps = []
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    gaps.append(CapabilityGap.from_dict(json.loads(line)))
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
        return list(reversed(gaps))[:limit]

    def get(self, gap_id: str) -> Optional[CapabilityGap]:
        for gap in self.list_all(limit=10000):
            if gap.gap_id == gap_id:
                return gap
        return None

    def list_all_unlimited(self) -> list[CapabilityGap]:
        return self.list_all(limit=10000)
