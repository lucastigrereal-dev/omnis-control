"""Onda 9 FIO 2 — LoopCloser: repetition → propose → build → activate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src.capability_forge_real.loop_closer import LoopCloser, LoopResult, _infer_sector, _slug
from src.capability_forge_real.models import BuildState


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_runs(path: Path, texts: list[str]) -> None:
    lines = [
        json.dumps({"run_id": f"run_{i}", "request_text": t})
        for i, t in enumerate(texts)
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _empty_caps(path: Path) -> None:
    path.write_text(yaml.dump({"capabilities": {}}), encoding="utf-8")


# ── _slug / _infer_sector ─────────────────────────────────────────────────────

class TestHelpers:
    def test_slug_basic(self):
        assert _slug("criar post viagem") == "criar_post_viagem"

    def test_slug_removes_special(self):
        assert _slug("hotel@natal!") == "hotel_natal"

    def test_infer_sector_midia(self):
        assert _infer_sector("criar post de viagem em natal") == "midia"

    def test_infer_sector_comercial(self):
        assert _infer_sector("qualificar lead de hotel") == "comercial"

    def test_infer_sector_financeiro(self):
        assert _infer_sector("gerar relatorio mensal") == "financeiro"

    def test_infer_sector_default(self):
        assert _infer_sector("algo completamente desconhecido xyzabc") == "automacao"


# ── LoopResult ────────────────────────────────────────────────────────────────

class TestLoopResult:
    def test_succeeded_true_when_done(self):
        r = LoopResult(candidate_text="x", candidate_count=3, build_state="done")
        assert r.succeeded is True

    def test_succeeded_false_when_skipped(self):
        r = LoopResult(candidate_text="x", candidate_count=3, build_state="done", skipped=True)
        assert r.succeeded is False

    def test_succeeded_false_when_error(self):
        r = LoopResult(candidate_text="x", candidate_count=3, build_state="done", error="oops")
        assert r.succeeded is False

    def test_succeeded_false_when_score_failed(self):
        r = LoopResult(candidate_text="x", candidate_count=3, build_state="score_failed")
        assert r.succeeded is False

    def test_succeeded_false_when_none_build_state(self):
        r = LoopResult(candidate_text="x", candidate_count=3)
        assert r.succeeded is False

    def test_to_dict_keys(self):
        r = LoopResult(candidate_text="t", candidate_count=3)
        d = r.to_dict()
        expected = {"candidate_text", "candidate_count", "cap_id", "proposal_id",
                    "build_state", "activated_skill_id", "skipped", "skip_reason",
                    "error", "succeeded", "pending_approval"}
        assert set(d.keys()) == expected

    def test_to_dict_succeeded_reflects_state(self):
        r = LoopResult(candidate_text="t", candidate_count=3, build_state="done")
        assert r.to_dict()["succeeded"] is True


# ── LoopCloser: empty / below threshold ──────────────────────────────────────

class TestLoopCloserEdgeCases:
    def test_missing_log_returns_empty(self, tmp_path):
        caps = tmp_path / "caps.yaml"
        _empty_caps(caps)
        closer = LoopCloser(
            runs_log=tmp_path / "nope.jsonl", threshold=3,
            dry_run=True, caps_path=caps,
        )
        assert closer.run() == []

    def test_below_threshold_returns_empty(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["criar post natal", "criar post natal"])  # only 2
        caps = tmp_path / "caps.yaml"
        _empty_caps(caps)
        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        assert closer.run() == []


# ── LoopCloser: happy path ────────────────────────────────────────────────────

class TestLoopCloserHappyPath:
    def test_single_candidate_returns_one_result(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["criar post natal"] * 3)
        caps = tmp_path / "caps.yaml"
        _empty_caps(caps)
        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        results = closer.run()
        assert len(results) == 1

    def test_result_build_state_done(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["criar post natal"] * 3)
        caps = tmp_path / "caps.yaml"
        _empty_caps(caps)
        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        result = closer.run()[0]
        assert result.build_state == BuildState.DONE.value

    def test_result_succeeded(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["criar post natal"] * 3)
        caps = tmp_path / "caps.yaml"
        _empty_caps(caps)
        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        assert closer.run()[0].succeeded is True

    def test_result_cap_id_is_slug(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["criar post natal"] * 3)
        caps = tmp_path / "caps.yaml"
        _empty_caps(caps)
        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        result = closer.run()[0]
        assert result.cap_id == _slug("criar post natal")

    def test_result_has_proposal_id(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["criar post natal"] * 3)
        caps = tmp_path / "caps.yaml"
        _empty_caps(caps)
        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        result = closer.run()[0]
        assert result.proposal_id is not None
        assert result.proposal_id.startswith("prop_")

    def test_result_activated_skill_id_matches_cap_id(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["criar post natal"] * 3)
        caps = tmp_path / "caps.yaml"
        _empty_caps(caps)
        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        result = closer.run()[0]
        assert result.activated_skill_id == result.cap_id

    def test_candidate_text_preserved(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["Criar Post Natal"] * 3)
        caps = tmp_path / "caps.yaml"
        _empty_caps(caps)
        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        result = closer.run()[0]
        assert result.candidate_text == "Criar Post Natal"
        assert result.candidate_count == 3


# ── LoopCloser: dedup ─────────────────────────────────────────────────────────

class TestLoopCloserDedup:
    def test_already_registered_skips(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["criar post natal"] * 3)
        cap_id = _slug("criar post natal")
        caps = tmp_path / "caps.yaml"
        caps.write_text(yaml.dump({
            "capabilities": {
                cap_id: {"sector": "midia", "status": "active"}
            }
        }), encoding="utf-8")
        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        result = closer.run()[0]
        assert result.skipped is True
        assert result.skip_reason == "already_registered"

    def test_skipped_result_not_succeeded(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["criar post natal"] * 3)
        cap_id = _slug("criar post natal")
        caps = tmp_path / "caps.yaml"
        caps.write_text(yaml.dump({
            "capabilities": {cap_id: {"sector": "midia", "status": "active"}}
        }), encoding="utf-8")
        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        assert closer.run()[0].succeeded is False


# ── LoopCloser: multiple candidates ──────────────────────────────────────────

class TestLoopCloserMultiple:
    def test_two_candidates_two_results(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["criar post natal"] * 3 + ["qualificar lead hotel"] * 4)
        caps = tmp_path / "caps.yaml"
        _empty_caps(caps)
        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        results = closer.run()
        assert len(results) == 2

    def test_all_results_succeeded(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["criar post natal"] * 3 + ["qualificar lead hotel"] * 4)
        caps = tmp_path / "caps.yaml"
        _empty_caps(caps)
        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        results = closer.run()
        assert all(r.succeeded for r in results)


# ── LoopCloser: sandbox rejection propagates ─────────────────────────────────

class TestLoopCloserSandboxRejection:
    def test_sandbox_blocked_propagates_to_loop_result(
        self, tmp_path, monkeypatch
    ):
        from src.capability_forge_real.sandbox import SandboxResult, SandboxStatus
        import src.capability_forge_real.builder as builder_mod

        def blocked(self_inner, code, run_id=""):
            return SandboxResult(
                run_id=run_id,
                status=SandboxStatus.BLOCKED,
                blocked_patterns=["subprocess"],
            )

        monkeypatch.setattr(builder_mod.SandboxRunner, "dry_run_validate", blocked)

        log = tmp_path / "runs.jsonl"
        _write_runs(log, ["criar post natal"] * 3)
        caps = tmp_path / "caps.yaml"
        _empty_caps(caps)

        closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
        result = closer.run()[0]
        assert result.build_state == BuildState.SCORE_FAILED.value
        assert result.succeeded is False
