class WarRoomError(Exception):
    """Base error for War Room bridge operations."""
    pass


class OrderNotFoundError(WarRoomError):
    def __init__(self, order_id: str):
        super().__init__(f"Order not found: {order_id}")


class ReportWriteError(WarRoomError):
    def __init__(self, path: str, reason: str):
        super().__init__(f"Failed to write report to {path}: {reason}")


class ForbiddenPathError(WarRoomError):
    def __init__(self, path: str):
        super().__init__(f"Path is forbidden for OMNIS: {path}")
