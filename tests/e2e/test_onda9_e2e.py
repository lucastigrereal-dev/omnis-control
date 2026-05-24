"""Validação Final Onda 9 — Self-Improving Loop end-to-end.

Verifica o ciclo completo:
  repeated request_text in JSONL
  → RepetitionDetector (FIO 1) surfaces candidate
  → LoopCloser (FIO 2) proposes + builds via sandbox rail (FIO 4)
  → activated_skill_id set via SkillCatalog activation (FIO 3)

Todos os testes usam dry_run=True e tmp_path — sem escrita em disco real.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src.capability_forge_real.loop_closer import LoopCloser, _slug
from src.capability_forge_real.repetition_detector import RepetitionDetector
from src.capability_forge_real.models import BuildState
from src.mission_orchestrator.service import DEFAULT_RUNS_LOG


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_runs(path: Path, texts: list[str]) -> None:
    lines = [
        json.dumps({"run_id": f"run_{i:04d}", "request_text": t})
        for i, t in enumerate(texts)
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _empty_caps(path: Path) -> None:
    path.write_text(yaml.dump({"capabilities": {}}), encoding="utf-8")


def _closer(tmp_path: Path, texts: list[str], threshold: int = 3) -> tuple[LoopCloser, Path]:
    log = tmp_path / "runs.jsonl"
    _write_runs(log, texts)
    caps = tmp_path / "caps.yaml"
    _empty_caps(caps)
    return LoopCloser(runs_log=log, threshold=threshold, dry_run=True, caps_path=caps), log


# ── FIO 1 standalone ─────────────────────────────────────────────────────────

def test_detector_surfaces_repeated_task(tmp_path):
    """FIO 1: RepetitionDetector retorna candidato quando request_text se repete >= threshold."""
    log = tmp_path / "runs.jsonl"
    _write_runs(log, ["criar post de viagem natal"] * 3)
    candidates = RepetitionDetector(runs_log=log, threshold=3).detect()
    assert len(candidates) == 1
    assert candidates[0].count == 3
    assert candidates[0].normalized_text == "criar post de viagem natal"


def test_detector_ignores_below_threshold(tmp_path):
    """FIO 1: Menos de threshold não gera candidato."""
    log = tmp_path / "runs.jsonl"
    _write_runs(log, ["criar post de viagem natal"] * 2)
    assert RepetitionDetector(runs_log=log, threshold=3).detect() == []


# ── FIO 1 → FIO 2 chain ──────────────────────────────────────────────────────

def test_fio1_fio2_candidate_counts_match(tmp_path):
    """RepetitionDetector e LoopCloser operam sobre o mesmo conjunto de dados."""
    texts = ["qualificar lead hotel"] * 4 + ["criar carrossel viagem"] * 3
    log = tmp_path / "runs.jsonl"
    _write_runs(log, texts)
    caps = tmp_path / "caps.yaml"
    _empty_caps(caps)

    candidates = RepetitionDetector(runs_log=log, threshold=3).detect()
    results = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps).run()

    assert len(candidates) == len(results)


def test_loop_result_cap_id_matches_detector_slug(tmp_path):
    """cap_id no LoopResult é o slug do normalized_text do RepetitionCandidate."""
    closer, _ = _closer(tmp_path, ["qualificar lead hotel"] * 3)
    candidates = RepetitionDetector(runs_log=tmp_path / "runs.jsonl", threshold=3).detect()
    results = closer.run()

    assert results[0].cap_id == _slug(candidates[0].normalized_text)


# ── Full loop: detect → build → activate ─────────────────────────────────────

def test_full_loop_result_succeeded(tmp_path):
    """Ciclo completo: task repetida → LoopCloser → result.succeeded=True."""
    closer, _ = _closer(tmp_path, ["criar post de viagem natal"] * 3)
    results = closer.run()
    assert len(results) == 1
    assert results[0].succeeded is True


def test_full_loop_build_state_done(tmp_path):
    """build_state deve ser DONE após loop bem-sucedido."""
    closer, _ = _closer(tmp_path, ["criar post de viagem natal"] * 3)
    result = closer.run()[0]
    assert result.build_state == BuildState.DONE.value


def test_full_loop_activated_skill_id_set(tmp_path):
    """FIO 3 wire: activated_skill_id está preenchido após DONE."""
    closer, _ = _closer(tmp_path, ["criar post de viagem natal"] * 3)
    result = closer.run()[0]
    assert result.activated_skill_id is not None
    assert result.activated_skill_id == result.cap_id


def test_full_loop_proposal_id_set(tmp_path):
    """LoopCloser gera proposal_id válido antes de construir."""
    closer, _ = _closer(tmp_path, ["criar post de viagem natal"] * 3)
    result = closer.run()[0]
    assert result.proposal_id is not None
    assert result.proposal_id.startswith("prop_")


def test_full_loop_candidate_metadata_preserved(tmp_path):
    """candidate_text e candidate_count chegam intactos no LoopResult."""
    closer, _ = _closer(tmp_path, ["Criar Post de Viagem Natal"] * 5)
    result = closer.run()[0]
    assert result.candidate_text == "Criar Post de Viagem Natal"
    assert result.candidate_count == 5


# ── FIO 4 (sandbox rail) wired in loop ───────────────────────────────────────

def test_sandbox_rail_rejects_broken_skill_in_loop(tmp_path, monkeypatch):
    """Sandbox blocked → SCORE_FAILED propaga até LoopResult.succeeded=False."""
    from src.capability_forge_real.sandbox import SandboxResult, SandboxStatus
    import src.capability_forge_real.builder as builder_mod

    def blocked(self_inner, code, run_id=""):
        return SandboxResult(
            run_id=run_id,
            status=SandboxStatus.BLOCKED,
            blocked_patterns=["subprocess"],
        )

    monkeypatch.setattr(builder_mod.SandboxRunner, "dry_run_validate", blocked)

    closer, _ = _closer(tmp_path, ["criar post de viagem natal"] * 3)
    result = closer.run()[0]
    assert result.build_state == BuildState.SCORE_FAILED.value
    assert result.succeeded is False


def test_low_evaluator_score_rejects_in_loop(tmp_path, monkeypatch):
    """Evaluator grade F → SCORE_FAILED → loop result não bem-sucedido."""
    from src.capability_forge_real.evaluator import EvaluatorScorecard, ScoreGrade, DimensionScore
    import src.capability_forge_real.builder as builder_mod

    def low_score(**kwargs):
        return EvaluatorScorecard(
            capability_name=kwargs.get("capability_name", ""),
            dimensions=[DimensionScore(name="code_quality", score=1.0)],
            total_score=5.0,
            max_total=50.0,
            grade=ScoreGrade.F,
        )

    monkeypatch.setattr(builder_mod.CapabilityEvaluator, "evaluate", staticmethod(low_score))

    closer, _ = _closer(tmp_path, ["criar post de viagem natal"] * 3)
    result = closer.run()[0]
    assert result.build_state == BuildState.SCORE_FAILED.value


# ── Dedup ─────────────────────────────────────────────────────────────────────

def test_second_run_skips_already_registered(tmp_path):
    """Chamar run() com caps_path já contendo o cap_id → skipped."""
    texts = ["criar post de viagem natal"] * 3
    log = tmp_path / "runs.jsonl"
    _write_runs(log, texts)
    cap_id = _slug("criar post de viagem natal")
    caps = tmp_path / "caps.yaml"
    caps.write_text(
        yaml.dump({"capabilities": {cap_id: {"sector": "midia", "status": "active"}}}),
        encoding="utf-8",
    )
    closer = LoopCloser(runs_log=log, threshold=3, dry_run=True, caps_path=caps)
    result = closer.run()[0]
    assert result.skipped is True
    assert result.skip_reason == "already_registered"
    assert result.succeeded is False


# ── Multiple candidates ───────────────────────────────────────────────────────

def test_multiple_repeated_tasks_all_built(tmp_path):
    """Dois padrões distintos repetidos → dois LoopResults, ambos succeeded."""
    texts = (
        ["criar post viagem natal"] * 3
        + ["qualificar lead hotel praia"] * 4
    )
    closer, _ = _closer(tmp_path, texts)
    results = closer.run()
    assert len(results) == 2
    assert all(r.succeeded for r in results)


def test_multiple_results_distinct_cap_ids(tmp_path):
    """Dois padrões distintos → dois cap_ids distintos."""
    texts = (
        ["criar post viagem natal"] * 3
        + ["qualificar lead hotel praia"] * 3
    )
    closer, _ = _closer(tmp_path, texts)
    results = closer.run()
    cap_ids = [r.cap_id for r in results]
    assert cap_ids[0] != cap_ids[1]


# ── Live log smoke ────────────────────────────────────────────────────────────

def test_real_log_has_known_candidate():
    """Smoke: o log real já contém 'criar post de viagem em natal' repetido >= 3x."""
    if not DEFAULT_RUNS_LOG.exists():
        pytest.skip("data/orchestrator_runs.jsonl não encontrado")
    candidates = RepetitionDetector(runs_log=DEFAULT_RUNS_LOG, threshold=3).detect()
    norms = {c.normalized_text for c in candidates}
    assert "criar post de viagem em natal" in norms
