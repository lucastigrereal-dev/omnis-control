"""Approval Gate — Aprovação e rejeição de rascunhos.

Dependência unidirecional: caption_approval → content_queue.
Nunca importar content_queue aqui (feito via injeção no CLI).
"""

from typing import Optional

from .models import (
    CaptionDraft, DraftStatus, ApprovalAction,
    BLOCKED_PLACEHOLDERS, _now_iso,
)
from .drafts import DraftsManager


class PreApprovalResult:
    """Resultado da validação pré-aprovação."""

    def __init__(self):
        self.blocks: list[str] = []
        self.warnings: list[str] = []
        self.passed: bool = True

    @property
    def blocked(self) -> bool:
        return len(self.blocks) > 0

    def to_dict(self) -> dict:
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

    def validate(self, caption_text: str, hashtags: Optional[list[str]] = None,
                 cta: str = "") -> PreApprovalResult:
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

    def approve(self, draft_id: str,
                queue_updater: Optional[callable] = None) -> tuple[Optional[CaptionDraft], Optional[str]]:
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

    def reject(self, draft_id: str, reason: str,
               queue_updater: Optional[callable] = None) -> tuple[Optional[CaptionDraft], Optional[str]]:
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
