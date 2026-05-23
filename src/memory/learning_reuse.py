"""LearningReuse — load, search, and report on reused learnings across missions."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class LearningReuse:
    """Loads learnings from JSONL and finds relevant entries by keyword match."""

    def load_learnings(self, jsonl_path: Path) -> list[dict[str, object]]:
        """Load all learning records from a JSONL file."""
        records: list[dict[str, object]] = []
        if not jsonl_path.exists():
            return records
        with jsonl_path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    def find_relevant(
        self,
        learnings: list[dict[str, object]],
        topic: str,
        max_results: int = 5,
    ) -> list[dict[str, object]]:
        """Return up to max_results learnings matching topic keywords (case-insensitive)."""
        keywords = [kw.lower().strip() for kw in topic.split() if kw.strip()]
        if not keywords:
            return learnings[:max_results]

        scored: list[tuple[int, dict[str, object]]] = []
        for record in learnings:
            text = json.dumps(record, ensure_ascii=False).lower()
            hits = sum(1 for kw in keywords if kw in text)
            if hits > 0:
                scored.append((hits, record))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [rec for _, rec in scored[:max_results]]

    def build_reuse_report(
        self,
        mission_a: dict[str, object],
        mission_b: dict[str, object],
        reused: list[dict[str, object]],
    ) -> dict[str, object]:
        """Build a structured report showing which learnings from A were reused in B."""
        return {
            "report_type": "memory_reuse",
            "generated_at": _now_iso(),
            "mission_a": {
                "id": mission_a.get("mission_id", "unknown"),
                "destination": mission_a.get("destination", ""),
                "tags": mission_a.get("tags", []),
            },
            "mission_b": {
                "id": mission_b.get("mission_id", "unknown"),
                "destination": mission_b.get("destination", ""),
                "tags": mission_b.get("tags", []),
            },
            "reused_count": len(reused),
            "reused_learnings": reused,
            "reuse_rate": (
                round(len(reused) / len(mission_a.get("learnings", [])), 2)
                if mission_a.get("learnings")
                else 0.0
            ),
            "verdict": "high_reuse" if len(reused) >= 3 else "low_reuse",
        }
