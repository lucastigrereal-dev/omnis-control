"""ContentQualityWorkflow — score de qualidade em lote de conteúdos → akasha.

Onda 23: envolve QualityScorer para avaliar N itens de conteúdo de uma vez.
Cada item: {id, type, content, metadata (opcional)}.
Retorna relatórios por item + distribuição de notas + event akasha.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.quality_gate.scorer import QualityScorer
from src.quality_gate.models import QualityReport
from src.akasha_event_sink.adapter import AkashaSinkAdapter, FileAkashaSink
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.content_quality")

_COST_LOCAL_PCT = 100
_VALID_TYPES = {"caption", "carrossel", "reel", "dm", "app"}


@dataclass
class ContentQualityResult:
    run_id: str
    success: bool
    items_total: int
    items_ready: int
    reports: list[QualityReport]
    akasha_event_id: str
    dry_run: bool
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None

    @property
    def items_not_ready(self) -> int:
        return self.items_total - self.items_ready

    @property
    def ready_rate(self) -> float:
        if self.items_total == 0:
            return 0.0
        return self.items_ready / self.items_total

    @property
    def average_score(self) -> float:
        if not self.reports:
            return 0.0
        return sum(r.overall_score for r in self.reports) / len(self.reports)

    @property
    def grade_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "N/A": 0}
        for r in self.reports:
            grade = r.grade if r.grade in dist else "N/A"
            dist[grade] += 1
        return dist

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "items_total": self.items_total,
            "items_ready": self.items_ready,
            "items_not_ready": self.items_not_ready,
            "ready_rate": self.ready_rate,
            "average_score": self.average_score,
            "grade_distribution": self.grade_distribution,
            "akasha_event_id": self.akasha_event_id,
            "cost_local_pct": self.cost_local_pct,
        }


class ContentQualityWorkflow:
    """Avalia qualidade de N conteúdos em lote, emite snapshot no akasha."""

    def __init__(
        self,
        akasha_sink: AkashaSinkAdapter | None = None,
        akasha_dir: str = "output/akasha/content_quality/",
    ) -> None:
        self._sink = akasha_sink or FileAkashaSink(target_dir=akasha_dir, dry_run=True)

    def run(
        self,
        items: list[dict],
        dry_run: bool = True,
    ) -> ContentQualityResult:
        """Score cada item e persiste evento akasha.

        Args:
            items: lista de dicts com keys: id (str), type (str), content (str),
                   metadata (dict, opcional).
            dry_run: se True, marca resultado como simulação.

        Returns:
            ContentQualityResult com relatórios e resumo de distribuição.
        """
        ctx = RunContext.new(budget_usd=0.0)

        if not items:
            _logger.warning("content_quality[%s]: empty items list", ctx.run_id)
            return ContentQualityResult(
                run_id=ctx.run_id,
                success=False,
                items_total=0,
                items_ready=0,
                reports=[],
                akasha_event_id="",
                dry_run=dry_run,
                error="empty_items",
            )

        scorer = QualityScorer()
        reports: list[QualityReport] = []

        for item in items:
            output_id = item.get("id", "")
            output_type = item.get("type", "caption")
            if output_type not in _VALID_TYPES:
                output_type = "caption"
            content = item.get("content", "")
            metadata = item.get("metadata") or {}

            report = scorer.score(
                output_id=output_id,
                output_type=output_type,
                content=content,
                metadata=metadata,
            )
            reports.append(report)
            _logger.debug(
                "content_quality[%s]: %s → grade=%s score=%.1f",
                ctx.run_id, output_id, report.grade, report.overall_score,
            )

        items_ready = sum(1 for r in reports if r.ready_for_use)
        avg_score = sum(r.overall_score for r in reports) / len(reports)
        grade_dist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for r in reports:
            if r.grade in grade_dist:
                grade_dist[r.grade] += 1

        event = SinkEvent(
            event_type="content_quality_scored",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "items_total": len(items),
                "items_ready": items_ready,
                "average_score": round(avg_score, 2),
                "grade_distribution": grade_dist,
                "dry_run": dry_run,
            },
        )
        ok = self._sink.write_event(event)

        _logger.info(
            "content_quality[%s]: %d items scored — %d ready, avg=%.1f, akasha=%s",
            ctx.run_id, len(items), items_ready, avg_score, ok,
        )

        return ContentQualityResult(
            run_id=ctx.run_id,
            success=True,
            items_total=len(items),
            items_ready=items_ready,
            reports=reports,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
        )
