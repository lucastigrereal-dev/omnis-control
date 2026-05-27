"""Tests for src/agencia/budget_guardrail.py — W19.

10 tests covering:
1.  BudgetConfig defaults
2.  check_daily with zero spend → not blocked
3.  check_daily at 80% → warning=True, not blocked
4.  check_daily over limit → blocked
5.  check_monthly over limit → blocked
6.  check_mission over per_mission_limit → blocked
7.  record_spend creates file
8.  daily_total reads correctly
9.  monthly_total reads multiple files
10. to_dict includes all fields
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.agencia.budget_guardrail import BudgetConfig, BudgetGuardrail, GuardrailResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _guardrail(tmp_path: Path, **config_kwargs) -> BudgetGuardrail:
    cfg = BudgetConfig(**config_kwargs) if config_kwargs else BudgetConfig()
    return BudgetGuardrail(config=cfg, data_dir=tmp_path, dry_run=False)


def _write_spend(data_dir: Path, date_str: str, usd: float, mission_id: str = ""):
    """Manually write a spend entry for a given date."""
    entry = {
        "ts": f"{date_str}T00:00:00+00:00",
        "usd": usd,
        "mission_id": mission_id,
    }
    target = data_dir / f"spend_{date_str}.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# 1. BudgetConfig defaults
# ---------------------------------------------------------------------------


def test_budget_config_defaults():
    cfg = BudgetConfig()
    assert cfg.daily_limit_usd == 5.0
    assert cfg.monthly_limit_usd == 50.0
    assert cfg.per_mission_limit_usd == 0.50
    assert cfg.warn_threshold == 0.80


# ---------------------------------------------------------------------------
# 2. check_daily with zero spend → not blocked
# ---------------------------------------------------------------------------


def test_check_daily_zero_spend(tmp_path):
    g = _guardrail(tmp_path)
    result = g.check_daily()
    assert not result.is_blocked
    assert not result.warning
    assert result.current_usd == 0.0
    assert result.limit_usd == 5.0


# ---------------------------------------------------------------------------
# 3. check_daily at 80% → warning=True, not blocked
# ---------------------------------------------------------------------------


def test_check_daily_at_warn_threshold(tmp_path):
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    _write_spend(tmp_path, today, usd=4.0)   # 80% of 5.0

    g = _guardrail(tmp_path)
    result = g.check_daily()

    assert not result.is_blocked
    assert result.warning
    assert result.current_usd == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# 4. check_daily over limit → blocked
# ---------------------------------------------------------------------------


def test_check_daily_over_limit(tmp_path):
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    _write_spend(tmp_path, today, usd=6.0)   # 120% of 5.0

    g = _guardrail(tmp_path)
    result = g.check_daily()

    assert result.is_blocked
    assert result.current_usd == pytest.approx(6.0)
    assert "daily" in result.reason


# ---------------------------------------------------------------------------
# 5. check_monthly over limit → blocked
# ---------------------------------------------------------------------------


def test_check_monthly_over_limit(tmp_path):
    # Write enough spend across two days this month
    month = datetime.now(tz=timezone.utc).strftime("%Y-%m")
    _write_spend(tmp_path, f"{month}-01", usd=30.0)
    _write_spend(tmp_path, f"{month}-02", usd=25.0)   # total 55 > 50

    g = _guardrail(tmp_path)
    result = g.check_monthly()

    assert result.is_blocked
    assert result.current_usd == pytest.approx(55.0)
    assert "monthly" in result.reason


# ---------------------------------------------------------------------------
# 6. check_mission over per_mission_limit → blocked
# ---------------------------------------------------------------------------


def test_check_mission_over_limit(tmp_path):
    g = _guardrail(tmp_path)
    result = g.check_mission(estimated_usd=1.00)   # > 0.50 limit

    assert result.is_blocked
    assert result.current_usd == pytest.approx(1.00)
    assert result.limit_usd == pytest.approx(0.50)


# ---------------------------------------------------------------------------
# 7. record_spend creates file
# ---------------------------------------------------------------------------


def test_record_spend_creates_file(tmp_path):
    g = _guardrail(tmp_path)
    g.record_spend(0.10, mission_id="test-mission")

    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    spend_file = tmp_path / f"spend_{today}.jsonl"
    assert spend_file.exists()

    with spend_file.open() as fh:
        data = json.loads(fh.readline())

    assert data["usd"] == pytest.approx(0.10)
    assert data["mission_id"] == "test-mission"


# ---------------------------------------------------------------------------
# 8. daily_total reads correctly
# ---------------------------------------------------------------------------


def test_daily_total_reads_correctly(tmp_path):
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    _write_spend(tmp_path, today, usd=1.25)
    _write_spend(tmp_path, today, usd=0.75)

    g = _guardrail(tmp_path)
    assert g.daily_total() == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# 9. monthly_total reads multiple files
# ---------------------------------------------------------------------------


def test_monthly_total_reads_multiple_files(tmp_path):
    month = datetime.now(tz=timezone.utc).strftime("%Y-%m")
    _write_spend(tmp_path, f"{month}-01", usd=10.0)
    _write_spend(tmp_path, f"{month}-02", usd=5.5)
    _write_spend(tmp_path, f"{month}-03", usd=3.0)

    g = _guardrail(tmp_path)
    assert g.monthly_total() == pytest.approx(18.5)


# ---------------------------------------------------------------------------
# 10. to_dict includes all fields
# ---------------------------------------------------------------------------


def test_to_dict_includes_all_fields(tmp_path):
    g = _guardrail(tmp_path)
    d = g.to_dict()

    assert "config" in d
    assert "daily_total_usd" in d
    assert "monthly_total_usd" in d
    assert "dry_run" in d
    assert "data_dir" in d

    cfg = d["config"]
    assert "daily_limit_usd" in cfg
    assert "monthly_limit_usd" in cfg
    assert "per_mission_limit_usd" in cfg
    assert "warn_threshold" in cfg
