"""Queue — Lógica de fila de conteúdo para assets de vídeo.

Operações de alto nível:
  - next_inbox: próximo asset não triado
  - next_ready_to_schedule: próximo asset aprovado sem agendamento
  - schedule: agenda asset para publicação (valida data futura)
  - mark_published: marca como publicado
"""

from datetime import datetime, timezone

from .models import VideoAsset
from .registry import Registry
from .status import AssetStatus


class Queue:
    """Fila de conteúdo — operações de alto nível sobre o registro."""

    def __init__(self, registry: Registry | None = None):
        self.registry = registry or Registry()

    def next_inbox(self, account: str | None = None) -> VideoAsset | None:
        """Próximo asset em inbox (mais antigo primeiro)."""
        assets = self.registry.filter(status=AssetStatus.INBOX)
        if account:
            acct = account.strip().lstrip("@").lower()
            assets = [a for a in assets if a.account_target == acct]
        if not assets:
            return None
        assets.sort(key=lambda a: a.created_at)
        return assets[0]

    def next_ready_to_schedule(self, account: str | None = None) -> VideoAsset | None:
        """Próximo asset aprovado sem agendamento."""
        assets = self.registry.filter(status=AssetStatus.APPROVED)
        if account:
            acct = account.strip().lstrip("@").lower()
            assets = [a for a in assets if a.account_target == acct]
        if not assets:
            return None
        assets.sort(key=lambda a: a.created_at)
        return assets[0]

    def schedule(self, asset_id: str, scheduled_at_iso: str) -> VideoAsset | None:
        """Agenda um asset para publicação. Valida data futura."""
        try:
            scheduled_dt = datetime.fromisoformat(scheduled_at_iso)
            if scheduled_dt.tzinfo is None:
                scheduled_dt = scheduled_dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            raise ValueError(f"Data inválida: {scheduled_at_iso}")

        if scheduled_dt <= datetime.now(timezone.utc):
            raise ValueError(
                f"Data de agendamento deve ser futura: {scheduled_at_iso}"
            )

        return self.registry.update(
            asset_id,
            status=AssetStatus.SCHEDULED,
            scheduled_at=scheduled_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def mark_published(self, asset_id: str) -> VideoAsset | None:
        """Marca como publicado."""
        return self.registry.mark_published(asset_id)

    def inbox_count(self, account: str | None = None) -> int:
        """Quantos assets aguardando triagem."""
        return len(self.registry.filter(status=AssetStatus.INBOX, account=account))

    def upcoming(self, days: int = 7) -> list[VideoAsset]:
        """Assets agendados para os próximos N dias."""
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        cutoff = (now + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        assets = self.registry.filter(status=AssetStatus.SCHEDULED)
        result = []
        for a in assets:
            if a.scheduled_at and a.scheduled_at <= cutoff:
                result.append(a)
        result.sort(key=lambda a: a.scheduled_at or "")
        return result
