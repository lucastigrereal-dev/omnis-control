"""Testes de RunContext + BudgetExceededError."""
from __future__ import annotations

import math

import pytest

from src.utils.run_context import RunContext, BudgetExceededError


# ── RunContext construction ───────────────────────────────────────────────────

def test_run_id_is_generated():
    ctx = RunContext()
    assert len(ctx.run_id) == 12
    assert ctx.run_id.isalnum()


def test_two_contexts_have_different_run_ids():
    assert RunContext().run_id != RunContext().run_id


def test_explicit_run_id():
    ctx = RunContext(run_id="myrun001")
    assert ctx.run_id == "myrun001"


def test_cost_accumulated_starts_at_zero():
    ctx = RunContext()
    assert ctx.cost_accumulated == 0.0


def test_new_classmethod():
    ctx = RunContext.new(budget_usd=1.0)
    assert ctx.budget_usd == 1.0
    assert ctx.cost_accumulated == 0.0


def test_log_prefix_format():
    ctx = RunContext(run_id="abc123xyz012")
    assert ctx.log_prefix() == "[run:abc123xyz012]"


# ── budget unlimited ──────────────────────────────────────────────────────────

def test_unlimited_budget_never_raises():
    ctx = RunContext(budget_usd=0)
    ctx.check_budget(999.99)  # should not raise


def test_remaining_budget_unlimited_is_inf():
    ctx = RunContext(budget_usd=0)
    assert ctx.remaining_budget() == math.inf


# ── add_cost ──────────────────────────────────────────────────────────────────

def test_add_cost_accumulates():
    ctx = RunContext(budget_usd=1.0)
    ctx.add_cost(0.01)
    ctx.add_cost(0.02)
    assert abs(ctx.cost_accumulated - 0.03) < 1e-9


def test_add_cost_zero_ignored():
    ctx = RunContext(budget_usd=1.0)
    ctx.add_cost(0.0)
    assert ctx.cost_accumulated == 0.0


def test_add_cost_negative_ignored():
    ctx = RunContext(budget_usd=1.0)
    ctx.add_cost(-0.5)
    assert ctx.cost_accumulated == 0.0


# ── check_budget ──────────────────────────────────────────────────────────────

def test_check_budget_passes_within_limit():
    ctx = RunContext(budget_usd=1.0)
    ctx.check_budget(0.5)  # no raise


def test_check_budget_raises_when_exceeded():
    ctx = RunContext(budget_usd=0.10)
    ctx.add_cost(0.09)
    with pytest.raises(BudgetExceededError):
        ctx.check_budget(0.02)


def test_check_budget_raises_at_exact_limit():
    ctx = RunContext(budget_usd=0.10)
    ctx.add_cost(0.10)
    with pytest.raises(BudgetExceededError):
        ctx.check_budget(0.001)


def test_budget_exceeded_error_has_fields():
    err = BudgetExceededError(accumulated=0.09, budget=0.10, estimated=0.02)
    assert err.accumulated == 0.09
    assert err.budget == 0.10
    assert err.estimated == 0.02


def test_budget_exceeded_error_message():
    err = BudgetExceededError(0.09, 0.10, 0.02)
    assert "Budget excedido" in str(err)
    assert "0.10" in str(err)


# ── remaining_budget ──────────────────────────────────────────────────────────

def test_remaining_budget_full():
    ctx = RunContext(budget_usd=1.0)
    assert ctx.remaining_budget() == 1.0


def test_remaining_budget_after_spend():
    ctx = RunContext(budget_usd=1.0)
    ctx.add_cost(0.30)
    assert abs(ctx.remaining_budget() - 0.70) < 1e-9


def test_remaining_budget_floor_zero():
    ctx = RunContext(budget_usd=0.10)
    ctx.add_cost(0.10)
    ctx.add_cost(0.05)
    assert ctx.remaining_budget() == 0.0
