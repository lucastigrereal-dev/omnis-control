"""Exportador de ArgosDrafts para CSV e JSON."""

import csv
import json
import os

from .draft_builder import list_all
from .models import ArgosDraft


EXPORT_DIR = os.path.expanduser("~/omnis-control/data/exports/argos")


def _ensure_dir() -> None:
    os.makedirs(EXPORT_DIR, exist_ok=True)


def _csv_row(draft: ArgosDraft) -> dict[str, object]:
    """View aplainada para CSV."""
    return {
        "draft_id": draft.draft_id,
        "queue_id": draft.queue_id,
        "caption_draft_id": draft.caption_draft_id,
        "account_handle": draft.account_handle,
        "platform": draft.platform,
        "post_type": draft.post_type,
        "caption_text": draft.caption_text,
        "hashtags": ", ".join(draft.hashtags) if draft.hashtags else "",
        "cta": draft.cta,
        "asset_id": draft.asset_id or "",
        "media_path": draft.media_path or "",
        "scheduled_date": draft.scheduled_date or "",
        "scheduled_time": draft.scheduled_time or "",
        "status": draft.status,
        "warnings": "; ".join(draft.warnings) if draft.warnings else "",
        "notes": draft.notes or "",
        "created_at": draft.created_at,
        "updated_at": draft.updated_at,
    }


def export_csv(drafts: list[ArgosDraft], filename: str = "argos_drafts.csv",
               output_dir: str | None = None) -> str:
    """Exporta drafts para CSV com BOM (compatível com Excel PT-BR)."""
    _ensure_dir()
    path = os.path.join(output_dir or EXPORT_DIR, filename)
    rows = [_csv_row(d) for d in drafts]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        else:
            f.write("﻿")  # BOM only
    return path


def export_json(drafts: list[ArgosDraft], filename: str = "argos_drafts.json",
                output_dir: str | None = None, pretty: bool = True) -> str:
    """Exporta drafts para JSON."""
    _ensure_dir()
    path = os.path.join(output_dir or EXPORT_DIR, filename)
    data = [d.to_dict() for d in drafts]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2 if pretty else None)
    return path


def export_all(format: str = "csv") -> str:
    """Exporta todos os drafts no formato especificado."""
    drafts = list_all()
    if not drafts:
        return "Nenhum ArgosDraft para exportar"
    if format == "csv":
        path = export_csv(drafts)
    elif format == "json":
        path = export_json(drafts)
    else:
        return f"Formato não suportado: {format}"
    return f"Exportado {len(drafts)} draft(s) para {path}"
