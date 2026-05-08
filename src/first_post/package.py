"""First Post Package — empacota conteudo para revisao (sem publicar). P1.3a."""
from __future__ import annotations

from typing import Optional

from src.first_post.models import PostPackage


class PostPackager:
    """Empacota conteudo aprovado para revisao humana antes de publicar."""

    def package_draft(self, queue_id: str) -> Optional[PostPackage]:
        """Cria pacote de publicacao para um slot especifico."""
        try:
            from src.content_queue import Queue as CQQueue
            from src.caption_approval import DraftsManager
            from src.caption_approval.models import DraftStatus

            queue = CQQueue()
            dm = DraftsManager()

            item = queue.get(queue_id)
            if not item:
                return None

            draft = dm.get_by_queue_id(queue_id)
            if not draft:
                return PostPackage(
                    queue_id=queue_id,
                    account_handle=item.account_handle,
                    format=item.format,
                    warnings=["Sem draft associado a este slot"],
                    ready=False,
                )

            warnings: list[str] = []
            if draft.status != DraftStatus.APPROVED:
                warnings.append(f"Draft status={draft.status}, deveria ser approved")
            if not draft.caption_text or len(draft.caption_text.strip()) < 10:
                warnings.append("Legenda muito curta ou vazia")
            if not item.asset_id:
                warnings.append("Sem asset atribuido ao slot")
            if "[BOT]" in (draft.caption_text or ""):
                warnings.append("Contem placeholder [BOT]")

            return PostPackage(
                queue_id=queue_id,
                account_handle=item.account_handle,
                format=item.format,
                caption_text=draft.caption_text,
                cta=draft.cta,
                hashtags=draft.hashtags,
                asset_id=item.asset_id,
                asset_file=item.asset_id or "",
                warnings=warnings,
                ready=len(warnings) == 0,
            )
        except Exception:
            return None

    def package_next_ready(self) -> Optional[PostPackage]:
        """Empacota o primeiro item pronto encontrado na fila."""
        try:
            from src.content_queue import Queue as CQQueue
            queue = CQQueue()
            items = queue.list_all()
            ready = [i for i in items if i.status in ("approved", "scheduled", "caption_ready")]
            for item in ready:
                pkg = self.package_draft(item.queue_id)
                if pkg and pkg.ready:
                    return pkg
            return None
        except Exception:
            return None
