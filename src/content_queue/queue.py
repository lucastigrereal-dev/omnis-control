"""Queue — Daily Content Queue da OMNIS.

Camada de planejamento editorial local.
Não substitui o Publisher OS — é o "quadro branco operacional".
"""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import QueueItem, QueueStatus, _now_iso
from .accounts import AccountRegistry, _normalize_handle

QUEUE_PATH = os.path.expanduser("~/omnis-control/data/content_queue.jsonl")
VIDEO_ASSETS_PATH = os.path.expanduser("~/omnis-control/data/video_assets.jsonl")
MAX_DAYS_DEFAULT = 7
MAX_DAYS_WITHOUT_FORCE = 30
MAX_DAYS_ABSOLUTE = 90


class Queue:
    """Gerencia a fila diária de conteúdo."""

    def __init__(self, path: str = QUEUE_PATH):
        self.path = path
        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ Generate

    def generate(
        self,
        days: int = MAX_DAYS_DEFAULT,
        dry_run: bool = True,
        force: bool = False,
        account_filter: str | None = None,
    ) -> dict[str, object]:
        """
        Gera slots de fila para N dias à frente.

        Args:
            days: Quantos dias gerar.
            dry_run: Se True, não escreve — só reporta.
            force: Se True, permite > 30 dias.
            account_filter: Se definido, gera só para esta conta.
        """
        if days > MAX_DAYS_ABSOLUTE:
            raise ValueError(f"Máximo de {MAX_DAYS_ABSOLUTE} dias. Passou {days}.")
        if days > MAX_DAYS_WITHOUT_FORCE and not force:
            raise ValueError(
                f"{days} dias requer --force (máximo sem force: {MAX_DAYS_WITHOUT_FORCE})"
            )

        accounts_reg = AccountRegistry()
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        # Contas ativas
        if account_filter:
            acct = accounts_reg.get_by_handle(account_filter)
            if not acct:
                raise ValueError(f"Account '{account_filter}' não encontrada")
            if not acct.active:
                raise ValueError(f"Account '{account_filter}' está desativada")
            accounts = [acct]
        else:
            accounts = accounts_reg.list_active()
            if not accounts:
                raise ValueError(
                    "Nenhuma conta ativa cadastrada. Use 'omnis accounts add' primeiro."
                )

        # Slots existentes (para idempotência)
        existing_slots = set()
        if not dry_run:
            for item in self.list_all():
                key = f"{item.account_handle}|{item.date}|{item.time}"
                existing_slots.add(key)

        new_items = []
        skipped = 0

        for account in accounts:
            times = account.default_posting_times or ["08:50", "17:50", "20:50"]
            for day_offset in range(days):
                slot_date = (today + timedelta(days=day_offset + 1)).strftime("%Y-%m-%d")
                for slot_time in times:
                    key = f"{account.handle}|{slot_date}|{slot_time}"
                    if not dry_run and key in existing_slots:
                        skipped += 1
                        continue

                    item = QueueItem(
                        queue_id=uuid.uuid4().hex[:12],
                        account_handle=account.handle,
                        date=slot_date,
                        time=slot_time,
                        timezone="America/Sao_Paulo",
                        format="unknown",
                        status=QueueStatus.NEEDS_ASSET,
                        priority=account.priority,
                    )
                    new_items.append(item)

                    if not dry_run:
                        self._append(item)

        return {
            "generated": len(new_items),
            "skipped": skipped,
            "dry_run": dry_run,
            "days": days,
            "accounts": len(accounts),
            "account_filter": account_filter,
        }

    # ------------------------------------------------------------------ CRUD

    def list_all(self) -> list[QueueItem]:
        if not os.path.isfile(self.path):
            return []
        items = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        items.append(QueueItem.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        return items

    def get(self, queue_id: str) -> QueueItem | None:
        """Busca por ID (com suporte a prefixo)."""
        items = self.list_all()
        # Exact match first
        for item in items:
            if item.queue_id == queue_id:
                return item
        # Prefix match (para IDs truncados na UI)
        matches = [i for i in items if i.queue_id.startswith(queue_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return None  # ambíguo — pedir ID completo
        return None

    def update(self, queue_id: str, **kwargs: object) -> QueueItem | None:
        items = self.list_all()
        found_item = self.get(queue_id)
        if not found_item:
            return None
        found_idx = None
        for i, item in enumerate(items):
            if item.queue_id == found_item.queue_id:
                found_idx = i
                break
        if found_idx is None:
            return None
        item = items[found_idx]
        for key, val in kwargs.items():
            if hasattr(item, key) and val is not None:
                setattr(item, key, val)
        item.updated_at = _now_iso()
        items[found_idx] = item
        self._rewrite(items)
        return item

    # ------------------------------------------------------------------ Assign

    def assign_asset(
        self,
        queue_id: str,
        asset_id: str,
        force: bool = False,
    ) -> tuple[QueueItem | None, str | None]:
        """Atribui um asset a um slot da fila."""
        # Validar asset
        if not os.path.isfile(VIDEO_ASSETS_PATH):
            raise ValueError(f"Video Asset Registry não encontrado em {VIDEO_ASSETS_PATH}")

        asset_found = False
        with open(VIDEO_ASSETS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("asset_id") == asset_id:
                            asset_found = True
                            break
                    except json.JSONDecodeError:
                        continue

        if not asset_found:
            raise ValueError(f"Asset '{asset_id}' não encontrado no Video Asset Registry")

        # Buscar slot
        item = self.get(queue_id)
        if not item:
            raise ValueError(f"Queue item '{queue_id}' não encontrado")

        if item.asset_id is not None and not force:
            raise ValueError(
                f"Slot já tem asset '{item.asset_id}'. Use --force para substituir."
            )

        # Se o slot tem formato definido, avisar divergência
        asset_format = None
        if asset_found:
            try:
                with open(VIDEO_ASSETS_PATH, encoding="utf-8") as f:
                    for line in f:
                        if asset_id in line:
                            try:
                                data = json.loads(line)
                                asset_format = data.get("format", "unknown")
                            except json.JSONDecodeError:
                                pass
                            break
            except (OSError, json.JSONDecodeError):
                pass

        # Atualizar
        kwargs = {"asset_id": asset_id}
        if item.status == QueueStatus.NEEDS_ASSET:
            kwargs["status"] = QueueStatus.NEEDS_CAPTION

        # Avisar divergência de formato (não bloqueia)
        warning = None
        if asset_format and item.format != "unknown" and asset_format != item.format:
            warning = f"Formato do asset ({asset_format}) difere do slot ({item.format})"

        result = self.update(queue_id, **kwargs)

        return result, warning

    # ------------------------------------------------------------------ Filters

    def filter(
        self,
        account: str | None = None,
        status: str | None = None,
        date: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[QueueItem]:
        """Filtra itens da fila."""
        items = self.list_all()

        if account:
            acct = _normalize_handle(account)
            items = [i for i in items if i.account_handle == acct]
        if status:
            items = [i for i in items if i.status == status]
        if date:
            items = [i for i in items if i.date == date]
        if date_from:
            items = [i for i in items if i.date >= date_from]
        if date_to:
            items = [i for i in items if i.date <= date_to]

        # Ordenar por data + hora
        items.sort(key=lambda i: (i.date, i.time))
        return items

    def today(self) -> list[QueueItem]:
        """Itens da fila para hoje."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.filter(date=today_str)

    # ------------------------------------------------------------------ Stats

    def stats(self) -> dict[str, object]:
        items = self.list_all()
        total = len(items)
        by_status = {}
        by_account = {}
        by_objective = {}
        for item in items:
            by_status[item.status] = by_status.get(item.status, 0) + 1
            by_account[item.account_handle] = by_account.get(item.account_handle, 0) + 1
            obj = item.objective or "unknown"
            by_objective[obj] = by_objective.get(obj, 0) + 1

        needs_asset = sum(1 for i in items if i.status == QueueStatus.NEEDS_ASSET)
        needs_caption = sum(1 for i in items if i.status == QueueStatus.NEEDS_CAPTION)
        approved = sum(1 for i in items if i.status == QueueStatus.APPROVED)
        scheduled = sum(1 for i in items if i.status == QueueStatus.SCHEDULED)

        return {
            "total": total,
            "by_status": by_status,
            "by_account": by_account,
            "by_objective": by_objective,
            "needs_asset": needs_asset,
            "needs_caption": needs_caption,
            "approved": approved,
            "scheduled": scheduled,
        }

    # ------------------------------------------------------------------ Export

    def export_csv(
        self,
        path: str,
        date_from: str | None = None,
        date_to: str | None = None,
        status_filter: str | None = None,
        account_filter: str | None = None,
    ) -> None:
        """Exporta fila como CSV com filtros."""
        items = self.filter(
            account=account_filter,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
        )
        # Se não passou filtro, limitar a próximos 30 dias
        if not date_from and not date_to and not status_filter and not account_filter:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            cutoff = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
            items = [i for i in items if i.date >= today and i.date <= cutoff]

        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            if not items:
                f.write("queue_id,account_handle,date,time,format,objective,status,asset_id\n")
                return
            writer = csv.DictWriter(f, fieldnames=items[0].to_dict().keys())
            writer.writeheader()
            for i in items:
                writer.writerow(i.to_dict())

    # ------------------------------------------------------------------ Internal

    def _append(self, item: QueueItem) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

    def _rewrite(self, items: list[QueueItem]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            for i in items:
                f.write(json.dumps(i.to_dict(), ensure_ascii=False) + "\n")
