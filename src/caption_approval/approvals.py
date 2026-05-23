"""Approval Gate — Aprovação e rejeição de rascunhos.

Dependência unidirecional: caption_approval → content_queue.
Nunca importar content_queue aqui (feito via injeção no CLI).
"""

from pathlib import Path
from typing import Callable

from .models import (
    CaptionDraft, DraftStatus, ApprovalAction,
    BLOCKED_PLACEHOLDERS, _now_iso,
)
from .drafts import DraftsManager

SKIP_PATTERNS = ["[", "]", "TODO", "REVISAR", "PLACEHOLDER"]


class PreApprovalResult:
    """Resultado da validação pré-aprovação."""

    def __init__(self) -> None:
        self.blocks: list[str] = []
        self.warnings: list[str] = []
        self.passed: bool = True

    @property
    def blocked(self) -> bool:
        return len(self.blocks) > 0

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed and not self.blocked,
            "blocks": self.blocks,
            "warnings": self.warnings,
        }


class ApprovalGate:
    """Gate de aprovação com validação e logging."""

    def __init__(self, drafts_manager: DraftsManager):
        self.dm = drafts_manager

    # ----------------------------------------------------------- Validate

    def validate(
        self,
        caption_text: str,
        hashtags: list[str] | None = None,
        cta: str = "",
    ) -> PreApprovalResult:
        """Valida conteúdo antes de aprovar."""
        result = PreApprovalResult()

        text = (caption_text or "").strip()

        # Bloqueantes
        if not text:
            result.blocks.append("Texto da legenda vazio")
        elif len(text) < 10:
            result.blocks.append(f"Texto muito curto ({len(text)} caracteres, mínimo 10)")

        # Verificar placeholders bloqueantes
        for placeholder in BLOCKED_PLACEHOLDERS:
            if placeholder in text:
                result.blocks.append(f"Texto contém placeholder não resolvido: {placeholder}")

        # Warnings
        if hashtags is None or len(hashtags) < 3:
            result.warnings.append("Menos de 3 hashtags sugeridas")

        if not cta or len(cta.strip()) < 3:
            result.warnings.append("CTA não definido ou muito curto")

        if result.blocked:
            result.passed = False

        return result

    # ----------------------------------------------------------- Approve

    def approve(
        self,
        draft_id: str,
        queue_updater: Callable[[str, str], bool] | None = None,
    ) -> tuple[CaptionDraft | None, str | None]:
        """Aprova um draft.

        Args:
            draft_id: ID do draft.
            queue_updater: Função para atualizar queue status.
                          Recebe (queue_id, status) e retorna bool.

        Returns:
            (draft, warning) onde warning é None ou string de aviso.
        """
        draft = self.dm.get(draft_id)
        if not draft:
            raise ValueError(f"Draft '{draft_id}' não encontrado")

        if draft.status not in (DraftStatus.NEEDS_REVIEW, DraftStatus.REVISED, DraftStatus.DRAFT):
            raise ValueError(
                f"Draft '{draft_id[:8]}' está {draft.status}. "
                f"Só pode aprovar drafts em needs_review, revised ou draft."
            )

        # Pré-validação
        validation = self.validate(draft.caption_text, draft.hashtags, draft.cta)
        if validation.blocked:
            raise ValueError(
                f"Validação pré-aprovação falhou:\n" +
                "\n".join(f"  - {b}" for b in validation.blocks)
            )

        # Atualizar draft
        items = self.dm.list_all()
        idx = next((i for i, item in enumerate(items) if item.draft_id == draft.draft_id), None)
        if idx is None:
            raise ValueError(f"Draft '{draft_id}' não encontrado no storage")

        old_status = draft.status
        items[idx].status = DraftStatus.APPROVED
        items[idx].updated_at = _now_iso()
        self.dm._rewrite(items)

        # Log
        self.dm._log(draft.draft_id, draft.queue_id, ApprovalAction.APPROVED,
                     previous_status=old_status, new_status=DraftStatus.APPROVED)

        # Atualizar queue se possível
        warning = None
        if queue_updater:
            try:
                updated = queue_updater(draft.queue_id, "caption_ready")
                if not updated:
                    warning = f"Queue item '{draft.queue_id[:8]}' não encontrado para atualizar status"
            except ValueError as e:
                # Queue já scheduled/published → warning, não erro
                warning = str(e)

        return items[idx], warning

    # ----------------------------------------------------------- Reject

    def reject(
        self,
        draft_id: str,
        reason: str,
        queue_updater: Callable[[str, str], bool] | None = None,
    ) -> tuple[CaptionDraft | None, str | None]:
        """Rejeita um draft.

        Args:
            draft_id: ID do draft.
            reason: Motivo da rejeição (obrigatório).
            queue_updater: Função para atualizar queue status.

        Returns:
            (draft, warning)
        """
        if not reason or not reason.strip():
            raise ValueError("Motivo da rejeição (--reason) é obrigatório")

        draft = self.dm.get(draft_id)
        if not draft:
            raise ValueError(f"Draft '{draft_id}' não encontrado")

        if draft.status not in (DraftStatus.NEEDS_REVIEW, DraftStatus.REVISED, DraftStatus.DRAFT):
            raise ValueError(
                f"Draft '{draft_id[:8]}' está {draft.status}. "
                f"Só pode rejeitar drafts em needs_review, revised ou draft."
            )

        items = self.dm.list_all()
        idx = next((i for i, item in enumerate(items) if item.draft_id == draft.draft_id), None)
        if idx is None:
            raise ValueError(f"Draft '{draft_id}' não encontrado no storage")

        old_status = draft.status
        items[idx].status = DraftStatus.REJECTED
        items[idx].rejection_reason = reason.strip()
        items[idx].updated_at = _now_iso()
        self.dm._rewrite(items)

        # Log
        self.dm._log(draft.draft_id, draft.queue_id, ApprovalAction.REJECTED,
                     reason=reason.strip(),
                     previous_status=old_status, new_status=DraftStatus.REJECTED)

        # Atualizar queue se possível (rejected → needs_caption)
        warning = None
        if queue_updater:
            try:
                updated = queue_updater(draft.queue_id, "needs_caption")
                if not updated:
                    warning = f"Queue item '{draft.queue_id[:8]}' não encontrado para atualizar status"
            except ValueError as e:
                warning = str(e)

        return items[idx], warning

    # ----------------------------------------------------------- Batch Approve

    def batch_approve(
        self,
        limit: int = 5,
        queue_updater: Callable[[str, str], bool] | None = None,
    ) -> dict[str, object]:
        """Aprova ate N drafts validos de needs_review/revised."""
        candidates = [
            d for d in self.dm.list_all()
            if d.status in (DraftStatus.NEEDS_REVIEW, DraftStatus.REVISED)
        ]

        approved = 0
        skipped = 0
        skip_reasons = []

        for draft in candidates:
            if approved >= limit:
                break

            text = draft.caption_text or ""
            reason = None

            if not text.strip():
                reason = f"{draft.draft_id[:8]}: content vazio"
            elif not draft.account_handle:
                reason = f"{draft.draft_id[:8]}: sem account_handle"
            else:
                for pat in SKIP_PATTERNS:
                    if pat in text:
                        reason = f"{draft.draft_id[:8]}: placeholder '{pat}'"
                        break

            if reason:
                skip_reasons.append(reason)
                skipped += 1
                continue

            try:
                self.approve(draft.draft_id, queue_updater=queue_updater)
                approved += 1
            except ValueError as e:
                skip_reasons.append(f"{draft.draft_id[:8]}: {e}")
                skipped += 1

        if approved > 0:
            self._export_approved_latest()

        return {"approved": approved, "skipped": skipped, "skip_reasons": skip_reasons}

    # ------------------------------------------------------ Export approved

    def _export_approved_latest(self) -> None:
        """Exporta drafts aprovados para CSV em data/exports/."""
        out = Path(__file__).resolve().parent.parent.parent / "data" / "exports" / "approved_latest.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        self.dm.export_csv(str(out), status_filter=DraftStatus.APPROVED)
