"""LegoCog — Protocol formal para todos os Legos OMNIS.

Define a interface mínima que todo Lego deve implementar para participar
do pipeline de execução coordenada (Onda 8).

  run(spec: LegoCogSpec) -> LegoCogResult  — executa a tarefa principal
  health_check() -> bool                   — verifica se o lego está operacional
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class LegoCogSpec:
    """Spec genérica para LegoCog.run().

    Cada Lego converte para sua spec nativa; campos adicionais ficam em payload.
    """

    goal: str
    dry_run: bool = True
    run_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class LegoCogResult:
    """Resultado genérico de LegoCog.run()."""

    success: bool
    output: str = ""
    dry_run: bool = True
    error: str = ""
    artifacts: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LegoCog(Protocol):
    """Protocol formal para Legos OMNIS.

    Qualquer classe com run(spec) -> LegoCogResult e health_check() -> bool
    satisfaz este Protocol (duck typing via @runtime_checkable).
    """

    def run(self, spec: LegoCogSpec) -> LegoCogResult: ...
    def health_check(self) -> bool: ...
