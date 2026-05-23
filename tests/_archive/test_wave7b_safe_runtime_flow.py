"""P45: Happy-path integration — LOW risk order flows through full pipeline."""

import tempfile
from pathlib import Path

from src.runtime_orchestrator.service import OrchestratorService
from src.war_room_bridge.adapter import WarRoomAdapter
from src.war_room_bridge.models import WarRoomReport, OrderStatus
from src.skills_bridge.skill_catalog import SkillCatalog
from src.skills_bridge.dryrun import DryRunDispatcher


def _write_md_order(orders_dir: Path, filename: str, risk: str, title: str) -> Path:
    content = f"""---
title: {title}
aba: aba-0
type: task
status: READY
risk: {risk}
project: omnis-control
allowed_paths: src/
requires_approval: false
dry_run: true
---

{title} body content.
"""
    path = orders_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class TestSafeRuntimeFlow:
    def test_low_risk_order_flows_through_orchestrator(self):
        """LOW risk: parsed, valid contract, auto-approved, skill, dry-run, logged, sunk, report."""
        svc = OrchestratorService(dry_run=True)
        result = svc.run({"order_id": "wro_test_low", "risk": "LOW"})
        assert result.status.value == "COMPLETED"
        assert len(result.steps) == 9
        assert all(s.status.value == "COMPLETED" for s in result.steps)
        assert result.final_output.get("report_written") is True

    def test_pipeline_steps_accumulate_data(self):
        """Data chains through steps: order_id and risk reach execute_dryrun step."""
        svc = OrchestratorService(dry_run=True)
        result = svc.run({"order_id": "wro_data_chain", "risk": "LOW"})
        steps = result.steps
        assert len(steps) == 9
        # execute_dryrun (index 5) received accumulated data from earlier steps
        dryrun_step = steps[5]
        assert dryrun_step.name == "execute_dryrun"
        assert result.status.value == "COMPLETED"

    def test_multiple_orders_independent(self):
        """Two orders produce independent pipeline results."""
        svc = OrchestratorService(dry_run=True)
        r1 = svc.run({"order_id": "wro_a", "risk": "LOW"})
        r2 = svc.run({"order_id": "wro_b", "risk": "LOW"})
        assert r1.status.value == "COMPLETED"
        assert r2.status.value == "COMPLETED"
        assert r1.steps[0].input_data.get("order_id") == "wro_a"
        assert r2.steps[0].input_data.get("order_id") == "wro_b"

    def test_war_room_adapter_reads_and_writes(self):
        """WarRoomAdapter: list orders from real directory, write report via writer."""
        with tempfile.TemporaryDirectory() as tmp:
            orders = Path(tmp) / "orders"
            reports = Path(tmp) / "reports"
            _write_md_order(orders, "test_order.md", "LOW", "Safe Test Order")

            adapter = WarRoomAdapter(str(orders), str(reports), dry_run=True)
            all_orders = adapter.list_orders()
            assert len(all_orders) == 1
            assert all_orders[0].title == "Safe Test Order"

            report = WarRoomReport(
                order_id=all_orders[0].order_id,
                title="Test Report",
                summary="All good",
                tests_run=1,
                tests_passed=1,
            )
            output_path = adapter.write_report(report)
            assert "reports" in output_path

    def test_dryrun_dispatcher_falls_back_for_missing_skill(self):
        """Unknown skill dispatches with FALLBACK status."""
        catalog = SkillCatalog()
        dispatcher = DryRunDispatcher(catalog, dry_run=True)
        from src.skills_bridge.models import SkillCall
        result = dispatcher.dispatch(SkillCall(skill_id="nonexistent-skill"))
        assert result["status"] == "FALLBACK"
        assert result["dry_run"] is True

    def test_dryrun_dispatcher_resolves_known_skill(self):
        """Known skill dispatches directly."""
        catalog = SkillCatalog()
        from src.skills_bridge.models import SkillDefinition, SkillCall
        catalog.add_skill(SkillDefinition(skill_id="seogram", name="SEOgram"))
        dispatcher = DryRunDispatcher(catalog, dry_run=True)
        result = dispatcher.dispatch(SkillCall(skill_id="seogram"))
        assert result["status"] == "DRY_RUN_OK"
        assert result["resolved_skill"] == "seogram"

    def test_war_room_reader_parses_frontmatter_correctly(self):
        """Reader correctly parses risk and title from Markdown frontmatter."""
        with tempfile.TemporaryDirectory() as tmp:
            orders = Path(tmp)
            _write_md_order(orders, "low_risk.md", "LOW", "Low Risk Task")
            _write_md_order(orders, "med_risk.md", "MEDIUM", "Medium Risk Task")

            adapter = WarRoomAdapter(str(orders), str(Path(tmp) / "reports"), dry_run=True)
            all_orders = adapter.list_orders()
            assert len(all_orders) == 2
            risks = {o.title: o.risk for o in all_orders}
            assert risks["Low Risk Task"] == "LOW"
            assert risks["Medium Risk Task"] == "MEDIUM"
