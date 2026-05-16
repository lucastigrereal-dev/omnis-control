class BridgeError(Exception):
    """Base error for RuntimeBridge."""
    pass


class BridgeMappingError(BridgeError):
    """Unknown or unmappable step status."""

    def __init__(self, step_id: str, status: str):
        super().__init__(
            f"Cannot map step '{step_id}' with status '{status}': "
            f"no corresponding queue status defined"
        )
        self.step_id = step_id
        self.status = status
