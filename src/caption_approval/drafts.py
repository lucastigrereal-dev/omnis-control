"""Gerenciamento de rascunhos de legenda (CaptionDraft CRUD).

Armazenamento: data/caption_drafts.jsonl (JSONL)
"""

import json
import os
import uuid
from pathlib import Path

from .models import CaptionDraft, DraftStatus, ApprovalAction, ApprovalLogEntry, _now_iso

DRAFTS_PATH = os.path.expanduser("~/omnis-control/data/caption_drafts.jsonl")
APPROVAL_LOG_PATH = os.path.expanduser("~/omnis-control/data/approval_log.jsonl")
STALE_DAYS = 3


def _fingerprint(source_path: str, size_bytes: int, modified_at: str) -> str:
    """Fingerprint para dedup sem SHA256."""
    return f"{source_path}|{size_bytes}|{modified_at}"


class DraftsManager:
    """CRUD de rascunhos de legenda."""

    def __init__(self, drafts_path: str = DRAFTS_PATH, log_path: str = APPROVAL_LOG_PATH):
        self.drafts_path = drafts_path
        self.log_path = log_path
        Path(os.path.dirname(drafts_path)).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(log_path)).mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------- Create

    def create(
        self,
        queue_id: str,
        account_handle: str,
        caption_text: str = "",
        hashtags: list[str] | None = None,
        cta: str = "",
        objective: str = "alcance",
        format: str = "unknown",
        notes: str = "",
        asset_id: str | None = None,
    ) -> CaptionDraft:
        """Cria um novo rascunho."""
        draft = CaptionDraft(
            draft_id=uuid.uuid4().hex[:12],
            queue_id=queue_id,
            account_handle=account_handle,
            caption_text=caption_text,
            hashtags=hashtags or [],
            cta=cta,
            status=DraftStatus.DRAFT,
            version=1,
            objective=objective,
            format=format,
            notes=notes,
            asset_id=asset_id,
        )
        self._append(draft)
        self._log(draft.draft_id, draft.queue_id, ApprovalAction.CREATED)
        return draft

    # ---------------------------------------------------------------- Read

    def list_all(self) -> list[CaptionDraft]:
        if not os.path.isfile(self.drafts_path):
            return []
        items = []
        with open(self.drafts_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        items.append(CaptionDraft.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        return items

    def get(self, draft_id: str) -> CaptionDraft | None:
        items = self.list_all()
        for item in items:
            if item.draft_id == draft_id:
                return item
        # Prefix match
        matches = [i for i in items if i.draft_id.startswith(draft_id)]
        if len(matches) == 1:
            return matches[0]
        return None

    def get_by_queue_id(self, queue_id: str) -> CaptionDraft | None:
        """Retorna o draft mais recente para um queue_id (último criado no JSONL)."""
        items = [i for i in self.list_all() if i.queue_id == queue_id]
        if not items:
            return None
        return items[-1]  # último = mais recente (append-only JSONL)

    # -------------------------------------------------------------- Update

    def update(self, draft_id: str, **kwargs: object) -> CaptionDraft | None:
        """Atualiza campos de um rascunho.

        Regras:
        - Se status for rejected, update → revised, version++, rejection_reason=null
        - Se status for approved, update → revised, version++
        - Caso contrário, só atualiza os campos
        """
        items = self.list_all()
        found = self.get(draft_id)
        if not found:
            return None

        idx = next((i for i, item in enumerate(items) if item.draft_id == found.draft_id), None)
        if idx is None:
            return None

        draft = items[idx]

        # Se veio caption_text ou hashtags ou cta via kwargs, é alteração de conteúdo
        has_content_change = any(k in kwargs for k in ("caption_text", "hashtags", "cta"))

        if has_content_change:
            if draft.status == DraftStatus.REJECTED:
                draft.status = DraftStatus.REVISED
                draft.rejection_reason = None
                draft.version += 1
            elif draft.status == DraftStatus.APPROVED:
                draft.status = DraftStatus.REVISED
                draft.version += 1
            else:
                draft.version += 1

        for key, val in kwargs.items():
            if hasattr(draft, key) and val is not None:
                setattr(draft, key, val)

        draft.updated_at = _now_iso()
        items[idx] = draft
        self._rewrite(items)
        self._log(draft.draft_id, draft.queue_id, ApprovalAction.UPDATED)
        return draft

    # -------------------------------------------------------------- Submit

    def submit(self, draft_id: str) -> CaptionDraft | None:
        """Marca draft para revisão (draft → needs_review)."""
        items = self.list_all()
        found = self.get(draft_id)
        if not found:
            return None

        if found.status not in (DraftStatus.DRAFT, DraftStatus.REVISED):
            return None  # só pode submeter se está em draft ou revised

        idx = next((i for i, item in enumerate(items) if item.draft_id == found.draft_id), None)
        if idx is None:
            return None

        draft = items[idx]
        draft.status = DraftStatus.NEEDS_REVIEW
        draft.updated_at = _now_iso()
        items[idx] = draft
        self._rewrite(items)
        self._log(draft.draft_id, draft.queue_id, ApprovalAction.SUBMITTED)
        return draft

    # ----------------------------------------------------------- Stale check

    def check_stale(self) -> list[CaptionDraft]:
        """Retorna drafts em needs_review/revised parados há mais de STALE_DAYS."""
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_DAYS)
        stale = []
        for d in self.list_all():
            if d.status in (DraftStatus.NEEDS_REVIEW, DraftStatus.REVISED):
                try:
                    updated = datetime.strptime(d.updated_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    if updated < cutoff:
                        stale.append(d)
                except (ValueError, TypeError):
                    continue
        return stale

    # -------------------------------------------------------------- Export

    def export_csv(
        self,
        path: str,
        status_filter: str | None = None,
        account_filter: str | None = None,
    ) -> None:
        """Exporta rascunhos como CSV."""
        items = self.list_all()
        if status_filter:
            items = [i for i in items if i.status == status_filter]
        if account_filter:
            from src.content_queue.accounts import _normalize_handle
            acct = _normalize_handle(account_filter)
            items = [i for i in items if i.account_handle == acct]

        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            if not items:
                f.write("draft_id,queue_id,account_handle,status,version,objective,format,caption_text,hashtags,cta,notes,rejection_reason,asset_id,created_at,updated_at\n")
                return
            writer = csv.DictWriter(f, fieldnames=[
                "draft_id", "queue_id", "account_handle", "status", "version",
                "objective", "format", "caption_text", "hashtags", "cta",
                "notes", "rejection_reason", "asset_id", "created_at", "updated_at",
            ])
            writer.writeheader()
            for i in items:
                row = i.to_dict()
                # Escapar newlines no texto
                if row.get("caption_text"):
                    row["caption_text"] = row["caption_text"].replace("\n", "\\n")
                # Listas como string comma-separated
                if isinstance(row.get("hashtags"), list):
                    row["hashtags"] = ", ".join(row["hashtags"])
                if isinstance(row.get("rejection_reason"), type(None)):
                    row["rejection_reason"] = ""
                writer.writerow(row)

    # ----------------------------------------------------------- Approval Log

    def get_approval_log(
        self,
        limit: int = 50,
        draft_id: str | None = None,
        action: str | None = None,
    ) -> list[ApprovalLogEntry]:
        if not os.path.isfile(self.log_path):
            return []
        entries = []
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(ApprovalLogEntry.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        if draft_id:
            entries = [e for e in entries if e.draft_id.startswith(draft_id)]
        if action:
            entries = [e for e in entries if e.action == action]
        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]

    # -------------------------------------------------------------- Internal

    def _append(self, draft: CaptionDraft) -> None:
        with open(self.drafts_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(draft.to_dict(), ensure_ascii=False) + "\n")

    def _rewrite(self, items: list[CaptionDraft]) -> None:
        with open(self.drafts_path, "w", encoding="utf-8") as f:
            for i in items:
                f.write(json.dumps(i.to_dict(), ensure_ascii=False) + "\n")

    def _log(
        self,
        draft_id: str,
        queue_id: str,
        action: str,
        reason: str | None = None,
        previous_status: str | None = None,
        new_status: str | None = None,
    ) -> None:
        entry = ApprovalLogEntry(
            event_id=uuid.uuid4().hex[:12],
            draft_id=draft_id,
            queue_id=queue_id,
            action=action,
            actor="local_user",
            reason=reason,
            previous_status=previous_status,
            new_status=new_status,
        )
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
