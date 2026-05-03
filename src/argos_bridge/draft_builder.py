"""ArgosDraft builder — cria drafts a partir de queue + caption aprovado.

Regras:
- Só cria se queue_id existir na fila
- Só cria se caption_draft_id existir e estiver approved
- Só cria se queue item estiver caption_ready
- Cria sem asset com warning NO_ASSET_ATTACHED (não bloqueia)
"""

import os
import uuid
from typing import Optional

from .models import ArgosDraft, ArgosStatus, WarnCode


DRAFTS_PATH = os.path.expanduser("~/omnis-control/data/argos_drafts.jsonl")


def _load_drafts() -> list[ArgosDraft]:
    if not os.path.isfile(DRAFTS_PATH):
        return []
    drafts = []
    with open(DRAFTS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                import json
                drafts.append(ArgosDraft.from_dict(json.loads(line)))
    return drafts


def _save_drafts(drafts: list[ArgosDraft]) -> None:
    import json
    os.makedirs(os.path.dirname(DRAFTS_PATH), exist_ok=True)
    with open(DRAFTS_PATH, "w", encoding="utf-8") as f:
        for d in drafts:
            f.write(json.dumps(d.to_dict(), ensure_ascii=False) + "\n")


class DraftBuilder:
    """Valida fontes e cria ArgosDrafts."""

    def __init__(self, queue_provider, caption_provider):
        """queue_provider: callable(queue_id) -> QueueItem | None
        caption_provider: callable(draft_id) -> CaptionDraft | None
        account_exists: callable(handle) -> bool
        """
        self._get_queue = queue_provider
        self._get_caption = caption_provider

    def create(self, queue_id: str) -> tuple[Optional[ArgosDraft], list[str]]:
        """Cria um ArgosDraft a partir de um queue_id.

        Returns:
            (ArgosDraft | None, lista_de_erros)
        """
        errors: list[str] = []

        # 1. Validar queue item
        queue_item = self._get_queue(queue_id)
        if not queue_item:
            errors.append(f"Queue item '{queue_id[:8]}' não encontrado")
            return None, errors

        if queue_item.status != "caption_ready":
            errors.append(
                f"Queue item '{queue_id[:8]}' está {queue_item.status}. "
                f"Esperado caption_ready."
            )
            return None, errors

        # 2. Buscar caption draft aprovado para este queue_id
        # Precisamos de um caption_provider que encontra por queue_id
        caption = self._get_caption(queue_id)
        if not caption:
            errors.append(f"Nenhum caption aprovado encontrado para queue '{queue_id[:8]}'")
            return None, errors

        if caption.status != "approved":
            errors.append(
                f"Caption '{caption.draft_id[:8]}' está {caption.status}. "
                f"Esperado approved."
            )
            return None, errors

        # 3. Verificar warnings
        warnings: list[str] = []
        if not queue_item.asset_id:
            warnings.append(WarnCode.NO_ASSET_ATTACHED)

        # 4. Criar ArgosDraft
        draft_id = uuid.uuid4().hex[:12]
        draft = ArgosDraft(
            draft_id=draft_id,
            queue_id=queue_id,
            caption_draft_id=caption.draft_id,
            account_handle=queue_item.account_handle,
            platform="instagram",
            post_type=queue_item.format,
            caption_text=caption.caption_text,
            hashtags=caption.hashtags or [],
            cta=caption.cta or "",
            asset_id=queue_item.asset_id,
            scheduled_date=queue_item.date,
            scheduled_time=queue_item.time,
            status=ArgosStatus.LOCAL_DRAFT,
            warnings=warnings,
            notes=None,
        )

        # 5. Persistir
        drafts = _load_drafts()
        drafts.append(draft)
        _save_drafts(drafts)

        return draft, []


def get(queue_id: str) -> Optional[ArgosDraft]:
    """Busca um ArgosDraft por queue_id."""
    drafts = _load_drafts()
    for d in drafts:
        if d.queue_id == queue_id:
            return d
    return None


def get_by_id(draft_id: str) -> Optional[ArgosDraft]:
    """Busca um ArgosDraft por draft_id."""
    drafts = _load_drafts()
    for d in drafts:
        if d.draft_id == draft_id:
            return d
    return None


def list_all() -> list[ArgosDraft]:
    """Lista todos os ArgosDrafts."""
    return _load_drafts()


def stats() -> dict:
    """Estatísticas dos ArgosDrafts."""
    drafts = _load_drafts()
    by_status: dict[str, int] = {}
    by_account: dict[str, int] = {}
    warnings_count = 0
    for d in drafts:
        by_status[d.status] = by_status.get(d.status, 0) + 1
        by_account[d.account_handle] = by_account.get(d.account_handle, 0) + 1
        if d.warnings:
            warnings_count += 1
    return {
        "total": len(drafts),
        "by_status": by_status,
        "by_account": by_account,
        "with_warnings": warnings_count,
    }
