"""BatchRunner — processa N itens da fila em sequência com relatório final.

Candidatos: QueueItems com status planned ou needs_caption.
Resultado por item: approved | needs_review | failed | skipped.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from src.agentic.caption_draft_agent import CaptionDraftAgent
from src.agentic.agent_models import AgentRunStatus
from src.content_queue.models import QueueItem, QueueStatus
from src.content_queue.queue import Queue


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── statuses processáveis ─────────────────────────────────────────────────────

PROCESSABLE_STATUSES = {QueueStatus.PLANNED, QueueStatus.NEEDS_CAPTION}


# ── models ────────────────────────────────────────────────────────────────────

class BatchVerdict:
    """Resultados normalizados para cada item processado no batch."""

    APPROVED = "approved"
    APPROVED_DRY = "approved_dry"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchItemResult:
    """Resultado individual de um QueueItem dentro de um batch."""

    queue_id: str
    account_handle: str
    objective: str
    run_id: str
    verdict: str
    draft_id: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, object]:
        """Serializa o resultado individual para resposta/log."""
        return asdict(self)


@dataclass
class BatchReport:
    """Relatorio agregado de uma execucao do BatchRunner."""

    batch_id: str
    dry_run: bool
    account_filter: str | None
    limit: int
    total_candidates: int
    total_processed: int
    results: list[BatchItemResult] = field(default_factory=list)
    started_at: str = field(default_factory=_now_iso)
    finished_at: str | None = None

    # ── computed ──────────────────────────────────────────────────────────────

    @property
    def approved(self) -> int:
        """Conta itens aprovados, incluindo dry-run aprovado."""
        return sum(1 for r in self.results
                   if r.verdict in (BatchVerdict.APPROVED, BatchVerdict.APPROVED_DRY))

    @property
    def needs_review(self) -> int:
        """Conta itens que precisam de revisao humana."""
        return sum(1 for r in self.results if r.verdict == BatchVerdict.NEEDS_REVIEW)

    @property
    def failed(self) -> int:
        """Conta itens que falharam durante o processamento."""
        return sum(1 for r in self.results if r.verdict == BatchVerdict.FAILED)

    @property
    def skipped(self) -> int:
        """Conta itens ignorados pelo agente."""
        return sum(1 for r in self.results if r.verdict == BatchVerdict.SKIPPED)

    def finish(self) -> None:
        """Marca o relatorio como finalizado."""
        self.finished_at = _now_iso()

    def to_dict(self) -> dict[str, object]:
        """Serializa o relatorio agregado para CLI/API."""
        return {
            "batch_id": self.batch_id,
            "dry_run": self.dry_run,
            "account_filter": self.account_filter,
            "limit": self.limit,
            "total_candidates": self.total_candidates,
            "total_processed": self.total_processed,
            "approved": self.approved,
            "needs_review": self.needs_review,
            "failed": self.failed,
            "skipped": self.skipped,
            "results": [r.to_dict() for r in self.results],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


# ── runner ────────────────────────────────────────────────────────────────────

class BatchRunner:
    """Processa múltiplos QueueItems em sequência."""

    def __init__(
        self,
        dry_run: bool = True,
        queue: Queue | None = None,
        agent: CaptionDraftAgent | None = None,
    ) -> None:
        self.dry_run = dry_run
        self._queue = queue or Queue()
        self._agent = agent or CaptionDraftAgent(dry_run=dry_run, queue=self._queue)

    def run(
        self,
        limit: int = 5,
        account_filter: str | None = None,
        status_filter: set[str] | None = None,
    ) -> BatchReport:
        """Executa o batch e retorna o relatório."""
        statuses = status_filter or PROCESSABLE_STATUSES
        candidates = self._select_candidates(account_filter, statuses, limit)

        report = BatchReport(
            batch_id=uuid.uuid4().hex[:10],
            dry_run=self.dry_run,
            account_filter=account_filter,
            limit=limit,
            total_candidates=len(candidates),
            total_processed=0,
        )

        for item in candidates:
            result = self._process_item(item)
            report.results.append(result)
            report.total_processed += 1

        report.finish()
        return report

    # ── internals ─────────────────────────────────────────────────────────────

    def _select_candidates(
        self,
        account_filter: str | None,
        statuses: set[str],
        limit: int,
    ) -> list[QueueItem]:
        items = self._queue.list_all()
        items = [i for i in items if i.status in statuses]
        if account_filter:
            handle = account_filter if account_filter.startswith("@") else f"@{account_filter}"
            items = [i for i in items if i.account_handle == handle]
        return items[:limit]

    def _process_item(self, item: QueueItem) -> BatchItemResult:
        try:
            run = self._agent.run(item.queue_id)
        except Exception as exc:
            return BatchItemResult(
                queue_id=item.queue_id,
                account_handle=item.account_handle,
                objective=item.objective or "",
                run_id="error",
                verdict=BatchVerdict.FAILED,
                error=str(exc),
            )

        if run.status == AgentRunStatus.FAILED:
            return BatchItemResult(
                queue_id=item.queue_id,
                account_handle=item.account_handle,
                objective=item.objective or "",
                run_id=run.run_id,
                verdict=BatchVerdict.FAILED,
                error=run.error or "",
            )

        verdict = run.result.get("gate_verdict", BatchVerdict.SKIPPED)
        draft_id = run.result.get("draft_id", "")

        return BatchItemResult(
            queue_id=item.queue_id,
            account_handle=item.account_handle,
            objective=item.objective or "",
            run_id=run.run_id,
            verdict=str(verdict),
            draft_id=str(draft_id),
        )
