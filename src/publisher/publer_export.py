"""Publer/Metricool Export — export contract for external scheduling platforms."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class PublerPlatform(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"


@dataclass
class PublerExportItem:
    item_id: str
    caption: str
    account_handle: str
    platform: PublerPlatform = PublerPlatform.INSTAGRAM
    media_url: str = ""
    hashtags: list[str] = field(default_factory=list)
    schedule_iso: str = ""
    link_in_bio: str = ""
    first_comment: str = ""

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "caption": self.caption,
            "account_handle": self.account_handle,
            "platform": self.platform.value,
            "media_url": self.media_url,
            "hashtags": self.hashtags,
            "schedule_iso": self.schedule_iso,
            "link_in_bio": self.link_in_bio,
            "first_comment": self.first_comment,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PublerExportItem":
        return cls(
            item_id=d["item_id"],
            caption=d.get("caption", ""),
            account_handle=d.get("account_handle", ""),
            platform=PublerPlatform(d.get("platform", "instagram")),
            media_url=d.get("media_url", ""),
            hashtags=d.get("hashtags", []),
            schedule_iso=d.get("schedule_iso", ""),
            link_in_bio=d.get("link_in_bio", ""),
            first_comment=d.get("first_comment", ""),
        )


@dataclass
class PublerExportBatch:
    batch_id: str
    label: str = ""
    items: list[PublerExportItem] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dry_run: bool = True

    def add(self, item: PublerExportItem) -> None:
        self.items.append(item)

    def to_csv_rows(self) -> list[dict]:
        return [i.to_dict() for i in self.items]

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "label": self.label,
            "item_count": len(self.items),
            "created_at": self.created_at,
            "dry_run": self.dry_run,
            "items": [i.to_dict() for i in self.items],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PublerExportBatch":
        batch = cls(
            batch_id=d["batch_id"],
            label=d.get("label", ""),
            created_at=d.get("created_at", ""),
            dry_run=d.get("dry_run", True),
        )
        for i in d.get("items", []):
            batch.add(PublerExportItem.from_dict(i))
        return batch


@dataclass
class PublerBatchExporter:
    """Deterministic Publer/Metricool export — dry-run only, no API calls."""

    dry_run: bool = True
    batches: dict[str, PublerExportBatch] = field(default_factory=dict)

    def create_batch(self, label: str = "") -> PublerExportBatch:
        import uuid
        batch = PublerExportBatch(
            batch_id=str(uuid.uuid4())[:8],
            label=label,
            dry_run=self.dry_run,
        )
        self.batches[batch.batch_id] = batch
        return batch

    def build_item(
        self,
        caption: str,
        account_handle: str,
        media_url: str = "",
        hashtags: list[str] | None = None,
        schedule_iso: str = "",
    ) -> PublerExportItem:
        import uuid
        return PublerExportItem(
            item_id=str(uuid.uuid4())[:8],
            caption=caption,
            account_handle=account_handle,
            media_url=media_url,
            hashtags=hashtags or [],
            schedule_iso=schedule_iso,
        )

    def export_batch(self, batch_id: str) -> str | None:
        """Export a batch as CSV-formatted string (dry-run — never writes to disk)."""
        batch = self.batches.get(batch_id)
        if batch is None or not batch.items:
            return None
        headers = ["item_id", "caption", "account_handle", "platform", "media_url", "hashtags", "schedule_iso"]
        rows = []
        for item in batch.items:
            d = item.to_dict()
            d["hashtags"] = " ".join(item.hashtags)
            rows.append(",".join(str(d.get(h, "")) for h in headers))
        header_line = ",".join(headers)
        return header_line + "\n" + "\n".join(rows)

    def to_dict(self) -> dict:
        return {
            "dry_run": self.dry_run,
            "batches": {k: v.to_dict() for k, v in self.batches.items()},
        }


# Backward-compat alias — tests and existing code import `PublerExporter`
PublerExporter = PublerBatchExporter


# ---------------------------------------------------------------------------
# PublerZipExporter — ZIP package exporter (B3 / W088-ZIP)
# ---------------------------------------------------------------------------

import csv as _csv
import json as _json
import logging as _logging
import os as _os
import shutil as _shutil
import uuid as _uuid
import zipfile as _zipfile
from pathlib import Path
from typing import Optional

_logger = _logging.getLogger("omnis.publisher.publer_export")

_ROOT = Path(_os.getenv("OMNIS_ROOT", _os.path.expanduser("~/omnis-control")))
_DEFAULT_EXPORTS_BASE = Path("data/publer_exports")

# Horários de pico (reutilizados de publisher_prepare)
_PEAK_HOURS: dict[int, list[str]] = {
    0: ["07:00", "12:00", "19:00"],
    1: ["07:30", "12:00", "20:00"],
    2: ["08:00", "13:00", "19:00"],
    3: ["07:00", "12:30", "20:00"],
    4: ["07:00", "12:00", "18:00"],
    5: ["09:00", "14:00", "20:00"],
    6: ["10:00", "15:00", "19:00"],
}
_TIMEZONE = "America/Sao_Paulo"

_README_PT = """\
=== OMNIS — Instruções de Upload no Publer ===

Este pacote foi gerado automaticamente pelo OMNIS.
Lucas faz o upload manualmente — o OMNIS nunca publica nada sozinho.

PASSO A PASSO:
1. Acesse https://publer.io e faça login na sua conta.
2. Clique em "Bulk Scheduling" ou "Bulk Upload" no menu principal.
3. Selecione o arquivo `publer_bulk.csv` desta pasta.
4. Revise os posts agendados na pré-visualização do Publer.
5. Se houver mídia (fotos/vídeos), faça upload dos arquivos da pasta `assets/`
   e vincule cada um ao post correspondente.
6. Clique em "Schedule All" para agendar.

ARQUIVOS DESTE PACOTE:
- publer_bulk.csv       → CSV com todos os posts prontos para import
- assets/               → Pasta com arquivos de mídia (se disponíveis)
- README_instrucoes.txt → Este arquivo
- manifest.json         → Metadados do pacote (para referência)

ATENÇÃO:
- Revise as legendas antes de agendar.
- Ajuste horários se necessário direto no Publer.
- Em caso de dúvida, abra o manifest.json para ver os detalhes de cada post.

Gerado por OMNIS Control — {created_at}
"""

_CSV_FIELDNAMES = ["Account", "Date", "Time", "Timezone", "Caption", "Hashtags", "CTA", "Media Files", "Type"]


@dataclass
class PublerPackage:
    """Pacote ZIP pronto para upload manual no Publer."""

    package_id: str
    created_at: str
    output_dir: Path
    zip_path: Optional[Path]      # None se dry_run=True
    csv_path: Path                # sempre gerado
    manifest_path: Path           # sempre gerado
    total_posts: int
    dry_run: bool
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "created_at": self.created_at,
            "output_dir": str(self.output_dir),
            "zip_path": str(self.zip_path) if self.zip_path else None,
            "csv_path": str(self.csv_path),
            "manifest_path": str(self.manifest_path),
            "total_posts": self.total_posts,
            "dry_run": self.dry_run,
            "warnings": self.warnings,
        }

    def summary(self) -> str:
        lines = [
            "=== PUBLER PACKAGE ===",
            f"package_id:  {self.package_id}",
            f"created_at:  {self.created_at[:19]}",
            f"output_dir:  {self.output_dir}",
            f"total_posts: {self.total_posts}",
            f"dry_run:     {self.dry_run}",
            f"csv:         {self.csv_path.name}",
            f"zip:         {self.zip_path.name if self.zip_path else 'N/A (dry_run)'}",
        ]
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  AVISO: {w}")
        return "\n".join(lines)


class PublerZipExporter:
    """Gera pacote ZIP pronto para upload manual no Publer.

    dry_run=True  → CSV + manifest gerados, ZIP NÃO criado, assets NÃO copiados.
    dry_run=False → ZIP completo: publer_bulk.csv + assets/ + README + manifest.

    Lucas faz upload manual — OMNIS nunca publica nada.
    """

    def __init__(
        self,
        dry_run: bool = True,
        drafts_path: Optional[Path] = None,
        output_base: Path = _DEFAULT_EXPORTS_BASE,
    ) -> None:
        self.dry_run = dry_run
        self._drafts_path: Optional[Path] = Path(drafts_path) if drafts_path else None
        self.output_base = Path(output_base)

    def export(
        self,
        account_filter: Optional[str] = None,
        output_dir: Optional[Path] = None,
        package_id: Optional[str] = None,
    ) -> PublerPackage:
        """Gera o pacote de exportação Publer.

        Args:
            account_filter: Perfil @handle para filtrar (None = todos os aprovados).
            output_dir:     Pasta de trabalho. Default: data/publer_exports/<date>-<id>.
            package_id:     ID do pacote. Gerado automaticamente se omitido.

        Returns:
            PublerPackage com paths dos arquivos gerados.
        """
        from src.caption_approval.drafts import DraftsManager, DRAFTS_PATH, APPROVAL_LOG_PATH
        from src.caption_approval.models import DraftStatus
        from datetime import datetime, timezone, timedelta

        if package_id is None:
            package_id = _uuid.uuid4().hex[:8]

        now = datetime.now(timezone.utc)
        created_at = now.isoformat()

        if output_dir is None:
            date_str = now.strftime("%Y-%m-%d")
            output_dir = self.output_base / f"{date_str}-{package_id}"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Carrega drafts aprovados
        drafts_path = str(self._drafts_path) if self._drafts_path else DRAFTS_PATH
        log_path = APPROVAL_LOG_PATH
        dm = DraftsManager(drafts_path=drafts_path, log_path=log_path)
        all_drafts = [d for d in dm.list_all() if d.status == DraftStatus.APPROVED]

        if account_filter:
            handle = account_filter.lstrip("@")
            all_drafts = [d for d in all_drafts if d.account_handle.lstrip("@") == handle]

        warnings: list[str] = []
        if not all_drafts:
            warnings.append("Nenhum draft aprovado encontrado para exportar")

        # Distribui em slots de horário de pico
        slots = self._assign_slots(all_drafts, now)

        # Gera CSV (sempre)
        csv_path = output_dir / "publer_bulk.csv"
        self._write_csv(csv_path, slots)

        # README
        readme_path = output_dir / "README_instrucoes.txt"
        readme_path.write_text(
            _README_PT.format(created_at=created_at[:19]),
            encoding="utf-8",
        )

        # Manifesto (sempre)
        manifest_path = output_dir / "manifest.json"

        zip_path: Optional[Path] = None
        assets_dir: Optional[Path] = None

        if not self.dry_run:
            # Copia assets dos drafts aprovados
            assets_dir = output_dir / "assets"
            assets_dir.mkdir(exist_ok=True)
            self._copy_assets(all_drafts, assets_dir)

            # Determina path do ZIP (timestamp no nome)
            ts = now.strftime("%Y%m%d_%H%M%S")
            zip_path = output_dir / f"publer_export_{ts}.zip"

        pkg = PublerPackage(
            package_id=package_id,
            created_at=created_at,
            output_dir=output_dir,
            zip_path=zip_path,
            csv_path=csv_path,
            manifest_path=manifest_path,
            total_posts=len(slots),
            dry_run=self.dry_run,
            warnings=warnings,
        )

        # Escreve manifest primeiro (para que seja incluído no ZIP)
        manifest_path.write_text(
            _json.dumps(pkg.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if not self.dry_run and zip_path is not None:
            # Cria ZIP com todos os arquivos (manifest já escrito)
            self._write_zip(zip_path, csv_path, assets_dir, readme_path, manifest_path)

        _logger.info(
            "publer_export: %s — %d posts | dry_run=%s",
            package_id, len(slots), self.dry_run,
        )
        return pkg

    # ------------------------------------------------------------------
    # Slot assignment
    # ------------------------------------------------------------------

    def _assign_slots(self, drafts: list, now: "datetime") -> list[dict]:
        """Distribui drafts em slots de horário de pico (próximos 14 dias)."""
        from datetime import timedelta

        slot_pool: list[tuple[str, str]] = []
        for delta in range(14):
            d = now + timedelta(days=delta + 1)
            day_of_week = d.weekday()
            date_str = d.strftime("%Y-%m-%d")
            for hour_str in _PEAK_HOURS.get(day_of_week, ["12:00"]):
                slot_pool.append((date_str, hour_str))
            if len(slot_pool) >= max(len(drafts) * 2, 6):
                break

        slots = []
        for i, draft in enumerate(drafts):
            date_str, time_str = slot_pool[i % len(slot_pool)] if slot_pool else (
                (now + timedelta(days=i + 1)).strftime("%Y-%m-%d"), "12:00"
            )
            hashtags_str = " ".join(f"#{h.lstrip('#')}" for h in (draft.hashtags or []))
            slots.append({
                "account": f"@{draft.account_handle.lstrip('@')}",
                "date": date_str,
                "time": time_str,
                "caption": draft.caption_text or "",
                "hashtags": hashtags_str,
                "cta": getattr(draft, "cta", "") or "",
                "draft_id": draft.draft_id,
            })
        return slots

    # ------------------------------------------------------------------
    # CSV writer
    # ------------------------------------------------------------------

    def _write_csv(self, path: Path, slots: list[dict]) -> None:
        """Escreve publer_bulk.csv no formato Publer bulk import."""
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = _csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
            writer.writeheader()
            for s in slots:
                writer.writerow({
                    "Account":     s["account"],
                    "Date":        s["date"],
                    "Time":        s["time"],
                    "Timezone":    _TIMEZONE,
                    "Caption":     s["caption"].replace("\n", "\\n"),
                    "Hashtags":    s["hashtags"],
                    "CTA":         s["cta"],
                    "Media Files": "",
                    "Type":        "reel",
                })

    # ------------------------------------------------------------------
    # Asset copy
    # ------------------------------------------------------------------

    def _copy_assets(self, drafts: list, assets_dir: Path) -> None:
        """Copia assets dos drafts aprovados para a pasta assets/."""
        for draft in drafts:
            asset_id = getattr(draft, "asset_id", None)
            if not asset_id:
                continue
            # Heurística: tenta localizar pasta de carrossel pelo account_handle
            acct_dir = Path("output/agencia") / draft.account_handle.lstrip("@")
            if acct_dir.exists():
                for png in acct_dir.rglob("*.png"):
                    dst = assets_dir / png.name
                    if not dst.exists():
                        _shutil.copy2(str(png), str(dst))

    # ------------------------------------------------------------------
    # ZIP writer
    # ------------------------------------------------------------------

    def _write_zip(
        self,
        zip_path: Path,
        csv_path: Path,
        assets_dir: Optional[Path],
        readme_path: Path,
        manifest_path: Path,
    ) -> None:
        """Cria o ZIP final com todos os arquivos do pacote.

        O manifest deve estar escrito em disco antes de chamar este método.
        """
        with _zipfile.ZipFile(str(zip_path), "w", compression=_zipfile.ZIP_DEFLATED) as zf:
            zf.write(str(csv_path), "publer_bulk.csv")
            zf.write(str(readme_path), "README_instrucoes.txt")
            if manifest_path.exists():
                zf.write(str(manifest_path), "manifest.json")
            if assets_dir is not None and assets_dir.exists():
                for asset in assets_dir.iterdir():
                    if asset.is_file():
                        zf.write(str(asset), f"assets/{asset.name}")
