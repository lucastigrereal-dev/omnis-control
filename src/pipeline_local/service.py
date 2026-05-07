"""Serviço do Pipeline Local Dry-Run.

Conecta Content Queue + Caption Approval + Creative Production + Publisher Local
em um fluxo rastreável offline-first. Sem chamadas externas.
"""
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import (
    PipelineRunResult, PipelineRunStatus, PipelineBlockReason,
)

logger = logging.getLogger("omnis.pipeline_local.service")

# Store path
PIPELINE_RUNS_PATH = os.path.expanduser("~/omnis-control/data/pipeline_runs.jsonl")


class PipelineLocalService:
    """Serviço principal: conecta módulos existentes em um pipeline rastreável."""

    def __init__(self):
        from src.content_queue import Queue as ContentQueue
        from src.caption_approval import DraftsManager
        from src.publisher.pipeline import PublishPipeline, JsonLStore
        from src.observability.tracer_local import get_tracer, record_metric

        self.queue = ContentQueue()
        self.caption_mgr = DraftsManager()
        self.tracer = get_tracer("pipeline_local")
        self.record_metric = record_metric
        self.publisher_pipeline = PublishPipeline()
        self.publisher_store = JsonLStore()
        Path(os.path.dirname(PIPELINE_RUNS_PATH)).mkdir(parents=True, exist_ok=True)

    # ── Pipeline principal ──────────────────────────────────────────────────

    def run_local_content_pipeline(self, queue_item_id: str) -> PipelineRunResult:
        """Executa pipeline dry-run completo para um queue item.

        Fluxo:
            Queue Item → Caption Aprovada → Creative Brief → Export Package
            → Publisher Local Draft → Publisher Dry-Run → Métrica/Trace → Relatório

        Args:
            queue_item_id: ID do item na Content Queue.

        Returns:
            PipelineRunResult com status, warnings, evidence_refs.
        """
        run_id = uuid.uuid4().hex[:12]
        started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        warnings_list = []
        evidence = []
        result = PipelineRunResult(
            run_id=run_id,
            queue_item_id=queue_item_id,
            started_at=started_at,
            status=PipelineRunStatus.SUCCESS,
        )

        with self.tracer.start_as_current_span("pipeline_local_run") as span:
            span.set_attribute("queue_item_id", queue_item_id)
            span.set_attribute("run_id", run_id)

            try:
                # ── Stage 1: Load Queue Item ────────────────────────────────
                queue_item = self.queue.get(queue_item_id)
                if queue_item:
                    queue_item_id = queue_item.queue_id  # normaliza ID truncado → completo
                if not queue_item:
                    result.status = PipelineRunStatus.BLOCKED
                    result.block_reason = PipelineBlockReason.QUEUE_ITEM_NOT_FOUND
                    result.warnings = ["Queue item não encontrado"]
                    self._save(result)
                    span.set_attribute("status", result.status)
                    return result

                span.set_attribute("account_handle", queue_item.account_handle)
                span.set_attribute("format", queue_item.format or "unknown")
                evidence.append(f"queue_item:{queue_item_id}")

                # ── Stage 2: Find Approved Caption ──────────────────────────
                caption_draft_id = self._find_approved_caption(queue_item_id)
                if caption_draft_id:
                    result.caption_draft_id = caption_draft_id
                    evidence.append(f"caption_draft:{caption_draft_id}")
                    span.set_attribute("caption_draft_id", caption_draft_id)
                else:
                    warnings_list.append("CAPTION_NOT_APPROVED")
                    span.set_attribute("caption_warning", "CAPTION_NOT_APPROVED")

                # ── Stage 3: Create/Reuse Creative Brief ─────────────────────
                brief_id = self._find_or_create_brief(
                    queue_id=queue_item_id,
                    account_handle=queue_item.account_handle,
                    fmt=queue_item.format or "unknown",
                    objective=queue_item.objective or "alcance",
                    caption_draft_id=caption_draft_id,
                )
                if brief_id:
                    result.creative_brief_id = brief_id
                    evidence.append(f"creative_brief:{brief_id}")
                    span.set_attribute("creative_brief_id", brief_id)
                else:
                    warnings_list.append("BRIEF_FAILED")

                # ── Stage 4: Generate Export Package ─────────────────────────
                if brief_id:
                    try:
                        export_result = self._generate_export(brief_id)
                        if export_result:
                            result.export_package_path = str(export_result.package_path)
                            evidence.append(f"export_package:{export_result.package_id}")
                            span.set_attribute("export_package_id", export_result.package_id)
                            for w in export_result.warnings:
                                warnings_list.append(f"EXPORT_WARN:{w}")
                    except Exception as e:
                        warnings_list.append(f"EXPORT_FAILED:{e}")
                        logger.warning("Export package failed for brief %s: %s", brief_id, e)

                # ── Stage 5: Publisher Local Dry-Run ─────────────────────────
                publisher_draft_id = self._create_publisher_dry_run(
                    queue_item_id=queue_item_id,
                    account_handle=queue_item.account_handle,
                    title=queue_item.notes or f"Pipeline run {run_id[:8]}",
                    fmt=queue_item.format or "post",
                )
                if publisher_draft_id:
                    result.publisher_draft_id = publisher_draft_id
                    evidence.append(f"publisher_draft:{publisher_draft_id}")
                    span.set_attribute("publisher_draft_id", publisher_draft_id)
                else:
                    warnings_list.append("PUBLISHER_ENTRY_FAILED")

                # ── Final: Determine status ──────────────────────────────────
                if not caption_draft_id:
                    result.status = PipelineRunStatus.BLOCKED
                    result.block_reason = PipelineBlockReason.CAPTION_NOT_APPROVED
                elif warnings_list:
                    result.status = PipelineRunStatus.SUCCESS_WITH_WARNINGS
                else:
                    result.status = PipelineRunStatus.SUCCESS

                result.warnings = warnings_list
                result.evidence_refs = evidence
                result.finished_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                span.set_attribute("status", result.status)
                span.set_attribute("warnings_count", len(warnings_list))
                span.set_attribute("evidence_count", len(evidence))

            except Exception as e:
                result.status = PipelineRunStatus.FAILED
                result.warnings = [f"UNHANDLED_ERROR:{e}"]
                result.finished_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                span.set_attribute("status", result.status)
                span.set_attribute("error", str(e))
                logger.exception("Pipeline local run %s failed: %s", run_id, e)

        # Registrar métrica
        duration = self._calc_duration_ms(started_at, result.finished_at)
        self.record_metric(
            "pipeline_local.run_duration_ms", duration,
            {"status": result.status, "queue_id": queue_item_id[:8]},
        )

        self._save(result)
        return result

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _find_approved_caption(self, queue_id: str) -> Optional[str]:
        """Busca um caption aprovado para este queue_id (com prefix matching)."""
        drafts = self.caption_mgr.list_all()
        for d in drafts:
            if d.queue_id == queue_id and d.status == "approved":
                return d.draft_id
        # Prefix match (IDs truncados)
        matches = [d for d in drafts
                   if d.queue_id.startswith(queue_id) and d.status == "approved"]
        if len(matches) == 1:
            return matches[0].draft_id
        return None

    def _find_or_create_brief(
        self, queue_id: str, account_handle: str,
        fmt: str, objective: str,
        caption_draft_id: Optional[str] = None,
    ) -> Optional[str]:
        """Reusa brief existente ou cria um novo."""
        from src.creative_production.briefs import list_briefs, create_brief

        existing = list_briefs()
        for b in existing:
            if b.get("queue_id") == queue_id:
                return b.get("creative_brief_id")

        visual = f"Formato: {fmt}. Seguir identidade visual do perfil @{account_handle}."
        brief = create_brief(
            queue_id=queue_id,
            account_handle=account_handle,
            format=fmt,
            objective=objective,
            visual_direction=visual,
            caption_draft_id=caption_draft_id,
            script="(Script gerado pelo pipeline dry-run)",
            shot_list="(Shot list a definir)",
            design_notes=f"Carrossel/Reel para @{account_handle}. Tom: autêntico, próximo.",
            editing_notes="Edição padrão do perfil.",
        )
        return brief.creative_brief_id if brief else None

    def _generate_export(self, brief_id: str):
        """Gera export package para um brief."""
        from src.creative_production.exporter import generate_export_package
        return generate_export_package(brief_id, include_html=False, include_mock_image=False)

    def _create_publisher_dry_run(
        self, queue_item_id: str, account_handle: str,
        title: str, fmt: str,
    ) -> Optional[str]:
        """Cria entrada no Publisher Local Dry-Run."""
        import uuid as _uuid

        content_id = _uuid.uuid4().hex[:12]
        self.publisher_store.insert("content_items", {
            "id": content_id,
            "title": title,
            "account_handle": account_handle,
            "status": "idea",
            "format": fmt,
            "idempotency_key": _uuid.uuid4().hex[:16],
            "source": f"pipeline_local:{queue_item_id}",
        })
        return content_id

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save(self, result: PipelineRunResult) -> None:
        with open(PIPELINE_RUNS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")

    def _list_runs(self, limit: int = 20) -> list:
        if not os.path.isfile(PIPELINE_RUNS_PATH):
            return []
        items = []
        with open(PIPELINE_RUNS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return items[-limit:]

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _calc_duration_ms(self, start_iso: str, end_iso: str) -> float:
        try:
            fmt = "%Y-%m-%dT%H:%M:%SZ"
            s = datetime.strptime(start_iso, fmt).replace(tzinfo=timezone.utc)
            e = datetime.strptime(end_iso, fmt).replace(tzinfo=timezone.utc)
            return (e - s).total_seconds() * 1000
        except (ValueError, TypeError):
            return 0.0

    def status(self) -> dict:
        """Resumo de execuções do pipeline local."""
        runs = self._list_runs(50)
        total = len(runs)
        by_status = {}
        for r in runs:
            st = r.get("status", "unknown")
            by_status[st] = by_status.get(st, 0) + 1

        recent = runs[-5:] if runs else []
        return {
            "total_runs": total,
            "by_status": by_status,
            "recent_runs": [
                {
                    "run_id": r.get("run_id", "?")[:8],
                    "queue_item_id": r.get("queue_item_id", "?")[:8],
                    "status": r.get("status", "?"),
                    "warnings": r.get("warnings", []),
                }
                for r in recent
            ],
        }
