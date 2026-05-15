"""P45: Full War Room → Report flow with filesystem-backed components."""

import tempfile
from pathlib import Path
import json

from src.war_room_bridge.models import WarRoomOrder, WarRoomReport, OrderStatus
from src.war_room_bridge.reader import WarRoomReader
from src.war_room_bridge.writer import WarRoomWriter
from src.war_room_bridge.adapter import WarRoomAdapter
from src.akasha_event_sink.adapter import FileAkashaSink, MockAkashaSink
from src.akasha_event_sink.models import SinkEvent, SinkStatus
from src.observability.audit import AuditTrail
from src.observability.rollback import RollbackEngine, RollbackStatus
from src.observability.run_log import RunLogger


LOW_RISK_MD = """---
title: Test Order
aba: aba-0
type: task
status: READY
risk: LOW
project: omnis-control
allowed_paths: src/
requires_approval: false
dry_run: true
---

Execute a safe task.
"""


class TestWarRoomToReport:
    def test_markdown_order_parsed_and_read(self):
        """Parse a markdown war room order and read it back by ID."""
        with tempfile.TemporaryDirectory() as tmp:
            orders_dir = Path(tmp) / "orders"
            orders_dir.mkdir()
            order_file = orders_dir / "test_order.md"
            order_file.write_text(LOW_RISK_MD, encoding="utf-8")

            reader = WarRoomReader(str(orders_dir), dry_run=True)
            orders = reader.list_orders()
            assert len(orders) == 1
            assert orders[0].title == "Test Order"
            assert orders[0].risk == "LOW"
            assert orders[0].status == OrderStatus.READY

            found = reader.read_order(orders[0].order_id)
            assert found.title == "Test Order"

    def test_json_order_parsed_and_read(self):
        """Parse a JSON war room order."""
        with tempfile.TemporaryDirectory() as tmp:
            orders_dir = Path(tmp) / "orders"
            orders_dir.mkdir()
            order_data = {
                "title": "JSON Order",
                "aba": "aba-0",
                "type": "task",
                "status": "READY",
                "risk": "MEDIUM",
                "project": "omnis-control",
                "allowed_paths": ["src/"],
                "forbidden_paths": [],
                "requires_approval": True,
                "dry_run": True,
                "description": "A JSON-based order",
                "body": "Execute this task.",
            }
            order_file = orders_dir / "json_order.json"
            order_file.write_text(json.dumps(order_data), encoding="utf-8")

            reader = WarRoomReader(str(orders_dir), dry_run=True)
            orders = reader.list_orders()
            assert len(orders) == 1
            assert orders[0].title == "JSON Order"
            assert orders[0].risk == "MEDIUM"

    def test_report_generation_and_write(self):
        """Generate a report and write it via WarRoomWriter (dry_run)."""
        with tempfile.TemporaryDirectory() as tmp:
            reports_dir = Path(tmp) / "reports"
            writer = WarRoomWriter(str(reports_dir), dry_run=True)
            report = WarRoomReport(
                order_id="wro_test",
                title="Execution Report",
                summary="All steps passed",
                tests_run=5,
                tests_passed=5,
                status="PASS",
            )
            path = writer.write_report(report)
            assert "reports" in path
            assert "wrr_" in path

    def test_adapter_full_sync_flow(self):
        """Adapter sync: list orders, write report — full cycle."""
        with tempfile.TemporaryDirectory() as tmp:
            orders = Path(tmp) / "orders"
            reports = Path(tmp) / "reports"
            orders.mkdir()

            (orders / "sync_test.md").write_text(LOW_RISK_MD, encoding="utf-8")

            adapter = WarRoomAdapter(str(orders), str(reports), dry_run=True)
            synced = adapter.sync()
            assert len(synced) == 1

            report = WarRoomReport(
                order_id=synced[0].order_id,
                title="Sync Report",
                summary="Sync completed",
                tests_run=1,
                tests_passed=1,
            )
            path = adapter.write_report(report)
            assert path.endswith(".md")

    def test_akasha_sink_writes_event_dry_run(self):
        """FileAkashaSink queues event in dry_run mode."""
        sink = FileAkashaSink("/tmp/akasha_test", dry_run=True)
        event = SinkEvent(event_type="pipeline_run", payload={"ok": True})
        ok = sink.write_event(event)
        assert ok is True
        assert event.status == SinkStatus.QUEUED

    def test_mock_akasha_sink_writes_and_queries(self):
        """MockAkashaSink stores events in memory."""
        sink = MockAkashaSink()
        event = SinkEvent(event_type="test_event", payload={"key": "val"})
        ok = sink.write_event(event)
        assert ok is True
        assert event.status == SinkStatus.WRITTEN

        results = sink.query_events("test_event")
        assert len(results) == 1
        assert results[0].payload == {"key": "val"}

    def test_observability_trio(self):
        """AuditTrail + RollbackEngine + RunLogger work together."""
        audit = AuditTrail()
        audit.record("pipeline_run", "PASS", source="p45_test")
        assert audit.entry_count == 1

        rollback = RollbackEngine()
        plan = rollback.plan("exc_test", "revert file change")
        assert plan.is_reversible is True
        assert plan.status == RollbackStatus.POSSIBLE

        logger = RunLogger()
        run = logger.start_run("p45_phase")
        assert run.status == "STARTED"
        logger.update(run.run_id, "COMPLETED", "All good")
        assert logger.get_run(run.run_id).status == "COMPLETED"
