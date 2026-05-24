"""OutreachSequenceWorkflow — molde: prospects → sequências de outreach → akasha.

Onda 18 — wires existing SDR pieces without adding new algorithms:
  - RunContext            → run_id único
  - build_outreach_sequence() → OutreachSequence deterministico (P9 SDR)
  - validate_sequence()       → warnings de validação
  - AkashaSinkAdapter    → persiste resultado com run_id

Pipeline:
  1. validate  → garante lista não-vazia
  2. sequence  → build_outreach_sequence() por prospect
  3. validate  → validate_sequence() para cada sequência
  4. akasha    → evento com run_id, counts, warnings
  5. retorna   → OutreachSequenceResult com sequências e relatório

Uso (zero LLM — geração determinística):
  wf = OutreachSequenceWorkflow()
  result = wf.run([prospect_a, prospect_b], dry_run=True)
  print(result.sequences_count)   # 2 sequências geradas
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.commercial_sdr.models import OutreachSequence, ProspectProfile
from src.commercial_sdr.service import build_outreach_sequence, validate_sequence
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.outreach_sequence")

_COST_LOCAL_PCT = 100


@dataclass
class SequenceReport:
    """Relatório de uma sequência gerada para um prospect."""
    profile_id: str
    company_name: str
    sequence_id: str
    steps_count: int
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "company_name": self.company_name,
            "sequence_id": self.sequence_id,
            "steps_count": self.steps_count,
            "warnings": self.warnings,
            "has_warnings": bool(self.warnings),
        }


@dataclass
class OutreachSequenceResult:
    """Resultado consolidado do workflow de sequências de outreach."""

    run_id: str
    success: bool
    total_prospects: int = 0
    sequences: list[OutreachSequence] = field(default_factory=list)
    reports: list[SequenceReport] = field(default_factory=list)
    akasha_event_id: str = ""
    dry_run: bool = True
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)

    @property
    def sequences_count(self) -> int:
        return len(self.sequences)

    @property
    def total_steps(self) -> int:
        return sum(len(s.steps) for s in self.sequences)

    @property
    def total_warnings(self) -> int:
        return sum(len(r.warnings) for r in self.reports)

    @property
    def sequences_with_warnings(self) -> list[OutreachSequence]:
        warn_ids = {r.sequence_id for r in self.reports if r.warnings}
        return [s for s in self.sequences if s.sequence_id in warn_ids]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "total_prospects": self.total_prospects,
            "sequences_count": self.sequences_count,
            "total_steps": self.total_steps,
            "total_warnings": self.total_warnings,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
            "reports": [r.to_dict() for r in self.reports],
        }


class OutreachSequenceWorkflow:
    """Workflow de outreach: lista de prospects → sequências SDR → akasha."""

    def __init__(
        self,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/outreach/",
        budget_usd: float = 0.0,
    ) -> None:
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)
        self._budget_usd = budget_usd

    def run(
        self,
        prospects: list[ProspectProfile],
        dry_run: bool = True,
    ) -> OutreachSequenceResult:
        """Gera sequências de outreach para uma lista de prospects.

        Args:
            prospects: Lista de ProspectProfile para gerar sequências.
            dry_run:   True → processa e retorna sem persistir arquivos.
        """
        ctx = RunContext.new(budget_usd=self._budget_usd)
        _logger.info(
            "%s OutreachSequenceWorkflow.run: %d prospects, dry_run=%s",
            ctx.log_prefix(), len(prospects), dry_run,
        )

        if not prospects:
            return OutreachSequenceResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="empty_prospect_list",
            )

        sequences: list[OutreachSequence] = []
        reports: list[SequenceReport] = []

        for p in prospects:
            try:
                seq = build_outreach_sequence(p)
                warnings = validate_sequence(seq)
                sequences.append(seq)
                reports.append(SequenceReport(
                    profile_id=p.profile_id,
                    company_name=p.company_name,
                    sequence_id=seq.sequence_id,
                    steps_count=len(seq.steps),
                    warnings=warnings,
                ))
            except Exception as exc:
                _logger.warning(
                    "%s sequence failed for %s: %s", ctx.log_prefix(), p.profile_id, exc
                )

        if not sequences:
            return OutreachSequenceResult(
                run_id=ctx.run_id, success=False, dry_run=dry_run,
                error="all_sequences_failed",
            )

        total_steps = sum(len(s.steps) for s in sequences)
        total_warnings = sum(len(r.warnings) for r in reports)

        _logger.info(
            "%s sequences: %d geradas, %d steps totais, %d warnings",
            ctx.log_prefix(), len(sequences), total_steps, total_warnings,
        )

        event = SinkEvent(
            event_type="outreach_sequences_generated",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "total_prospects": len(prospects),
                "sequences_count": len(sequences),
                "total_steps": total_steps,
                "total_warnings": total_warnings,
                "cost_local_pct": _COST_LOCAL_PCT,
                "dry_run": dry_run,
            },
        )
        written = self._sink.write_event(event)
        _logger.info(
            "%s akasha write: event_id=%s, ok=%s", ctx.log_prefix(), event.event_id, written
        )

        return OutreachSequenceResult(
            run_id=ctx.run_id,
            success=True,
            total_prospects=len(prospects),
            sequences=sequences,
            reports=reports,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
            cost_local_pct=_COST_LOCAL_PCT,
            artifacts={
                "run_id": ctx.run_id,
                "akasha_event_id": event.event_id,
                "sequences_count": len(sequences),
                "total_steps": total_steps,
            },
        )
