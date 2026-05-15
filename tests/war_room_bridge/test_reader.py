import json
import pytest
from pathlib import Path

from src.war_room_bridge.reader import WarRoomReader
from src.war_room_bridge.models import WarRoomOrder, OrderStatus
from src.war_room_bridge.errors import OrderNotFoundError


class TestWarRoomReader:
    def test_list_orders_empty_dir(self, tmp_path):
        reader = WarRoomReader(str(tmp_path))
        assert reader.list_orders() == []

    def test_list_orders_nonexistent_dir(self, tmp_path):
        reader = WarRoomReader(str(tmp_path / "nonexistent"))
        assert reader.list_orders() == []

    def test_list_orders_markdown(self, tmp_path):
        order_md = """---
title: Test Order
aba: aba-3
type: feature
status: READY
risk: LOW
project: omnis
allowed_paths: src/war_room_bridge/
forbidden_paths: src/health/
description: A test order
---
This is the body content.
"""
        (tmp_path / "test-order.md").write_text(order_md, encoding="utf-8")

        reader = WarRoomReader(str(tmp_path))
        orders = reader.list_orders()
        assert len(orders) == 1
        assert orders[0].title == "Test Order"
        assert orders[0].aba == "aba-3"
        assert orders[0].status == OrderStatus.READY
        assert orders[0].risk == "LOW"
        assert orders[0].body == "This is the body content."
        assert "src/war_room_bridge/" in orders[0].allowed_paths
        assert "src/health/" in orders[0].forbidden_paths

    def test_list_orders_json(self, tmp_path):
        order_data = {
            "order_id": "wro_json1",
            "title": "JSON Order",
            "aba": "aba-3",
            "type": "feature",
            "status": "READY",
            "risk": "MEDIUM",
            "project": "omnis",
            "description": "A JSON order",
            "body": "Body here",
        }
        (tmp_path / "order.json").write_text(json.dumps(order_data), encoding="utf-8")

        reader = WarRoomReader(str(tmp_path))
        orders = reader.list_orders()
        assert len(orders) == 1
        assert orders[0].title == "JSON Order"
        assert orders[0].risk == "MEDIUM"
        assert orders[0].body == "Body here"

    def test_read_order_by_id(self, tmp_path):
        order_md = """---
title: Find Me
status: READY
risk: LOW
---
Body.
"""
        (tmp_path / "find-me.md").write_text(order_md, encoding="utf-8")

        reader = WarRoomReader(str(tmp_path))
        orders = reader.list_orders()
        order_id = orders[0].order_id

        found = reader.read_order(order_id)
        assert found.title == "Find Me"

    def test_read_order_not_found(self, tmp_path):
        reader = WarRoomReader(str(tmp_path))
        with pytest.raises(OrderNotFoundError):
            reader.read_order("nonexistent_id")

    def test_skips_invalid_markdown(self, tmp_path):
        (tmp_path / "bad.md").write_text("no frontmatter here", encoding="utf-8")
        reader = WarRoomReader(str(tmp_path))
        orders = reader.list_orders()
        assert orders == []

    def test_dry_run_flag(self, tmp_path):
        reader = WarRoomReader(str(tmp_path), dry_run=True)
        assert reader.dry_run is True
        reader2 = WarRoomReader(str(tmp_path), dry_run=False)
        assert reader2.dry_run is False
