"""Tests for mission orchestrator planner."""
import pytest
from src.mission_orchestrator.planner import (
    _apply_capability_intelligence,
    _build_steps,
    _match_capabilities,
    _parse_intent,
    _validate_plan,
    build_plan,
)
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


def test_parse_intent_returns_detected_tuple():
    intent, deliverable, description = _parse_intent("quero um reels do hotel")
    assert intent == "reels"
    assert deliverable
    assert description


def test_match_capabilities_returns_capabilities_and_sector():
    cap_results, sector_result = _match_capabilities("cria campanha de posts para hotel")
    assert len(cap_results) >= 1
    assert sector_result is not None


def test_build_steps_preserves_dry_run_asset_skips():
    steps = _build_steps("carrossel hotel", dry_run=True)
    asset_steps = [step for step in steps if step.module == "asset_inbox"]
    assert len(asset_steps) == 2
    assert all(step.status == "skipped" for step in asset_steps)


def test_validate_plan_rejects_unknown_without_capability():
    with pytest.raises(UnknownIntentError):
        _validate_plan(
            request_text="algo que nao bate com nada",
            intent="unknown",
            cap_results=[],
            allow_unknown=False,
        )


def test_validate_plan_allows_unknown_when_capability_exists():
    class _Cap:
        capability_id = "cap_demo"
        risk_level = "low"

    _validate_plan(
        request_text="pedido fora da taxonomia, mas com match de cap",
        intent="unknown",
        cap_results=[_Cap()],
        allow_unknown=False,
    )


def test_apply_capability_intelligence_uses_gap_when_no_capabilities(monkeypatch):
    from src.mission_orchestrator.models import OrchestratorRun
    from src.capability_gap import detector as gap_detector

    class _Gap:
        def __init__(self, gap_id: str, risk_level: str):
            self.gap_id = gap_id
            self.risk_level = risk_level

    class _GapResult:
        def __init__(self):
            self.gaps = [_Gap("gap_1", "medium"), _Gap("gap_2", "low")]

    monkeypatch.setattr(gap_detector, "detect", lambda _request: _GapResult())

    run = OrchestratorRun.new("request sem capabilities")
    _apply_capability_intelligence(
        run=run,
        request_text="request sem capabilities",
        cap_results=[],
        sector_result=None,
    )

    assert run.sector_id == "unknown"
    assert run.matched_capabilities == []
    assert run.suggested_gap_ids == ["gap_1", "gap_2"]
    assert run.approval_required is True
