"""AppFactoryWorkflow — molde ponta a ponta: ideia → plano → artefato → akasha.

Wires existing OMNIS pieces without adding new algorithms:
  - RunContext (Onda 7)        → run_id único + teto de custo
  - AppFactoryPlanner          → gera PRD + estrutura + blueprint (determinístico)
  - AppIdea.new()              → normaliza idea_text em AppIdea
  - AkashaSinkAdapter          → persiste evento com run_id no payload

Pipeline do workflow:
  1. plan   → AppArtifact via AppFactoryPlanner (sempre dry_run=True no planner)
  2. gate   → se dry_run=False e approved=False → retorna error="approval_required"
  3. export → se dry_run=False e approved → salva artefato em output/app_factory/<run_id>/
  4. akasha → evento gravado com run_id + artifact_id + prd_chars

Safe defaults (RUNBOOK_EVOLUCAO_SEQUENCIAL.md):
  - dry_run=True  → só planeja, zero escrita em disco
  - approved=False → gate obriga revisão antes de qualquer escrita
  - deploy_mode="mock" → planner nunca grava em data/ no modo padrão
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.app_factory.models import AppIdea
from src.app_factory.planner import AppFactoryPlanner
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.app_factory")

# App Factory usa geração determinística — zero LLM, zero cloud
_COST_LOCAL_PCT = 100


@dataclass
class AppFactoryResult:
    """Resultado consolidado do workflow App Factory."""

    run_id: str
    success: bool
    idea_text: str = ""
    artifact_id: str = ""
    prd_markdown: str = ""
    project_structure: dict = field(default_factory=dict)
    tech_stack: dict = field(default_factory=dict)
    files_written: list[str] = field(default_factory=list)
    akasha_event_id: str = ""
    dry_run: bool = True
    approved: bool = False
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def prd_chars(self) -> int:
        return len(self.prd_markdown)

    @property
    def module_count(self) -> int:
        return int(self.artifacts.get("module_count", 0))

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "idea_text": self.idea_text,
            "artifact_id": self.artifact_id,
            "prd_chars": self.prd_chars,
            "module_count": self.module_count,
            "files_written": self.files_written,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "approved": self.approved,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
            "artifacts": self.artifacts,
        }


class AppFactoryWorkflow:
    """Workflow ponta a ponta: ideia → plano → artefato → akasha.

    Injeção de dependências para facilitar testes:
      planner       → AppFactoryPlanner (default: instância padrão dry_run)
      akasha_sink   → AkashaSinkAdapter (default: FileAkashaSink dry_run=True)
    """

    def __init__(
        self,
        planner: AppFactoryPlanner | None = None,
        akasha_sink: AkashaSinkAdapter | None = None,
        output_dir: str = "output/app_factory/",
        akasha_dir: str = "output/akasha/app_factory/",
        budget_usd: float = 0.0,
    ) -> None:
        self._planner = planner or AppFactoryPlanner()
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)
        self._output_dir = output_dir
        self._budget_usd = budget_usd

    def run(
        self,
        idea_text: str,
        dry_run: bool = True,
        approved: bool = False,
    ) -> AppFactoryResult:
        """Executa o pipeline para uma ideia de app.

        Args:
            idea_text: Descrição da ideia do app (título/descrição).
            dry_run:   True → plano apenas, sem escrita em disco.
            approved:  True → permite escrita em disco (só valido com dry_run=False).
        """
        ctx = RunContext.new(budget_usd=self._budget_usd)
        _logger.info(
            "%s AppFactoryWorkflow.run: idea='%s...', dry_run=%s, approved=%s",
            ctx.log_prefix(), idea_text[:40], dry_run, approved,
        )

        # Passo 1 — Planejar (sempre dry_run=True no planner — seguro)
        idea = AppIdea.new(
            title=idea_text[:200],
            description=idea_text,
        )
        try:
            artifact = self._planner.plan(idea, dry_run=True)
        except Exception as exc:
            _logger.warning("%s planner failed: %s", ctx.log_prefix(), exc)
            return AppFactoryResult(
                run_id=ctx.run_id,
                success=False,
                idea_text=idea_text,
                dry_run=dry_run,
                approved=approved,
                error=f"planner_error: {exc}",
            )

        _logger.info(
            "%s plan OK — artifact_id=%s, prd_chars=%d",
            ctx.log_prefix(), artifact.artifact_id, len(artifact.prd_markdown),
        )

        # Passo 2 — Approval gate
        if not dry_run and not approved:
            _logger.warning("%s approval gate blocked: approved=False", ctx.log_prefix())
            return AppFactoryResult(
                run_id=ctx.run_id,
                success=False,
                idea_text=idea_text,
                artifact_id=artifact.artifact_id,
                prd_markdown=artifact.prd_markdown,
                dry_run=dry_run,
                approved=approved,
                error="approval_required",
                artifacts={"plan_summary": artifact.prd_markdown[:300], "approval_required": True},
            )

        # Passo 3 — Exportar artefatos (somente se dry_run=False e approved=True)
        files_written: list[str] = []
        if not dry_run and approved:
            run_output = Path(self._output_dir) / ctx.run_id
            run_output.mkdir(parents=True, exist_ok=True)
            payloads = {
                "prd.md": artifact.prd_markdown,
                "project_structure.json": json.dumps(artifact.project_structure, indent=2, ensure_ascii=False),
                "tech_stack.json": json.dumps(artifact.tech_stack_summary, indent=2, ensure_ascii=False),
                "artifact_meta.json": json.dumps(artifact.to_dict(), indent=2, ensure_ascii=False),
            }
            for filename, content in payloads.items():
                target = run_output / filename
                target.write_text(content, encoding="utf-8")
                files_written.append(str(target))
            _logger.info("%s exported %d files to %s", ctx.log_prefix(), len(files_written), run_output)

        # Passo 4 — Gravar no akasha
        module_count = len(artifact.project_structure.get("modules", []))
        event = SinkEvent(
            event_type="app_factory_completed",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "idea_text": idea_text[:200],
                "artifact_id": artifact.artifact_id,
                "prd_chars": len(artifact.prd_markdown),
                "module_count": module_count,
                "tech_stack": artifact.tech_stack_summary,
                "files_written": files_written,
                "cost_local_pct": _COST_LOCAL_PCT,
                "dry_run": dry_run,
                "approved": approved,
            },
        )
        written = self._sink.write_event(event)
        _logger.info("%s akasha write: event_id=%s, ok=%s", ctx.log_prefix(), event.event_id, written)

        return AppFactoryResult(
            run_id=ctx.run_id,
            success=True,
            idea_text=idea_text,
            artifact_id=artifact.artifact_id,
            prd_markdown=artifact.prd_markdown,
            project_structure=artifact.project_structure,
            tech_stack=artifact.tech_stack_summary,
            files_written=files_written,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
            approved=approved,
            cost_local_pct=_COST_LOCAL_PCT,
            artifacts={
                **artifact.to_dict(),
                "run_id": ctx.run_id,
                "akasha_event_id": event.event_id,
                "module_count": module_count,
            },
        )
