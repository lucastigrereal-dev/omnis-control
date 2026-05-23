"""CodeExecutor — contrato para o Lego de geração e execução de código.

Este módulo define apenas o Protocol (contrato). A implementação real
vem de um Lego externo (ex: OpenHands) que implementa esta interface.

Uso previsto (Onda 3):
    from src.interfaces.code_executor import CodeExecutor, CodeSpec, CodeResult
    executor: CodeExecutor = OpenHandsLego(...)  # implementação do Lego
    result = executor.execute(CodeSpec(goal="criar script de relatório", language="python"))
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Any


@dataclass
class CodeSpec:
    """Especificação de uma tarefa de geração/execução de código."""
    goal: str
    language: str = "python"
    dry_run: bool = True
    context_files: list[str] = field(default_factory=list)
    output_dir: str = "output/"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeResult:
    """Resultado estruturado de uma tarefa de código."""
    success: bool
    output: str
    files_created: list[str]
    tests_passed: bool
    dry_run: bool
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)


class CodeExecutor(Protocol):
    """Contrato do executor de código. O Lego implementa este Protocol."""

    def execute(self, spec: CodeSpec) -> CodeResult:
        """Executa uma especificação de código e retorna resultado estruturado."""
        ...

    def health_check(self) -> bool:
        """Retorna True se o executor está pronto para receber tarefas."""
        ...
