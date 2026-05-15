from typing import Optional

from src.war_room_bridge.models import WarRoomOrder, WarRoomReport, OrderStatus
from src.war_room_bridge.reader import WarRoomReader
from src.war_room_bridge.writer import WarRoomWriter


class WarRoomAdapter:
    def __init__(self, orders_dir: str, reports_dir: str, dry_run: bool = True):
        self.reader = WarRoomReader(orders_dir, dry_run=dry_run)
        self.writer = WarRoomWriter(reports_dir, dry_run=dry_run)
        self.dry_run = dry_run

    def list_orders(self) -> list[WarRoomOrder]:
        return self.reader.list_orders()

    def read_order(self, order_id: str) -> WarRoomOrder:
        return self.reader.read_order(order_id)

    def write_report(self, report: WarRoomReport) -> str:
        return self.writer.write_report(report)

    def sync(self) -> list[WarRoomOrder]:
        return self.list_orders()
