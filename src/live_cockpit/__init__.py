"""P24 Live Cockpit Supreme — Read-only visual control panel."""
from src.live_cockpit.models import CockpitSnapshot, CockpitModule
from src.live_cockpit.collector import CockpitCollector
from src.live_cockpit.renderer import CockpitRenderer
from src.live_cockpit.alerts import AlertAggregator
from src.live_cockpit.errors import (
    CockpitError,
    ModuleUnreachableError,
    CollectionError,
    RenderError,
    ExportError,
)

__all__ = [
    # Models
    "CockpitSnapshot",
    "CockpitModule",
    # Core
    "CockpitCollector",
    "CockpitRenderer",
    "AlertAggregator",
    # Errors
    "CockpitError",
    "ModuleUnreachableError",
    "CollectionError",
    "RenderError",
    "ExportError",
]
