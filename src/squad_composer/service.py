"""Squad Composer service — thin wrapper for compose_squad."""
from __future__ import annotations

from src.squad_composer.composer import compose_squad
from src.squad_composer.models import SquadPlan


def compose(request: str) -> SquadPlan:
    """Compose a squad plan for the given request using default configs."""
    return compose_squad(request)
