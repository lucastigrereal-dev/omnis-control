class SinkError(Exception):
    """Base error for Akasha event sink operations."""
    pass


class SinkWriteError(SinkError):
    def __init__(self, path: str, reason: str):
        super().__init__(f"Failed to write event to {path}: {reason}")


class SerializationError(SinkError):
    def __init__(self, event_id: str, reason: str):
        super().__init__(f"Failed to serialize event {event_id}: {reason}")
