from src.war_room_bridge.adapter import WarRoomAdapter
from src.war_room_bridge.models import WarRoomReport


class TestWarRoomAdapter:
    def test_creates_with_dirs(self, tmp_path):
        orders = tmp_path / "orders"
        reports = tmp_path / "reports"
        orders.mkdir()
        reports.mkdir()

        adapter = WarRoomAdapter(str(orders), str(reports), dry_run=True)
        assert adapter.dry_run is True
        assert adapter.list_orders() == []

    def test_list_orders_delegates(self, tmp_path):
        orders = tmp_path / "orders"
        reports = tmp_path / "reports"
        orders.mkdir()
        reports.mkdir()

        (orders / "test.md").write_text("""---
title: Test
status: READY
---
Body.
""", encoding="utf-8")

        adapter = WarRoomAdapter(str(orders), str(reports))
        result = adapter.list_orders()
        assert len(result) == 1
        assert result[0].title == "Test"

    def test_read_order_delegates(self, tmp_path):
        orders = tmp_path / "orders"
        reports = tmp_path / "reports"
        orders.mkdir()
        reports.mkdir()

        (orders / "find.md").write_text("""---
title: Find This
status: READY
---
Body.
""", encoding="utf-8")

        adapter = WarRoomAdapter(str(orders), str(reports))
        all_orders = adapter.list_orders()
        found = adapter.read_order(all_orders[0].order_id)
        assert found.title == "Find This"

    def test_write_report_delegates(self, tmp_path):
        orders = tmp_path / "orders"
        reports = tmp_path / "reports"
        orders.mkdir()
        reports.mkdir()

        adapter = WarRoomAdapter(str(orders), str(reports), dry_run=False)
        report = WarRoomReport(
            order_id="wro_x",
            title="Adapter Write",
            status="COMPLETED",
            summary="via adapter",
        )
        path = adapter.write_report(report)
        assert path.endswith(".md")
        assert (reports / f"{report.report_id}.md").exists()

    def test_sync_returns_orders(self, tmp_path):
        orders = tmp_path / "orders"
        reports = tmp_path / "reports"
        orders.mkdir()
        reports.mkdir()

        (orders / "a.md").write_text("""---
title: A
status: READY
---
A body.
""", encoding="utf-8")
        (orders / "b.md").write_text("""---
title: B
status: WAITING
---
B body.
""", encoding="utf-8")

        adapter = WarRoomAdapter(str(orders), str(reports))
        synced = adapter.sync()
        assert len(synced) == 2
        titles = [o.title for o in synced]
        assert "A" in titles
        assert "B" in titles
