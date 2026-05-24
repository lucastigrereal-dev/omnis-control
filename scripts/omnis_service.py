"""omnis_service.py — daemon de execução contínua do OMNIS.

Executa SchedulerService.run_due() em loop, sem depender de terminal aberto.
Cada ciclo gera um RunContext novo (run_id único nos logs).

Uso:
    python scripts/omnis_service.py [--interval 60] [--dry-run]

Variáveis de ambiente:
    OMNIS_SERVICE_INTERVAL  — segundos entre ciclos (default: 60)
    OMNIS_SERVICE_DRY_RUN   — "1" para dry_run (default: "1")
    OMNIS_BUDGET_USD        — teto por ciclo (default: 0 = ilimitado)
"""
from __future__ import annotations

import logging
import os
import signal
import sys
import time

# Garante que o projeto está no sys.path
_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.agentic.scheduler import SchedulerService
from src.utils.run_context import RunContext

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
_logger = logging.getLogger("omnis.service")

_INTERVAL = int(os.getenv("OMNIS_SERVICE_INTERVAL", "60"))
_DRY_RUN = os.getenv("OMNIS_SERVICE_DRY_RUN", "1") != "0"

_running = True


def _handle_signal(signum, _frame) -> None:
    global _running
    _logger.info("Signal %s received — graceful shutdown iniciado", signum)
    _running = False


def _run_cycle(ctx: RunContext) -> None:
    """Executa um ciclo do scheduler e loga resultado."""
    prefix = ctx.log_prefix()
    _logger.info("%s ciclo iniciado (dry_run=%s)", prefix, _DRY_RUN)
    try:
        svc = SchedulerService(dry_run=_DRY_RUN)
        reports = svc.run_due()
        _logger.info(
            "%s ciclo concluído: %d schedule(s) executado(s)",
            prefix,
            len(reports),
        )
        for report in reports:
            _logger.info(
                "%s batch=%s approved=%d failed=%d",
                prefix,
                report.batch_id,
                report.approved,
                report.failed,
            )
    except Exception as exc:
        _logger.error("%s ciclo falhou: %s", prefix, exc)


def main() -> None:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    _logger.info(
        "OMNIS service iniciado — interval=%ds dry_run=%s",
        _INTERVAL,
        _DRY_RUN,
    )

    while _running:
        ctx = RunContext.new()
        _run_cycle(ctx)
        # Dorme em fatias de 1s para responder ao sinal de parada sem delay
        elapsed = 0
        while _running and elapsed < _INTERVAL:
            time.sleep(1)
            elapsed += 1

    _logger.info("OMNIS service encerrado com segurança")


if __name__ == "__main__":
    main()
