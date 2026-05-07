"""Metrics Store — JSONL file-based storage. P0.9."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.metrics.models import MetricEvent, RunSummary
from src.metrics.errors import StoreOperationError


class MetricsStore:
    """Storage file-based para MetricEvent + RunSummary."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is None:
            base_dir = os.path.expanduser("~/omnis-control/data/metrics_spine")
        self.base_dir = Path(base_dir)
        self.metrics_path = self.base_dir / "metrics.jsonl"
        self.runs_path = self.base_dir / "runs.jsonl"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ── Metrics ───────────────────────────────────────────────────────

    def write_metric(self, event: MetricEvent) -> MetricEvent:
        """Append MetricEvent ao metrics.jsonl."""
        line = json.dumps(event.model_dump(), ensure_ascii=True, separators=(",", ":"))
        with open(self.metrics_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return event

    def get_metrics(
        self,
        mission_id: Optional[str] = None,
        run_id: Optional[str] = None,
        tool_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[MetricEvent]:
        """Le metrics com filtros opcionais. limit=0 = sem limite."""
        results: List[MetricEvent] = []
        for m in self._read_metrics():
            if mission_id and m.mission_id != mission_id:
                continue
            if run_id and m.run_id != run_id:
                continue
            if tool_id and m.tool_id != tool_id:
                continue
            if event_type and m.event_type != event_type:
                continue
            results.append(m)
            if limit > 0 and len(results) >= limit:
                break
        return results

    # ── Runs ──────────────────────────────────────────────────────────

    def write_run(self, summary: RunSummary) -> RunSummary:
        """Append ou atualiza RunSummary no runs.jsonl (upsert por run_id)."""
        existing = self.get_run(summary.run_id)
        if existing:
            fields = {k: v for k, v in summary.model_dump().items() if k != "run_id"}
            return self.update_run(summary.run_id, **fields)
        line = json.dumps(summary.model_dump(), ensure_ascii=True, separators=(",", ":"))
        with open(self.runs_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return summary

    def get_run(self, run_id: str) -> Optional[RunSummary]:
        """Busca RunSummary por run_id."""
        for r in self._read_runs():
            if r.run_id == run_id:
                return r
        return None

    def get_runs(
        self,
        mission_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[RunSummary]:
        """Le runs com filtro opcional por mission_id. limit=0 = sem limite."""
        results: List[RunSummary] = []
        for r in self._read_runs():
            if mission_id and r.mission_id != mission_id:
                continue
            results.append(r)
            if limit > 0 and len(results) >= limit:
                break
        return results

    def update_run(self, run_id: str, **fields) -> Optional[RunSummary]:
        """Atualiza campos de um RunSummary existente."""
        records = self._read_runs()
        updated = None
        for r in records:
            if r.run_id == run_id:
                data = r.model_dump()
                data.update(fields)
                updated = RunSummary(**data)
                break

        if updated is None:
            return None

        # Rewrite entire file with updated record
        lines = []
        for r in records:
            if r.run_id == run_id:
                lines.append(json.dumps(updated.model_dump(), ensure_ascii=True, separators=(",", ":")))
            else:
                lines.append(json.dumps(r.model_dump(), ensure_ascii=True, separators=(",", ":")))
        self.runs_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return updated

    # ── Internals ─────────────────────────────────────────────────────

    def _read_metrics(self) -> List[MetricEvent]:
        if not self.metrics_path.exists():
            return []
        records: List[MetricEvent] = []
        with open(self.metrics_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                    records.append(MetricEvent(**data))
                except (json.JSONDecodeError, Exception):
                    continue
        return records

    def _read_runs(self) -> List[RunSummary]:
        if not self.runs_path.exists():
            return []
        records: List[RunSummary] = []
        with open(self.runs_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                    records.append(RunSummary(**data))
                except (json.JSONDecodeError, Exception):
                    continue
        return records
