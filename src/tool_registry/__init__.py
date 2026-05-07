"""Tool Registry — P0.8. Registro oficial de ferramentas/conectores do OMNIS."""
from __future__ import annotations

from typing import Optional

from src.tool_registry.models import ToolRecord
from src.tool_registry.registry import ToolRegistry


def get_tool_availability(tool_id: str) -> Optional[ToolRecord]:
    """Funcao publica leve: verifica se ferramenta existe e seu status.

    Uso tipico (pipeline, missions):
        tool = get_tool_availability("publisher_local_dry_run")
        if tool is None:
            print("warning: tool nao registrada")
        elif tool.status == "blocked":
            return blocked
    """
    registry = ToolRegistry()
    tool = registry.get_tool(tool_id)
    if tool is not None:
        from src.metrics import quick_record_metric
        quick_record_metric("tool_consultation", 1, tool_id=tool_id, status=tool.status)
    return tool

