"""Tests for OrchestratorRun and OrchestratorStep models."""
import pytest
from src.mission_orchestrator.models import (
    OrchestratorRun,
    OrchestratorStep,
    RUN_STATUS_PLANNED,
)


def test_run_new_creates_run_id():
    r = OrchestratorRun.new("cria carrossel hotel")
    assert r.run_id.startswith("run_")
    assert len(r.run_id) > 6


def test_run_new_defaults():
    r = OrchestratorRun.new("test request")
    assert r.status == RUN_STATUS_PLANNED
    assert r.dry_run is True
    assert r.steps == []


def test_run_to_dict_round_trip():
    r = OrchestratorRun.new("request text", account_handle="oinatalrn", intent="reels")
    r.steps.append(OrchestratorStep("s01", "label", "module", "cmd"))
    d = r.to_dict()
    r2 = OrchestratorRun.from_dict(d)
    assert r2.run_id == r.run_id
    assert r2.intent == "reels"
    assert len(r2.steps) == 1
    assert r2.steps[0].step_id == "s01"


def test_step_to_dict():
    s = OrchestratorStep("s01", "my label", "mission_builder", "jarvis mission run")
    d = s.to_dict()
    assert d["step_id"] == "s01"
    assert d["label"] == "my label"
    assert d["status"] == "pending"
