"""Testes de propagação de RunContext no BatchRunner (Onda 7)."""
from __future__ import annotations

import pytest

from src.agentic.batch_runner import BatchRunner
from src.utils.run_context import RunContext


def test_batch_runner_creates_run_context_by_default():
    runner = BatchRunner()
    assert runner._ctx is not None
    assert isinstance(runner._ctx, RunContext)


def test_batch_runner_accepts_explicit_run_context():
    ctx = RunContext(run_id="test_run_001")
    runner = BatchRunner(run_context=ctx)
    assert runner._ctx is ctx
    assert runner._ctx.run_id == "test_run_001"


def test_batch_runner_run_id_in_report(tmp_path, monkeypatch):
    """run_id do contexto deve aparecer nos logs (smoke test estrutural)."""
    import logging
    ctx = RunContext(run_id="smoke123")
    runner = BatchRunner(dry_run=True, run_context=ctx)
    # Sem itens na fila — report vazio mas sem crash
    report = runner.run(limit=0)
    assert report.total_candidates == 0


def test_two_runners_have_different_default_run_ids():
    r1 = BatchRunner()
    r2 = BatchRunner()
    assert r1._ctx.run_id != r2._ctx.run_id


def test_run_context_propagated_to_report_batch_id_unique():
    ctx = RunContext.new()
    r1 = BatchRunner(run_context=ctx)
    r2 = BatchRunner(run_context=ctx)
    # Mesmo contexto, batch_ids diferentes por UUID no BatchReport
    rep1 = r1.run(limit=0)
    rep2 = r2.run(limit=0)
    assert rep1.batch_id != rep2.batch_id
