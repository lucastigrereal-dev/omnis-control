"""CodeRunWorkflow — molde ponta a ponta: código → executor sandbox → relatório → akasha.

Onda 12 — wires existing pieces without adding new algorithms:
  - RunContext (Onda 7)     → run_id único + teto de custo
  - CodeExecutorLego        → executa Python local em subprocess sandboxado
  - AkashaSinkAdapter       → persiste evento com run_id no payload
  - cost_local_pct = 100    → execução sempre local, zero cloud

Pipeline:
  1. execute → CodeExecutorLego.execute(CodeSpec) → CodeResult
  2. akasha  → evento gravado com run_id, stdout, tests_passed, files_created
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.interfaces.code_executor import CodeSpec, CodeResult
from src.legos.code_executor_lego import CodeExecutorLego
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.code_run")

# Execução sandbox sempre local — custo cloud zero
_COST_LOCAL_PCT = 100


@dataclass
class CodeRunResult:
    """Resultado consolidado do workflow de execução de código."""

    run_id: str
    success: bool
    goal: str = ""
    output: str = ""
    tests_passed: bool = False
    files_created: list[str] = field(default_factory=list)
    akasha_event_id: str = ""
    dry_run: bool = True
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def output_lines(self) -> int:
        return len(self.output.splitlines()) if self.output else 0

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "goal": self.goal,
            "output_lines": self.output_lines,
            "tests_passed": self.tests_passed,
            "files_created": self.files_created,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
            "artifacts": self.artifacts,
        }


class CodeRunWorkflow:
    """Workflow ponta a ponta: código → sandbox → relatório → akasha.

    Injeção de dependências para testes:
      lego          → CodeExecutorLego (default: instância padrão)
      akasha_sink   → AkashaSinkAdapter (default: FileAkashaSink dry_run=True)
    """

    def __init__(
        self,
        lego: CodeExecutorLego | None = None,
        akasha_sink: AkashaSinkAdapter | None = None,
        output_dir: str = "output/code/",
        akasha_dir: str = "output/akasha/code/",
        budget_usd: float = 0.0,
    ) -> None:
        self._lego = lego or CodeExecutorLego()
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)
        self._output_dir = output_dir
        self._budget_usd = budget_usd

    def run(
        self,
        goal: str,
        language: str = "python",
        context_files: list[str] | None = None,
        dry_run: bool = True,
    ) -> CodeRunResult:
        """Executa o pipeline de código para um objetivo.

        Args:
            goal:          Descrição do que executar/analisar.
            language:      Linguagem de programação (default: "python").
            context_files: Arquivos de contexto para o executor.
            dry_run:       True → gera plano/análise sem executar código real.
        """
        ctx = RunContext.new(budget_usd=self._budget_usd)
        _logger.info(
            "%s CodeRunWorkflow.run: goal='%s...', lang=%s, dry_run=%s",
            ctx.log_prefix(), goal[:40], language, dry_run,
        )

        spec = CodeSpec(
            goal=goal,
            language=language,
            dry_run=dry_run,
            context_files=list(context_files or []),
            output_dir=self._output_dir,
            extra={"run_id": ctx.run_id},
        )
        code_result = self._lego.execute(spec)

        if not code_result.success:
            _logger.warning("%s code execution failed: %s", ctx.log_prefix(), code_result.error)
            return CodeRunResult(
                run_id=ctx.run_id,
                success=False,
                goal=goal,
                dry_run=dry_run,
                error=code_result.error,
            )

        _logger.info(
            "%s execution OK — %d output lines, tests_passed=%s, files=%d",
            ctx.log_prefix(), len(code_result.output.splitlines()),
            code_result.tests_passed, len(code_result.files_created),
        )

        # Gravar no akasha
        event = SinkEvent(
            event_type="code_run_completed",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "goal": goal,
                "language": language,
                "output_preview": code_result.output[:500],
                "output_lines": len(code_result.output.splitlines()),
                "tests_passed": code_result.tests_passed,
                "files_created": code_result.files_created,
                "cost_local_pct": _COST_LOCAL_PCT,
                "dry_run": dry_run,
            },
        )
        written = self._sink.write_event(event)
        _logger.info("%s akasha write: event_id=%s, ok=%s", ctx.log_prefix(), event.event_id, written)

        return CodeRunResult(
            run_id=ctx.run_id,
            success=True,
            goal=goal,
            output=code_result.output,
            tests_passed=code_result.tests_passed,
            files_created=code_result.files_created,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
            cost_local_pct=_COST_LOCAL_PCT,
            artifacts={
                **code_result.artifacts,
                "run_id": ctx.run_id,
                "akasha_event_id": event.event_id,
                "output_lines": len(code_result.output.splitlines()),
            },
        )
