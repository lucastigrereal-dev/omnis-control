"""AuroraPriority — Priorizador de tarefas por impacto para o OMNIS.

Classifica uma lista de pendências em ordem de prioridade usando 3 dimensões:
  1. Dinheiro    — gera caixa hoje? (peso 50)
  2. Desbloqueio — desbloqueia outra coisa? (peso 30)
  3. Risco       — risco de perder se não fizer? (peso 20)

Cada item recebe um score 0-100 e uma cor (verde/amarelo/vermelho).
Saída estável para KRATOS consumir via to_dict().

Princípios:
- Funciona 100% local (sem Ollama, sem API)
- Nunca falha: item inválido recebe score 0 com reason explicado
- Regras determinísticas + heurísticas simples de texto
- dry_run=True como default
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("omnis.aurora.priority")

# Pesos das dimensões (somam 100)
_PESO_DINHEIRO     = 50
_PESO_DESBLOQUEIO  = 30
_PESO_RISCO        = 20

# Keywords que sinalizam cada dimensão (case-insensitive)
_KW_DINHEIRO = [
    "publi", "collab", "parceria", "hotel", "restaurante", "pagamento",
    "proposta", "contrato", "invoice", "receita", "venda", "cliente",
    "patrocínio", "sponsor", "fee", "lead", "fechar", "negociar",
    "r$", "reais", "caixa", "faturamento", "cobrar",
]
_KW_DESBLOQUEIO = [
    "bloquei", "depende", "precisa", "aguarda", "esperando", "pendente",
    "prerequisito", "antes de", "para poder", "habilita", "libera",
    "desbloqueia", "prerequisite", "bloqueado", "travado",
]
_KW_RISCO = [
    "prazo", "deadline", "urgente", "vence", "expira", "hoje",
    "amanhã", "essa semana", "última chance", "perder", "cancelar",
    "risco", "critico", "emergência", "quebrar", "cair",
]

_THRESHOLD_GREEN  = 70
_THRESHOLD_YELLOW = 40


@dataclass
class PriorityItem:
    """Tarefa com score de prioridade calculado."""
    item_id: str
    texto: str
    score: int              # 0-100
    color: str              # "green" | "yellow" | "red"
    score_dinheiro: int     # 0-50
    score_desbloqueio: int  # 0-30
    score_risco: int        # 0-20
    reasoning: str          # explicação curta do score
    rank: int               # posição na lista ordenada (1 = mais prioritário)

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "texto": self.texto,
            "score": self.score,
            "color": self.color,
            "score_dinheiro": self.score_dinheiro,
            "score_desbloqueio": self.score_desbloqueio,
            "score_risco": self.score_risco,
            "reasoning": self.reasoning,
            "rank": self.rank,
        }

    def summary_line(self) -> str:
        _ICON = {"green": "[VERDE]", "yellow": "[AMARELO]", "red": "[VERMELHO]"}
        icon = _ICON.get(self.color, "")
        return (
            f"#{self.rank:02d} {icon} {self.score:3d}pts "
            f"[D:{self.score_dinheiro} B:{self.score_desbloqueio} R:{self.score_risco}] "
            f"{self.texto[:60]}"
        )


@dataclass
class PriorityReport:
    """Resultado da priorização de uma lista de tarefas."""
    report_id: str
    generated_at: str
    items: list[PriorityItem]   # ordenados por score DESC
    total_items: int
    high_priority: int          # score >= 70
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "items": [i.to_dict() for i in self.items],
            "total_items": self.total_items,
            "high_priority": self.high_priority,
            "warnings": self.warnings,
        }

    def summary(self) -> str:
        lines = [
            f"=== PRIORIDADE AURORA ({self.total_items} itens, {self.high_priority} alta prioridade) ===",
            f"gerado em: {self.generated_at[:19]}",
            "",
        ]
        for item in self.items:
            lines.append(f"  {item.summary_line()}")
            lines.append(f"       {item.reasoning}")
        for w in self.warnings:
            lines.append(f"  AVISO: {w}")
        return "\n".join(lines)

    def top(self, n: int = 3) -> list[PriorityItem]:
        """Retorna os N itens mais prioritários."""
        return self.items[:n]


class AuroraPriority:
    """Priorizador determinístico de tarefas por impacto.

    Uso:
        prio = AuroraPriority()
        report = prio.rank([
            "Fechar contrato hotel Ponta Negra (prazo hoje)",
            "Gravar reels para fila da semana",
            "Responder DMs pendentes",
        ])
        print(report.summary())
    """

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def rank(
        self,
        pendencias: list[str],
        context: Optional[dict] = None,
    ) -> PriorityReport:
        """Prioriza uma lista de tarefas por impacto.

        Args:
            pendencias: lista de strings descrevendo cada tarefa
            context:    dict opcional com contexto adicional
                        (ex: {"leads_quentes": 3, "deadline_hoje": True})

        Returns:
            PriorityReport com itens ordenados por score DESC.
        """
        import uuid
        report_id = str(uuid.uuid4())[:8]
        warnings: list[str] = []

        if not pendencias:
            warnings.append("Lista de pendências vazia")
            return PriorityReport(
                report_id=report_id,
                generated_at=datetime.now(timezone.utc).isoformat(),
                items=[],
                total_items=0,
                high_priority=0,
                warnings=warnings,
            )

        scored: list[PriorityItem] = []
        for idx, texto in enumerate(pendencias):
            if not isinstance(texto, str) or not texto.strip():
                warnings.append(f"Item {idx} inválido: '{texto}' — ignorado")
                continue
            item = self._score_item(
                item_id=f"item_{idx:03d}",
                texto=texto.strip(),
                context=context or {},
            )
            scored.append(item)

        # Ordena por score DESC, empate: preserva ordem original
        scored.sort(key=lambda x: -x.score)

        # Atribui rank
        for rank_idx, item in enumerate(scored, start=1):
            item.rank = rank_idx

        high = sum(1 for i in scored if i.score >= _THRESHOLD_GREEN)

        return PriorityReport(
            report_id=report_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            items=scored,
            total_items=len(scored),
            high_priority=high,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _score_item(self, item_id: str, texto: str, context: dict) -> PriorityItem:
        """Calcula score de 3 dimensões para um item."""
        texto_lower = texto.lower()

        # --- Dimensão 1: Dinheiro (0-50) ---
        d_score = self._score_dimensao(texto_lower, _KW_DINHEIRO, _PESO_DINHEIRO)

        # --- Dimensão 2: Desbloqueio (0-30) ---
        b_score = self._score_dimensao(texto_lower, _KW_DESBLOQUEIO, _PESO_DESBLOQUEIO)

        # --- Dimensão 3: Risco (0-20) ---
        r_score = self._score_dimensao(texto_lower, _KW_RISCO, _PESO_RISCO)

        total = d_score + b_score + r_score

        color = (
            "green"  if total >= _THRESHOLD_GREEN  else
            "yellow" if total >= _THRESHOLD_YELLOW else
            "red"
        )

        # Razões curtas
        reasons = []
        if d_score > 0:
            reasons.append(f"gera dinheiro ({d_score}pts)")
        if b_score > 0:
            reasons.append(f"desbloqueia algo ({b_score}pts)")
        if r_score > 0:
            reasons.append(f"tem risco/prazo ({r_score}pts)")
        if not reasons:
            reasons.append("sem sinal claro de impacto imediato")
        reasoning = " | ".join(reasons)

        return PriorityItem(
            item_id=item_id,
            texto=texto,
            score=total,
            color=color,
            score_dinheiro=d_score,
            score_desbloqueio=b_score,
            score_risco=r_score,
            reasoning=reasoning,
            rank=0,  # preenchido após ordenação
        )

    @staticmethod
    def _score_dimensao(texto_lower: str, keywords: list[str], peso_max: int) -> int:
        """Score proporcional ao número de keywords encontradas, cap em peso_max."""
        hits = sum(1 for kw in keywords if kw in texto_lower)
        if hits == 0:
            return 0
        # 1 hit = 50% do peso, 2+ hits = 100%
        frac = min(hits / 2, 1.0)
        return round(frac * peso_max)
