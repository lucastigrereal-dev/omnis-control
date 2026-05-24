"""RunContext — contexto de execução propagado por todos os módulos OMNIS.

Carrega: run_id (rastreabilidade ponta a ponta) e budget_usd (teto de custo
por run). Propagado de BatchRunner → CaptionDraftAgent → LiteLLMAdapter.
"""
from __future__ import annotations

import math
import os
import uuid
from dataclasses import dataclass, field


_DEFAULT_BUDGET = float(os.getenv("OMNIS_BUDGET_USD", "0"))


class BudgetExceededError(Exception):
    """Lançado quando o custo acumulado excederia o budget configurado."""

    def __init__(self, accumulated: float, budget: float, estimated: float) -> None:
        self.accumulated = accumulated
        self.budget = budget
        self.estimated = estimated
        super().__init__(
            f"Budget excedido: acumulado={accumulated:.4f} + estimado={estimated:.4f}"
            f" > limite={budget:.4f} USD"
        )


@dataclass
class RunContext:
    """Contexto de execução de uma run OMNIS.

    Gerado uma vez no ponto de entrada (CLI, API, daemon) e propagado por
    todos os módulos. Garante run_id único no log e controle de custo.

    Uso:
        ctx = RunContext.new(budget_usd=0.05)
        llm = LiteLLMAdapter(run_context=ctx)
        ...
    """

    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    budget_usd: float = field(default_factory=lambda: _DEFAULT_BUDGET)
    cost_accumulated: float = field(default=0.0, init=False, repr=False)

    @classmethod
    def new(cls, budget_usd: float | None = None) -> "RunContext":
        """Cria RunContext com budget explícito ou do env OMNIS_BUDGET_USD."""
        b = budget_usd if budget_usd is not None else _DEFAULT_BUDGET
        return cls(budget_usd=b)

    def check_budget(self, estimated_cost_usd: float) -> None:
        """Verifica se o custo estimado cabe no budget restante.

        Raises:
            BudgetExceededError: se budget > 0 e custo excederia o teto.
        """
        if self.budget_usd <= 0:
            return
        if self.cost_accumulated + estimated_cost_usd > self.budget_usd:
            raise BudgetExceededError(
                self.cost_accumulated, self.budget_usd, estimated_cost_usd
            )

    def add_cost(self, cost_usd: float) -> None:
        """Adiciona custo real ao acumulador (chamado após cada resposta LLM)."""
        if cost_usd > 0:
            self.cost_accumulated += cost_usd

    def remaining_budget(self) -> float:
        """Retorna budget restante em USD. math.inf se ilimitado (budget_usd=0)."""
        if self.budget_usd <= 0:
            return math.inf
        return max(0.0, self.budget_usd - self.cost_accumulated)

    def log_prefix(self) -> str:
        """Prefixo padrão para logs: [run:abc123]."""
        return f"[run:{self.run_id}]"
