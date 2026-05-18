"""Tests for SkillRunnerBridge — execution of dispatch entries via SkillSelector."""
from __future__ import annotations

import pytest

from src.agentic.deliverable_mapper import (
    DeliverableManifest,
    DeliverableMapper,
    DeliverableSpec,
)
from src.agentic.mission_intake import MissionIntake
from src.agentic.task_dispatcher import DispatchEntry, TaskDispatcher
from src.agentic.skill_runner_bridge import (
    SkillRunnerBridge,
    ExecutionResult,
    _resolve_tags,
    _resolve_intent,
)
from src.skills_bridge.models import SkillIntent


# ── fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def bridge():
    return SkillRunnerBridge(dry_run=True)


@pytest.fixture
def live_bridge():
    return SkillRunnerBridge(dry_run=False)


@pytest.fixture
def marketing_plan():
    intake = MissionIntake().parse("criar campanha de marketing para hotel")
    manifest = DeliverableMapper().map(intake)
    return TaskDispatcher(dry_run=True).dispatch(manifest, "MIS-MKT")


@pytest.fixture
def sales_plan():
    manifest = DeliverableManifest(
        mission_id=None, setor="sales", tipo="sales",
        deliverables=[
            DeliverableSpec("lead_list.csv", "Leads qualificados", "csv"),
            DeliverableSpec("dm_sequence.md", "Sequência DM", "md"),
            DeliverableSpec("proposta_comercial.md", "Proposta", "md"),
        ],
    )
    return TaskDispatcher(dry_run=True).dispatch(manifest, "MIS-SALES")


# ── tag/intent resolution ──────────────────────────────────────────────

class TestTagResolution:
    def test_legenda_tags(self):
        tags = _resolve_tags("legenda_final.md")
        assert "caption" in tags or "instagram" in tags

    def test_lead_tags(self):
        tags = _resolve_tags("lead_list.csv")
        assert any(t in tags for t in ["crm", "sales", "leads"])

    def test_prd_tags(self):
        tags = _resolve_tags("PRD.md")
        assert any(t in tags for t in ["app", "factory", "development"])

    def test_unknown_fallback(self):
        tags = _resolve_tags("unknown_file.xyz")
        assert "general" in tags


class TestIntentResolution:
    def test_legenda_is_create(self):
        assert _resolve_intent("legenda_final.md") == SkillIntent.CREATE

    def test_lead_is_read(self):
        assert _resolve_intent("lead_list.csv") == SkillIntent.READ

    def test_hashtag_is_analyze(self):
        assert _resolve_intent("hashtags.json") == SkillIntent.ANALYZE

    def test_unknown_is_generate(self):
        assert _resolve_intent("something_new.md") == SkillIntent.GENERATE


# ── ExecutionResult ────────────────────────────────────────────────────

class TestExecutionResult:
    def test_to_dict(self):
        r = ExecutionResult(
            entry_id="TSK-01", skill_id="s1", status="dry_run",
            output="ok", duration_ms=10,
        )
        d = r.to_dict()
        assert d["entry_id"] == "TSK-01"
        assert d["status"] == "dry_run"


# ── execute_entry ──────────────────────────────────────────────────────

class TestExecuteEntry:
    def test_dry_run_returns_dry_run_status(self, bridge):
        entry = DispatchEntry(
            task_id="TSK-01", deliverable="legenda_final.md", executor="publisher",
        )
        result = bridge.execute_entry(entry)
        assert result.status == "dry_run"
        assert result.entry_id == "TSK-01"
        assert result.skill_id != ""
        assert result.skill_id in ("generate_seogram_caption", "create_instagram_carousel")

    def test_live_mode_with_dry_entry_still_dry(self, live_bridge):
        entry = DispatchEntry(
            task_id="TSK-02", deliverable="legenda_final.md", executor="publisher",
            dry_run=True,
        )
        result = live_bridge.execute_entry(entry)
        assert result.status == "dry_run"

    def test_entry_with_sales_deliverable(self, bridge):
        entry = DispatchEntry(
            task_id="TSK-03", deliverable="lead_list.csv", executor="sales",
        )
        result = bridge.execute_entry(entry)
        assert result.status == "dry_run"
        assert result.skill_id in ("crm-pipeline", "manual-review")

    def test_entry_with_app_factory_deliverable(self, bridge):
        entry = DispatchEntry(
            task_id="TSK-04", deliverable="PRD.md", executor="app_factory",
        )
        result = bridge.execute_entry(entry)
        assert result.status in ("dry_run", "needs_review")

    def test_entry_with_computer_ops_deliverable(self, bridge):
        entry = DispatchEntry(
            task_id="TSK-05", deliverable="audit_report.md", executor="computer_ops",
        )
        result = bridge.execute_entry(entry)
        assert result.status in ("dry_run", "needs_review")

    def test_entry_with_unknown_deliverable_falls_back(self, bridge):
        entry = DispatchEntry(
            task_id="TSK-06", deliverable="weird_thing.xyz", executor="skill_runner",
        )
        result = bridge.execute_entry(entry)
        assert result.status in ("dry_run", "needs_review")


# ── execute_plan ───────────────────────────────────────────────────────

class TestExecutePlan:
    def test_executes_all_entries(self, bridge, marketing_plan):
        results = bridge.execute_plan(marketing_plan)
        assert len(results) == len(marketing_plan.entries)
        assert all(r.status == "dry_run" for r in results)

    def test_updates_entry_status_after_execution(self, bridge, marketing_plan):
        bridge.execute_plan(marketing_plan)
        for entry in marketing_plan.entries:
            assert entry.status == "done"
            assert entry.finished_at is not None
            assert entry.result_hint != ""

    def test_execute_sales_plan(self, bridge, sales_plan):
        results = bridge.execute_plan(sales_plan)
        assert len(results) == 3
        assert sales_plan.entries[0].status == "done"

    def test_execute_empty_plan(self, bridge):
        plan = TaskDispatcher(dry_run=True).dispatch(
            DeliverableManifest(
                mission_id=None, setor="general", tipo="general",
                deliverables=[],
            ),
            "MIS-EMPTY",
        )
        results = bridge.execute_plan(plan)
        assert results == []


# ── integration: dispatcher → bridge ───────────────────────────────────

class TestDispatcherToBridgeIntegration:
    def test_full_marketing_flow(self, bridge):
        intake = MissionIntake().parse("criar conteúdo instagram família viagem")
        manifest = DeliverableMapper().map(intake)
        plan = TaskDispatcher(dry_run=True).dispatch(manifest, "MIS-INT")
        assert plan.total > 0

        results = bridge.execute_plan(plan)
        assert len(results) == plan.total
        for r in results:
            assert r.status in ("dry_run", "needs_review")

    def test_full_sales_flow(self, bridge):
        intake = MissionIntake().parse("qualificar leads prospeccao vendas crm")
        manifest = DeliverableMapper().map(intake)
        plan = TaskDispatcher(dry_run=True).dispatch(manifest, "MIS-SALES2")
        assert plan.entries[0].executor == "sales"

        results = bridge.execute_plan(plan)
        assert len(results) == plan.total

    def test_dispatch_plan_to_dict_after_bridge(self, bridge, marketing_plan):
        bridge.execute_plan(marketing_plan)
        d = marketing_plan.to_dict()
        assert all(
            e["status"] == "done" and e["finished_at"] is not None
            for e in d["entries"]
        )
