"""FIO 1 — RepetitionDetector: finds repeated request_text in orchestrator_runs.jsonl.

A request_text appearing >= threshold times is a candidate for skill creation.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.mission_orchestrator.service import DEFAULT_RUNS_LOG


@dataclass
class RepetitionCandidate:
    """A request_text that has been repeated enough to warrant a skill proposal."""

    normalized_text: str
    original_text: str
    count: int
    run_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "normalized_text": self.normalized_text,
            "original_text": self.original_text,
            "count": self.count,
            "run_ids": self.run_ids,
        }


class RepetitionDetector:
    """Reads orchestrator_runs.jsonl and surfaces repeated request_text patterns.

    Usage:
        detector = RepetitionDetector(threshold=3)
        candidates = detector.detect()
        # returns list[RepetitionCandidate] sorted by count descending
    """

    def __init__(
        self,
        runs_log: Optional[Path] = None,
        threshold: int = 3,
    ):
        self.runs_log = Path(runs_log) if runs_log is not None else DEFAULT_RUNS_LOG
        self.threshold = threshold

    def detect(self, threshold: Optional[int] = None) -> list[RepetitionCandidate]:
        """Scan runs log and return candidates with count >= threshold.

        Args:
            threshold: Override instance threshold for this call.

        Returns:
            List of RepetitionCandidate sorted by count descending.
        """
        effective = threshold if threshold is not None else self.threshold

        counts: dict[str, int] = {}
        originals: dict[str, str] = {}
        run_ids: dict[str, list[str]] = {}

        for run in self._iter_runs():
            text = run.get("request_text", "")
            if not text:
                continue
            norm = self._normalize(text)
            counts[norm] = counts.get(norm, 0) + 1
            if norm not in originals:
                originals[norm] = text
            run_ids.setdefault(norm, []).append(run.get("run_id", ""))

        candidates = [
            RepetitionCandidate(
                normalized_text=norm,
                original_text=originals[norm],
                count=cnt,
                run_ids=run_ids.get(norm, []),
            )
            for norm, cnt in counts.items()
            if cnt >= effective
        ]
        candidates.sort(key=lambda c: c.count, reverse=True)
        return candidates

    def _iter_runs(self):
        """Yield parsed run dicts from the JSONL log, skipping malformed lines."""
        if not self.runs_log.exists():
            return
        with open(self.runs_log, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase + collapse whitespace for comparison."""
        return re.sub(r"\s+", " ", text.strip().lower())
