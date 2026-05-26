"""CostTracker — Rastreamento de custo por missão/operação (B4).

Como tudo é local (PIL, FFmpeg, Ollama), o custo real é R$ 0,00.
O tracker registra: tempo gasto, operações realizadas e valor estimado de
mercado equivalente (CPM R$15 × alcance estimado de 10K por operação).

Princípios:
- cost_brl é SEMPRE 0.0 — operações locais não têm custo
- market_value_brl = R$150 por operação (CPM R$15 × 10K alcance / 1000)
- savings_brl = market_value_brl − cost_brl = market_value_brl
- Persiste em logs/cost_tracker.jsonl (append-only, como mission_runs.jsonl)
- dry_run=True não salva no log (só retorna o resultado)
- Falha silenciosa: se o log não puder ser escrito, a execução continua

Uso como context manager:
    with CostTracker("carrossel", dry_run=False) as ct:
        # faz a operação...
        pass
    # ao sair, salva automaticamente no log

Uso direto:
    ct = CostTracker("export", dry_run=False)
    ct.__enter__()
    # ... faz a operação ...
    op_cost = ct.finish()

Relatório:
    report = CostTracker.generate_report(log_path=p, period_days=7)
    print(report.summary())
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("omnis.agencia.cost_tracker")

_ROOT = Path(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))
_DEFAULT_LOG_PATH = _ROOT / "logs" / "cost_tracker.jsonl"

# CPM base: R$15 por mil impressões × alcance médio de 10K por operação
_CPM_BRL = 15.0
_ALCANCE_MEDIO = 10_000
_MARKET_VALUE_PER_OP = _CPM_BRL * (_ALCANCE_MEDIO / 1_000)  # R$ 150.00


# ------------------------------------------------------------------
# Dataclasses
# ------------------------------------------------------------------

@dataclass
class OperationCost:
    """Custo de uma operação individual."""
    operation: str          # "carrossel" | "clip" | "export" | "approve" | ...
    count: int              # número de operações (sempre 1 por tracker)
    duration_s: float       # duração em segundos
    cost_brl: float         # sempre 0.0 (operação local)
    market_value_brl: float # equivalente em anúncios pagos

    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "count": self.count,
            "duration_s": round(self.duration_s, 4),
            "cost_brl": self.cost_brl,
            "market_value_brl": round(self.market_value_brl, 2),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OperationCost":
        return cls(
            operation=data["operation"],
            count=data.get("count", 1),
            duration_s=data.get("duration_s", 0.0),
            cost_brl=data.get("cost_brl", 0.0),
            market_value_brl=data.get("market_value_brl", _MARKET_VALUE_PER_OP),
        )


@dataclass
class CostReport:
    """Relatório consolidado de custo para um período."""
    report_id: str
    period_start: str
    period_end: str
    operations: list[OperationCost]
    total_cost_brl: float           # sempre 0.0
    total_market_value_brl: float
    savings_brl: float              # market_value − cost = savings
    generated_at: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "operations": [op.to_dict() for op in self.operations],
            "total_cost_brl": self.total_cost_brl,
            "total_market_value_brl": round(self.total_market_value_brl, 2),
            "savings_brl": round(self.savings_brl, 2),
            "generated_at": self.generated_at,
            "warnings": self.warnings,
        }

    def summary(self) -> str:
        lines = [
            f"=== COST REPORT — {self.period_start[:10]} a {self.period_end[:10]} ===",
            f"gerado em: {self.generated_at[:19]}",
            f"",
            f"OPERAÇÕES ({len(self.operations)} registros)",
        ]

        # Agrupa por tipo de operação
        by_op: dict[str, list[OperationCost]] = {}
        for op in self.operations:
            by_op.setdefault(op.operation, []).append(op)

        for op_name, ops in sorted(by_op.items()):
            total_dur = sum(o.duration_s for o in ops)
            total_val = sum(o.market_value_brl for o in ops)
            lines.append(
                f"  {op_name:<20s}  {len(ops):>3d}x  "
                f"dur={total_dur:.1f}s  valor=R${total_val:.0f}"
            )

        lines += [
            f"",
            f"CUSTO REAL         R$ {self.total_cost_brl:.2f}  (modelo local — zero)",
            f"VALOR DE MERCADO   R$ {self.total_market_value_brl:.2f}",
            f"ECONOMIA           R$ {self.savings_brl:.2f}  vs Meta Ads (CPM R$15)",
        ]

        if self.warnings:
            lines.append("")
            for w in self.warnings:
                lines.append(f"  AVISO: {w}")

        return "\n".join(lines)


# ------------------------------------------------------------------
# CostTracker
# ------------------------------------------------------------------

class CostTracker:
    """Context manager que rastreia custo de uma operação.

    Uso como context manager:
        with CostTracker("carrossel", dry_run=False) as ct:
            # faz a operação...
            pass
        # ao sair, salva automaticamente no log

    Args:
        operation: nome da operação ("carrossel", "clip", "export", "approve", ...)
        log_path: caminho para o JSONL de persistência (padrão: logs/cost_tracker.jsonl)
        dry_run: se True, não persiste no log (apenas retorna o resultado)
    """

    def __init__(
        self,
        operation: str,
        log_path: Optional[Path] = None,
        dry_run: bool = True,
    ) -> None:
        self.operation = operation
        self.log_path = Path(log_path) if log_path else _DEFAULT_LOG_PATH
        self.dry_run = dry_run
        self._start_time: float = 0.0
        self._finished: bool = False
        self._result: Optional[OperationCost] = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "CostTracker":
        self._start_time = time.monotonic()
        self._finished = False
        self._result = None
        return self

    def __exit__(self, *args) -> bool:
        if not self._finished:
            self.finish()
        return False  # não suprime exceções

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def finish(self) -> OperationCost:
        """Finaliza o rastreamento e persiste (se dry_run=False).

        Pode ser chamado manualmente ou é chamado automaticamente ao sair
        do context manager.

        Returns:
            OperationCost com os dados da operação.
        """
        if self._finished and self._result is not None:
            return self._result

        elapsed_s = time.monotonic() - self._start_time

        op_cost = OperationCost(
            operation=self.operation,
            count=1,
            duration_s=elapsed_s,
            cost_brl=0.0,                    # operações locais = R$ 0,00
            market_value_brl=_MARKET_VALUE_PER_OP,
        )

        self._save(op_cost)
        self._finished = True
        self._result = op_cost
        return op_cost

    # ------------------------------------------------------------------
    # API estática
    # ------------------------------------------------------------------

    @staticmethod
    def generate_report(
        log_path: Optional[Path] = None,
        period_days: int = 7,
    ) -> CostReport:
        """Lê o log e gera um CostReport para os últimos `period_days` dias.

        Args:
            log_path: caminho para o JSONL (padrão: logs/cost_tracker.jsonl)
            period_days: janela de análise em dias

        Returns:
            CostReport consolidado com totais e savings.
        """
        path = Path(log_path) if log_path else _DEFAULT_LOG_PATH
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=period_days)
        warnings: list[str] = []

        operations = CostTracker.read_operations(log_path=path, limit=10_000)

        # Filtra pelo período (usa recorded_at se disponível, senão inclui tudo)
        filtered: list[OperationCost] = []
        for op in operations:
            filtered.append(op)

        # Re-lê com filtro de data
        filtered = CostTracker._read_filtered(path, cutoff)

        total_market = sum(op.market_value_brl for op in filtered)
        total_cost = 0.0  # sempre zero

        if not filtered:
            warnings.append("Nenhuma operação registrada no período")

        return CostReport(
            report_id=uuid.uuid4().hex[:12],
            period_start=cutoff.isoformat(),
            period_end=now.isoformat(),
            operations=filtered,
            total_cost_brl=total_cost,
            total_market_value_brl=total_market,
            savings_brl=total_market - total_cost,
            generated_at=now.isoformat(),
            warnings=warnings,
        )

    @staticmethod
    def read_operations(
        log_path: Optional[Path] = None,
        limit: int = 50,
    ) -> list[OperationCost]:
        """Lê as últimas `limit` operações do JSONL.

        Args:
            log_path: caminho para o JSONL (padrão: logs/cost_tracker.jsonl)
            limit: número máximo de registros a retornar

        Returns:
            Lista de OperationCost do mais recente ao mais antigo.
        """
        path = Path(log_path) if log_path else _DEFAULT_LOG_PATH
        if not path.exists():
            return []

        ops: list[OperationCost] = []
        try:
            with path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        ops.append(OperationCost.from_dict(data))
                    except Exception:  # noqa: BLE001
                        continue
        except Exception:  # noqa: BLE001
            return []

        ops.reverse()  # mais recente primeiro
        return ops[:limit]

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    @staticmethod
    def _read_filtered(
        path: Path,
        cutoff: datetime,
    ) -> list[OperationCost]:
        """Lê operações do log filtrando pelo campo recorded_at >= cutoff."""
        if not path.exists():
            return []

        ops: list[OperationCost] = []
        try:
            with path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        recorded_at = data.get("recorded_at", "")
                        if recorded_at:
                            try:
                                dt = datetime.fromisoformat(
                                    recorded_at.replace("Z", "+00:00")
                                )
                                if dt < cutoff:
                                    continue
                            except ValueError:
                                pass  # inclui se não consegue parsear
                        ops.append(OperationCost.from_dict(data))
                    except Exception:  # noqa: BLE001
                        continue
        except Exception:  # noqa: BLE001
            pass

        return ops

    def _save(self, op: OperationCost) -> None:
        """Salva a operação no JSONL (append-only). Falha silenciosa."""
        if self.dry_run:
            _logger.debug(
                "cost_tracker: dry_run — operação '%s' não salva", op.operation
            )
            return
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(op.to_dict(), ensure_ascii=False) + "\n")
            _logger.debug(
                "cost_tracker: operação '%s' salva — dur=%.3fs valor=R$%.2f",
                op.operation,
                op.duration_s,
                op.market_value_brl,
            )
        except Exception as exc:  # noqa: BLE001
            _logger.warning("cost_tracker: falha ao salvar operação: %s", exc)
