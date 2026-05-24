"""Testes da ponte SkillRunnerBridge ↔ LegoRegistry (Onda 8 Passo 3)."""
from __future__ import annotations

import pytest

from src.agentic.skill_runner_bridge import SkillRunnerBridge, _ROLE_TO_LEGO
from src.agentic.task_dispatcher import DispatchEntry
from src.legos.registry import LegoRegistry, default_registry
from src.legos.channel_messenger_lego import ChannelMessengerLego
from src.legos.code_executor_lego import CodeExecutorLego
from src.legos.research_conductor_lego import ResearchConductorLego
from src.utils.run_context import RunContext


# ── configuração básica ───────────────────────────────────────────────────────

def test_bridge_accepts_lego_registry():
    reg = default_registry()
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg)
    assert bridge.lego_registry is reg


def test_bridge_accepts_run_context():
    ctx = RunContext.new()
    bridge = SkillRunnerBridge(dry_run=True, run_context=ctx)
    assert bridge.run_context is ctx


def test_bridge_without_registry_uses_skill_path():
    bridge = SkillRunnerBridge(dry_run=True)
    assert bridge.lego_registry is None


# ── mapeamento role → lego ────────────────────────────────────────────────────

def test_role_to_lego_map_covers_core_roles():
    assert _ROLE_TO_LEGO["research_lead"] == "research_conductor"
    assert _ROLE_TO_LEGO["code_executor"] == "code_executor"
    assert _ROLE_TO_LEGO["channel_messenger"] == "channel_messenger"
    assert _ROLE_TO_LEGO["publisher"] == "channel_messenger"
    assert _ROLE_TO_LEGO["video_processor"] == "video_processor"
    assert _ROLE_TO_LEGO["browser_executor"] == "browser_executor"


# ── _try_lego ─────────────────────────────────────────────────────────────────

def test_try_lego_returns_none_when_no_registry():
    bridge = SkillRunnerBridge(dry_run=True)
    entry = DispatchEntry(
        task_id="t1", deliverable="research topic", executor="research_lead", dry_run=True,
    )
    result = bridge._try_lego(entry)
    assert result is None


def test_try_lego_returns_none_for_unmapped_executor():
    reg = default_registry()
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg)
    entry = DispatchEntry(
        task_id="t1", deliverable="do something", executor="copywriter", dry_run=True,
    )
    result = bridge._try_lego(entry)
    assert result is None


def test_try_lego_routes_to_research_conductor():
    reg = default_registry()
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg)
    entry = DispatchEntry(
        task_id="t1",
        deliverable="research about tourism in Natal RN",
        executor="research_lead",
        dry_run=True,
    )
    result = bridge._try_lego(entry)
    assert result is not None
    assert result.skill_id == "lego:research_conductor"
    assert result.status == "dry_run"
    assert result.entry_id == "t1"


def test_try_lego_routes_to_code_executor():
    reg = default_registry()
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg)
    entry = DispatchEntry(
        task_id="t2",
        deliverable="write a python script to parse JSON",
        executor="code_executor",
        dry_run=True,
    )
    result = bridge._try_lego(entry)
    assert result is not None
    assert result.skill_id == "lego:code_executor"
    assert result.status == "dry_run"


def test_try_lego_routes_to_channel_messenger():
    reg = default_registry()
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg)
    entry = DispatchEntry(
        task_id="t3",
        deliverable="send notification: pipeline complete",
        executor="channel_messenger",
        dry_run=True,
    )
    result = bridge._try_lego(entry)
    assert result is not None
    assert result.skill_id == "lego:channel_messenger"
    assert result.status == "dry_run"


def test_try_lego_propagates_run_id():
    reg = default_registry()
    ctx = RunContext.new()
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg, run_context=ctx)
    entry = DispatchEntry(
        task_id="t1",
        deliverable="research about hotels",
        executor="research_lead",
        dry_run=True,
    )
    result = bridge._try_lego(entry)
    assert result is not None
    assert result.status == "dry_run"


def test_try_lego_passes_run_id_into_legocog_spec():
    captured: dict[str, object] = {}

    class _FakeLego:
        def run(self, spec):
            captured["run_id"] = spec.run_id
            from src.legos.protocol import LegoCogResult
            return LegoCogResult(success=True, output="ok", dry_run=True)

        def health_check(self):
            return True

    reg = LegoRegistry()
    reg.register("research_conductor", _FakeLego())
    ctx = RunContext(run_id="ctx_run_777")
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg, run_context=ctx)
    entry = DispatchEntry(
        task_id="tctx",
        deliverable="research coastal tourism trends",
        executor="research_lead",
        dry_run=True,
    )
    result = bridge._try_lego(entry)
    assert result is not None
    assert result.status == "dry_run"
    assert captured["run_id"] == "ctx_run_777"


# ── execute_entry com lego ────────────────────────────────────────────────────

def test_execute_entry_uses_lego_when_registry_present():
    reg = default_registry()
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg)
    entry = DispatchEntry(
        task_id="t10",
        deliverable="research luxury hotels in Brazil",
        executor="research_lead",
        dry_run=True,
    )
    result = bridge.execute_entry(entry)
    assert result.skill_id == "lego:research_conductor"
    assert result.status == "dry_run"


def test_execute_entry_falls_back_to_skill_when_no_lego_match():
    reg = default_registry()
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg)
    entry = DispatchEntry(
        task_id="t20",
        deliverable="generate instagram caption",
        executor="copywriter",
        dry_run=True,
    )
    result = bridge.execute_entry(entry)
    # fell through to skill path — skill_id should NOT start with "lego:"
    assert not result.skill_id.startswith("lego:")


def test_execute_entry_exact_lego_name_matches():
    reg = LegoRegistry()
    reg.register("channel_messenger", ChannelMessengerLego())
    bridge = SkillRunnerBridge(dry_run=True, lego_registry=reg)
    entry = DispatchEntry(
        task_id="t30",
        deliverable="Novo conteúdo publicado!",
        executor="channel_messenger",  # exact lego name
        dry_run=True,
    )
    result = bridge.execute_entry(entry)
    assert result.skill_id == "lego:channel_messenger"
    assert result.status == "dry_run"
