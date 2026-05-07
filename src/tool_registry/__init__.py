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
    return registry.get_tool(tool_id)

