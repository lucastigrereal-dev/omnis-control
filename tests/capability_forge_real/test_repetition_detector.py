"""Onda 9 FIO 1 — RepetitionDetector tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.capability_forge_real.repetition_detector import RepetitionDetector, RepetitionCandidate


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_runs(path: Path, runs: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in runs), encoding="utf-8")


def _run(text: str, run_id: str = "") -> dict:
    return {"run_id": run_id or f"run_{text[:8].replace(' ', '_')}", "request_text": text}


# ── RepetitionCandidate ───────────────────────────────────────────────────────

class TestRepetitionCandidate:
    def test_to_dict_keys(self):
        c = RepetitionCandidate(
            normalized_text="criar post", original_text="Criar Post", count=3, run_ids=["r1"]
        )
        d = c.to_dict()
        assert set(d.keys()) == {"normalized_text", "original_text", "count", "run_ids"}

    def test_to_dict_values(self):
        c = RepetitionCandidate(
            normalized_text="criar post", original_text="Criar Post", count=5, run_ids=["r1", "r2"]
        )
        d = c.to_dict()
        assert d["count"] == 5
        assert d["original_text"] == "Criar Post"
        assert d["run_ids"] == ["r1", "r2"]


# ── Normalize ─────────────────────────────────────────────────────────────────

class TestNormalize:
    def test_lowercase(self):
        assert RepetitionDetector._normalize("Criar POST") == "criar post"

    def test_strip_whitespace(self):
        assert RepetitionDetector._normalize("  criar  ") == "criar"

    def test_collapse_spaces(self):
        assert RepetitionDetector._normalize("criar   post  viagem") == "criar post viagem"


# ── Empty / missing log ───────────────────────────────────────────────────────

class TestEdgeCases:
    def test_missing_log_returns_empty(self, tmp_path):
        detector = RepetitionDetector(runs_log=tmp_path / "nope.jsonl", threshold=3)
        assert detector.detect() == []

    def test_empty_log_returns_empty(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        log.write_text("", encoding="utf-8")
        detector = RepetitionDetector(runs_log=log, threshold=3)
        assert detector.detect() == []

    def test_malformed_line_skipped(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        lines = [
            '{"run_id": "r1", "request_text": "ok run"}',
            "NOT JSON AT ALL",
            '{"run_id": "r2", "request_text": "ok run"}',
            '{"run_id": "r3", "request_text": "ok run"}',
        ]
        log.write_text("\n".join(lines), encoding="utf-8")
        detector = RepetitionDetector(runs_log=log, threshold=3)
        candidates = detector.detect()
        assert len(candidates) == 1
        assert candidates[0].count == 3

    def test_missing_request_text_skipped(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, [
            {"run_id": "r1"},
            {"run_id": "r2", "request_text": ""},
            {"run_id": "r3", "request_text": "valid text"},
        ])
        detector = RepetitionDetector(runs_log=log, threshold=1)
        candidates = detector.detect()
        assert len(candidates) == 1
        assert candidates[0].normalized_text == "valid text"


# ── Threshold logic ───────────────────────────────────────────────────────────

class TestThreshold:
    def test_below_threshold_no_candidates(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, [_run("criar post natal", f"r{i}") for i in range(2)])
        detector = RepetitionDetector(runs_log=log, threshold=3)
        assert detector.detect() == []

    def test_exactly_at_threshold(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, [_run("criar post natal", f"r{i}") for i in range(3)])
        detector = RepetitionDetector(runs_log=log, threshold=3)
        candidates = detector.detect()
        assert len(candidates) == 1
        assert candidates[0].count == 3

    def test_above_threshold(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, [_run("criar post natal", f"r{i}") for i in range(7)])
        detector = RepetitionDetector(runs_log=log, threshold=3)
        candidates = detector.detect()
        assert candidates[0].count == 7

    def test_override_threshold_at_detect_call(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, [_run("criar post natal", f"r{i}") for i in range(2)])
        detector = RepetitionDetector(runs_log=log, threshold=5)
        candidates = detector.detect(threshold=2)
        assert len(candidates) == 1

    def test_threshold_one_returns_all_unique(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, [_run("text a", "r1"), _run("text b", "r2")])
        detector = RepetitionDetector(runs_log=log, threshold=1)
        assert len(detector.detect()) == 2


# ── Candidate content ─────────────────────────────────────────────────────────

class TestCandidateContent:
    def test_run_ids_tracked(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, [
            _run("criar post natal", "run_a"),
            _run("criar post natal", "run_b"),
            _run("criar post natal", "run_c"),
        ])
        detector = RepetitionDetector(runs_log=log, threshold=3)
        c = detector.detect()[0]
        assert set(c.run_ids) == {"run_a", "run_b", "run_c"}

    def test_original_text_preserved(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, [
            {"run_id": "r1", "request_text": "Criar Post Natal"},
            {"run_id": "r2", "request_text": "criar post natal"},
            {"run_id": "r3", "request_text": "CRIAR POST NATAL"},
        ])
        detector = RepetitionDetector(runs_log=log, threshold=3)
        c = detector.detect()[0]
        assert c.original_text == "Criar Post Natal"
        assert c.normalized_text == "criar post natal"

    def test_sorted_by_count_desc(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, (
            [_run("rare task", f"r{i}") for i in range(3)]
            + [_run("frequent task", f"f{i}") for i in range(7)]
        ))
        detector = RepetitionDetector(runs_log=log, threshold=3)
        candidates = detector.detect()
        assert candidates[0].normalized_text == "frequent task"
        assert candidates[0].count == 7
        assert candidates[1].count == 3

    def test_multiple_distinct_candidates(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, (
            [_run("task alpha", f"a{i}") for i in range(4)]
            + [_run("task beta", f"b{i}") for i in range(3)]
            + [_run("task gamma", f"g{i}") for i in range(1)]
        ))
        detector = RepetitionDetector(runs_log=log, threshold=3)
        candidates = detector.detect()
        norms = {c.normalized_text for c in candidates}
        assert "task alpha" in norms
        assert "task beta" in norms
        assert "task gamma" not in norms

    def test_casing_deduplication(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, [
            {"run_id": "r1", "request_text": "Create Hotel Report"},
            {"run_id": "r2", "request_text": "create hotel report"},
            {"run_id": "r3", "request_text": "CREATE HOTEL REPORT"},
        ])
        detector = RepetitionDetector(runs_log=log, threshold=3)
        candidates = detector.detect()
        assert len(candidates) == 1
        assert candidates[0].count == 3

    def test_whitespace_deduplication(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, [
            {"run_id": "r1", "request_text": "criar  post  natal"},
            {"run_id": "r2", "request_text": "criar post natal"},
            {"run_id": "r3", "request_text": "  criar post natal  "},
        ])
        detector = RepetitionDetector(runs_log=log, threshold=3)
        candidates = detector.detect()
        assert len(candidates) == 1
        assert candidates[0].count == 3
