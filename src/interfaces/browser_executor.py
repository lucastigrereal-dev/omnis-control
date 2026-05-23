"""BrowserExecutor — contrato para o Lego de automação web.

Este módulo define apenas o Protocol (contrato). A implementação real
vem de um Lego externo (ex: browser-use) que implementa esta interface.

Uso previsto (Onda 2):
    from src.interfaces.browser_executor import BrowserExecutor, BrowserTask, BrowserResult
    executor: BrowserExecutor = BrowserUseLego(...)  # implementação do Lego
    result = executor.execute(BrowserTask(url="...", goal="extrair preço"))
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Any


@dataclass
class BrowserTask:
    """Tarefa de automação web a ser executada pelo Lego."""
    url: str
    goal: str
    dry_run: bool = True
    timeout_seconds: int = 30
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrowserResult:
    """Resultado estruturado de uma tarefa web."""
    success: bool
    output: str
    url_visited: str
    dry_run: bool
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)


class BrowserExecutor(Protocol):
    """Contrato do executor web. O Lego implementa este Protocol."""

    def execute(self, task: BrowserTask) -> BrowserResult:
        """Executa uma tarefa web e retorna resultado estruturado."""
        ...

    def health_check(self) -> bool:
        """Retorna True se o executor está pronto para receber tarefas."""
        ...
