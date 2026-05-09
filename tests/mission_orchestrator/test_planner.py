"""Tests for mission orchestrator planner."""
import pytest
from src.mission_orchestrator.planner import build_plan
from src.mission_orchestrator.errors import UnknownIntentError
from src.mission_orchestrator.models import RUN_STATUS_PLANNED


def test_plan_creates_run_with_steps():
    run = build_plan("cria um carrossel para hotel em Natal")
    assert run.run_id.startswith("run_")
    assert run.status == RUN_STATUS_PLANNED
    assert len(run.steps) >= 2


def test_plan_detects_reels_intent():
    run = build_plan("quero um reels do hotel")
    assert run.intent == "reels"


def test_plan_detects_carrossel_intent():
    run = build_plan("preciso de um carrossel")
    assert run.intent == "carousel"


def test_plan_unknown_raises():
    with pytest.raises(UnknownIntentError):
        build_plan("algo que nao bate com nada")


def test_plan_unknown_allow_unknown():
    run = build_plan("algo indefinido", allow_unknown=True)
    assert run.intent == "unknown"
    assert run.status == RUN_STATUS_PLANNED


def test_plan_steps_include_mission_builder():
    run = build_plan("carrossel hotel Natal")
    modules = [s.module for s in run.steps]
    assert "mission_builder" in modules


def test_plan_steps_include_mission_report():
    run = build_plan("reels praia Natal")
    modules = [s.module for s in run.steps]
    assert "mission_report" in modules


def test_plan_dry_run_skips_asset_steps():
    run = build_plan("carrossel hotel", dry_run=True)
    skipped = [s for s in run.steps if s.module == "asset_inbox" and s.status == "skipped"]
    assert len(skipped) >= 1
