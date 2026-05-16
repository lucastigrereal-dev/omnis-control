"""RuntimeBridge — ponte explicita entre ExecutionGraph e ExecutionQueue."""

from src.runtime_bridge.models import BridgeResult, STATUS_MAP, map_step_status
from src.runtime_bridge.bridge import RuntimeBridge
from src.runtime_bridge.errors import BridgeError, BridgeMappingError

__all__ = [
    "RuntimeBridge",
    "BridgeResult",
    "BridgeError",
    "BridgeMappingError",
    "STATUS_MAP",
    "map_step_status",
]
