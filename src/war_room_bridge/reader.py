import os
import json
from pathlib import Path
from typing import Optional

from src.war_room_bridge.models import WarRoomOrder, OrderStatus
from src.war_room_bridge.errors import OrderNotFoundError


class WarRoomReader:
    def __init__(self, orders_dir: str, dry_run: bool = True):
        self.orders_dir = Path(orders_dir)
        self.dry_run = dry_run

    def list_orders(self) -> list[WarRoomOrder]:
        orders = []
        if not self.orders_dir.exists():
            return orders
        for entry in sorted(self.orders_dir.iterdir()):
            if entry.is_file() and entry.suffix in (".md", ".json"):
                order = self._parse_file(entry)
                if order:
                    orders.append(order)
        return orders

    def read_order(self, order_id: str) -> WarRoomOrder:
        orders = self.list_orders()
        for order in orders:
            if order.order_id == order_id:
                return order
        raise OrderNotFoundError(order_id)

    def _parse_file(self, filepath: Path) -> Optional[WarRoomOrder]:
        try:
            if filepath.suffix == ".json":
                return self._parse_json(filepath)
            return self._parse_markdown(filepath)
        except Exception:
            return None

    def _parse_json(self, filepath: Path) -> WarRoomOrder:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["source_file"] = str(filepath)
        return WarRoomOrder.from_dict(data)

    def _parse_markdown(self, filepath: Path) -> Optional[WarRoomOrder]:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return self._parse_frontmatter_md(content, str(filepath))

    def _parse_frontmatter_md(self, content: str, source_file: str) -> Optional[WarRoomOrder]:
        if not content.startswith("---"):
            return None
        end = content.find("---", 3)
        if end == -1:
            return None
        frontmatter = content[3:end].strip()
        body = content[end + 3:].strip()

        data = {}
        for line in frontmatter.split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                data[key] = value

        if "allowed_paths" in data:
            data["allowed_paths"] = [p.strip() for p in data["allowed_paths"].split(",") if p.strip()]
        else:
            data["allowed_paths"] = []

        if "forbidden_paths" in data:
            data["forbidden_paths"] = [p.strip() for p in data["forbidden_paths"].split(",") if p.strip()]
        else:
            data["forbidden_paths"] = []

        data["body"] = body
        data["source_file"] = source_file
        stem = Path(source_file).stem
        data.setdefault("order_id", f"wro_{stem}")
        data.setdefault("status", "DRAFT")
        data.setdefault("risk", "LOW")
        data.setdefault("requires_approval", False)
        data.setdefault("dry_run", True)

        return WarRoomOrder(**{
            k: v for k, v in data.items()
            if k in WarRoomOrder.__dataclass_fields__
        })
