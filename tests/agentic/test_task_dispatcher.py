"""Tests for TaskDispatcher — routing, dry-run, plans, round-trips."""
from __future__ import annotations

import json

import pytest

from src.agentic.deliverable_mapper import (
    DeliverableManifest,
    DeliverableMapper,
    DeliverableSpec,
)
from src.agentic.mission_intake import MissionIntake
from src.agentic.task_dispatcher import (
    DispatchEntry,
    DispatchPlan,
    TaskDispatcher,
    SECTOR_EXECUTOR,
)


# ── fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def sample_manifest() -> DeliverableManifest:
    intake = MissionIntake().parse("criar campanha de marketing para hotel")
    return DeliverableMapper().map(intake)


@pytest.fixture
def dispatcher() -> TaskDispatcher:
    return TaskDispatcher(dry_run=True)


# ── DispatchEntry tests ────────────────────────────────────────────────

class TestDispatchEntry:
    def test_defaults(self):
        entry = DispatchEntry(task_id="TSK-001", deliverable="test.md", executor="publisher")
        assert entry.status == "pending"
        assert entry.dry_run is True
        assert entry.dispatched_at is None
        assert entry.result_hint == ""

    def test_to_dict(self):
        entry = DispatchEntry(
            task_id="TSK-001",
            deliverable="legenda_final.md",
            executor="publisher",
            status="dispatched",
            dry_run=False,
            dispatched_at="2026-05-18T10:00:00Z",
            result_hint="ok",
        )
        d = entry.to_dict()
        assert d["task_id"] == "TSK-001"
        assert d["executor"] == "publisher"
        assert d["dry_run"] is False

    def test_from_dict(self):
        data = {
            "task_id": "TSK-002",
            "deliverable": "lead_list.csv",
            "executor": "sales",
            "status": "done",
            "dry_run": True,
            "dispatched_at": None,
            "finished_at": None,
            "result_hint": "",
        }
        entry = DispatchEntry.from_dict(data)
        assert entry.task_id == "TSK-002"
        assert entry.executor == "sales"
        assert entry.status == "done"

    def test_round_trip(self):
        entry = DispatchEntry(
            task_id="TSK-abc123",
            deliverable="PRD.md",
            executor="app_factory",
            status="pending",
            dry_run=True,
        )
        assert DispatchEntry.from_dict(entry.to_dict()) == entry


# ── DispatchPlan tests ─────────────────────────────────────────────────

class TestDispatchPlan:
    def test_to_dict(self, sample_manifest, dispatcher):
        plan = dispatcher.dispatch(sample_manifest, "MIS-001")
        d = plan.to_dict()
        assert d["mission_id"] == "MIS-001"
        assert isinstance(d["entries"], list)
        assert len(d["entries"]) == len(sample_manifest.deliverables)
        assert d["dry_run"] is True

    def test_from_dict(self):
        data = {
            "mission_id": "MIS-001",
            "entries": [
                {
                    "task_id": "TSK-01",
                    "deliverable": "test.md",
                    "executor": "publisher",
                    "status": "pending",
                    "dry_run": True,
                    "dispatched_at": None,
                    "finished_at": None,
                    "result_hint": "",
                }
            ],
            "generated_at": "2026-05-18T10:00:00Z",
            "dry_run": True,
            "total": 1,
            "summary": "test",
        }
        plan = DispatchPlan.from_dict(data)
        assert plan.mission_id == "MIS-001"
        assert len(plan.entries) == 1
        assert plan.entries[0].task_id == "TSK-01"

    def test_round_trip(self, sample_manifest, dispatcher):
        plan = dispatcher.dispatch(sample_manifest, "MIS-RT")
        reloaded = DispatchPlan.from_dict(plan.to_dict())
        assert reloaded.mission_id == plan.mission_id
        assert reloaded.total == plan.total
        assert len(reloaded.entries) == len(plan.entries)


# ── TaskDispatcher routing tests ───────────────────────────────────────

class TestTaskDispatcherRouting:
    def test_marketing_routes_to_publisher(self, dispatcher):
        manifest = DeliverableManifest(
            mission_id=None, setor="marketing", tipo="campaign",
            deliverables=[DeliverableSpec("test.md", "desc", "md")],
        )
        plan = dispatcher.dispatch(manifest, "MIS-001")
        assert plan.entries[0].executor == "publisher"

    def test_sales_routes_to_sales(self, dispatcher):
        manifest = DeliverableManifest(
            mission_id=None, setor="sales", tipo="sales",
            deliverables=[DeliverableSpec("leads.csv", "desc", "csv")],
        )
        plan = dispatcher.dispatch(manifest, "MIS-002")
        assert plan.entries[0].executor == "sales"

    def test_app_factory_routes_to_app_factory(self, dispatcher):
        manifest = DeliverableManifest(
            mission_id=None, setor="app_factory", tipo="dev",
            deliverables=[DeliverableSpec("PRD.md", "desc", "md")],
        )
        plan = dispatcher.dispatch(manifest, "MIS-003")
        assert plan.entries[0].executor == "app_factory"

    def test_computer_ops_routes_to_computer_ops(self, dispatcher):
        manifest = DeliverableManifest(
            mission_id=None, setor="computer_ops", tipo="ops",
            deliverables=[DeliverableSpec("audit.md", "desc", "md")],
        )
        plan = dispatcher.dispatch(manifest, "MIS-004")
        assert plan.entries[0].executor == "computer_ops"

    def test_finance_routes_to_finance(self, dispatcher):
        manifest = DeliverableManifest(
            mission_id=None, setor="finance", tipo="finance",
            deliverables=[DeliverableSpec("pricing.csv", "desc", "csv")],
        )
        plan = dispatcher.dispatch(manifest, "MIS-005")
        assert plan.entries[0].executor == "finance"

    def test_unknown_sector_defaults_to_skill_runner(self, dispatcher):
        manifest = DeliverableManifest(
            mission_id=None, setor="unknown_sector", tipo="x",
            deliverables=[DeliverableSpec("out.md", "desc", "md")],
        )
        plan = dispatcher.dispatch(manifest, "MIS-006")
        assert plan.entries[0].executor == "skill_runner"

    def test_general_routes_to_skill_runner(self, dispatcher):
        manifest = DeliverableManifest(
            mission_id=None, setor="general", tipo="general",
            deliverables=[DeliverableSpec("brief.md", "desc", "md")],
        )
        plan = dispatcher.dispatch(manifest, "MIS-007")
        assert plan.entries[0].executor == "skill_runner"


# ── SECTOR_EXECUTOR map ────────────────────────────────────────────────

def test_sector_executor_map_coverage():
    for sector in ["marketing", "sales", "app_factory", "computer_ops", "finance", "general"]:
        assert sector in SECTOR_EXECUTOR, f"Missing sector: {sector}"
        assert SECTOR_EXECUTOR[sector] is not None


# ── dry-run vs live ────────────────────────────────────────────────────

class TestDryRun:
    def test_dry_run_entries_not_dispatched(self, sample_manifest):
        d = TaskDispatcher(dry_run=True)
        plan = d.dispatch(sample_manifest, "MIS-DRY")
        for entry in plan.entries:
            assert entry.dry_run is True
            assert entry.dispatched_at is None
            assert "[DRY-RUN]" in entry.result_hint

    def test_live_mode_entries_dispatched(self, sample_manifest):
        d = TaskDispatcher(dry_run=False)
        plan = d.dispatch(sample_manifest, "MIS-LIVE")
        for entry in plan.entries:
            assert entry.dry_run is False
            assert entry.dispatched_at is not None
            assert "[DRY-RUN]" not in entry.result_hint

    def test_dispatch_plan_reflects_mode(self, sample_manifest):
        dry_plan = TaskDispatcher(dry_run=True).dispatch(sample_manifest, "MIS-1")
        live_plan = TaskDispatcher(dry_run=False).dispatch(sample_manifest, "MIS-1")
        assert dry_plan.dry_run is True
        assert live_plan.dry_run is False


# ── log writing ────────────────────────────────────────────────────────

class TestLogWriting:
    def test_log_written_when_log_dir_provided(self, tmp_path, sample_manifest):
        log_dir = tmp_path / "08_logs"
        d = TaskDispatcher(dry_run=True, log_dir=log_dir)
        d.dispatch(sample_manifest, "MIS-LOG")
        log_file = log_dir / "task_dispatch_log.jsonl"
        assert log_file.exists()

        lines = log_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == len(sample_manifest.deliverables)
        for line in lines:
            data = json.loads(line)
            assert "task_id" in data
            assert "executor" in data

    def test_no_log_when_log_dir_is_none(self, sample_manifest):
        d = TaskDispatcher(dry_run=True, log_dir=None)
        plan = d.dispatch(sample_manifest, "MIS-NOLOG")
        assert plan.total == len(sample_manifest.deliverables)

    def test_log_appends_to_existing(self, tmp_path, sample_manifest):
        log_dir = tmp_path / "08_logs"
        d = TaskDispatcher(dry_run=True, log_dir=log_dir)
        d.dispatch(sample_manifest, "MIS-1")
        d.dispatch(sample_manifest, "MIS-2")
        log_file = log_dir / "task_dispatch_log.jsonl"
        lines = log_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2 * len(sample_manifest.deliverables)


# ── edge cases ─────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_manifest(self, dispatcher):
        manifest = DeliverableManifest(
            mission_id=None, setor="general", tipo="general",
            deliverables=[],
        )
        plan = dispatcher.dispatch(manifest, "MIS-EMPTY")
        assert plan.total == 0
        assert plan.entries == []

    def test_single_deliverable(self, dispatcher):
        manifest = DeliverableManifest(
            mission_id=None, setor="sales", tipo="sales",
            deliverables=[DeliverableSpec("one.csv", "only one", "csv")],
        )
        plan = dispatcher.dispatch(manifest, "MIS-ONE")
        assert plan.total == 1
        assert plan.entries[0].deliverable == "one.csv"

    def test_all_task_ids_are_unique(self, sample_manifest, dispatcher):
        plan = dispatcher.dispatch(sample_manifest, "MIS-UNIQ")
        ids = {e.task_id for e in plan.entries}
        assert len(ids) == len(plan.entries)

    def test_summary_includes_sector_and_executor(self, dispatcher):
        manifest = DeliverableManifest(
            mission_id=None, setor="finance", tipo="finance",
            deliverables=[DeliverableSpec("r.csv", "x", "csv")],
        )
        plan = dispatcher.dispatch(manifest, "MIS-SUM")
        assert "finance" in plan.summary.lower()
        assert "finance agent" in plan.summary.lower()
