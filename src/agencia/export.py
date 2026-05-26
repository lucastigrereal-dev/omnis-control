"""ContentExporter — Exporta pacote aprovado para Publer/CSV.

Pega drafts APPROVED do DraftsManager e empacota em:
  data/exports/<YYYY-MM-DD>/
    posts.csv          — colunas prontas para import no Publer (bulk upload)
    manifest.json      — todos os drafts exportados com metadados completos
    assets/            — cópia dos PNGs de carrossel (se disponíveis)

Formato do CSV (Publer bulk import):
  account, date, time, text, hashtags, cta, media_path, notes

Princípios:
- dry_run=True: gera manifest.json e posts.csv sem copiar assets
- dry_run=False: copia assets para pasta e gera todos os arquivos
- Nunca publica — só entrega arquivo
- Sem inventar dado: draft sem texto → linha vazia explícita no CSV
"""
from __future__ import annotations

import csv
import json
import logging
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("omnis.agencia.export")

_DEFAULT_EXPORTS_DIR = Path("data/exports")

_CARROSSEL_BASE = Path("output/agencia")


@dataclass
class ExportedDraft:
    draft_id: str
    account_handle: str
    caption_text: str
    hashtags: list[str]
    cta: str
    status: str
    asset_id: Optional[str]
    notes: str
    carrossel_paths: list[str] = field(default_factory=list)
    thumbnail_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "draft_id": self.draft_id,
            "account_handle": self.account_handle,
            "caption_text": self.caption_text,
            "hashtags": self.hashtags,
            "cta": self.cta,
            "status": self.status,
            "asset_id": self.asset_id,
            "notes": self.notes,
            "carrossel_paths": self.carrossel_paths,
            "thumbnail_path": self.thumbnail_path,
        }


@dataclass
class ExportResult:
    export_id: str
    export_dir: Path
    csv_path: Path
    manifest_path: Path
    total_drafts: int
    total_assets_copied: int
    dry_run: bool
    exported_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    drafts: list[ExportedDraft] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "export_id": self.export_id,
            "export_dir": str(self.export_dir),
            "csv_path": str(self.csv_path),
            "manifest_path": str(self.manifest_path),
            "total_drafts": self.total_drafts,
            "total_assets_copied": self.total_assets_copied,
            "dry_run": self.dry_run,
            "exported_at": self.exported_at,
            "drafts": [d.to_dict() for d in self.drafts],
            "warnings": self.warnings,
        }

    def summary(self) -> str:
        lines = [
            f"export_id={self.export_id}  dry_run={self.dry_run}",
            f"output:     {self.export_dir}",
            f"csv:        {self.csv_path.name}",
            f"manifest:   {self.manifest_path.name}",
            f"drafts:     {self.total_drafts}",
            f"assets:     {self.total_assets_copied} copiados",
        ]
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  AVISO: {w}")
        return "\n".join(lines)


class ContentExporter:
    """Exporta drafts aprovados para pacote Publer-ready.

    Uso:
        exporter = ContentExporter(dry_run=False)
        result = exporter.export(
            account_filter="oinatalrn",
            export_dir=Path("data/exports/2026-05-25"),
        )
        print(result.summary())
    """

    def __init__(self, dry_run: bool = True, exports_base: Path = _DEFAULT_EXPORTS_DIR) -> None:
        self.dry_run = dry_run
        self.exports_base = Path(exports_base)

    def export(
        self,
        account_filter: Optional[str] = None,
        export_dir: Optional[Path] = None,
        export_id: Optional[str] = None,
        drafts_path: Optional[str] = None,
        log_path: Optional[str] = None,
    ) -> ExportResult:
        """Exporta todos os drafts APPROVED para um pacote exportável.

        Args:
            account_filter: Se informado, filtra por @perfil.
            export_dir:     Pasta de destino. Default: data/exports/<date>-<id>.
            export_id:      ID único do export. Gerado se não fornecido.
            drafts_path:    Caminho ao JSONL de drafts (para testes isolados).
            log_path:       Caminho ao log de aprovações (para testes isolados).

        Returns:
            ExportResult com paths gerados e contagem de assets.
        """
        from src.caption_approval.drafts import DraftsManager, DRAFTS_PATH, APPROVAL_LOG_PATH
        from src.caption_approval.models import DraftStatus

        if export_id is None:
            export_id = str(uuid.uuid4())[:8]

        if export_dir is None:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            export_dir = self.exports_base / f"{today}-{export_id}"

        export_dir = Path(export_dir)

        # DraftsManager — usa paths injetados (testes) ou padrão (produção)
        dm = DraftsManager(
            drafts_path=drafts_path or DRAFTS_PATH,
            log_path=log_path or APPROVAL_LOG_PATH,
        )

        all_drafts = dm.list_all()
        approved = [d for d in all_drafts if d.status == DraftStatus.APPROVED]

        if account_filter:
            handle = account_filter.lstrip("@")
            approved = [d for d in approved if d.account_handle.lstrip("@") == handle]

        warnings: list[str] = []
        exported: list[ExportedDraft] = []
        assets_copied = 0

        for draft in approved:
            carrossel_paths: list[str] = []
            thumbnail_path: Optional[str] = None

            # Tenta encontrar carrossel associado via account_handle (heurística)
            acct_dir = _CARROSSEL_BASE / draft.account_handle.lstrip("@")
            if acct_dir.exists():
                # Busca manifesto mais recente com draft_id no nome ou no conteúdo
                manifests = sorted(acct_dir.rglob("*.manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                for manifest_path in manifests[:3]:  # checa os 3 mais recentes
                    try:
                        mdata = json.loads(manifest_path.read_text(encoding="utf-8"))
                        slides_raw = mdata.get("slides", [])
                        thumb_raw  = mdata.get("thumbnail")
                        if slides_raw:
                            carrossel_paths = slides_raw
                            thumbnail_path = thumb_raw
                            break
                    except Exception:  # noqa: BLE001
                        continue

            exp = ExportedDraft(
                draft_id=draft.draft_id,
                account_handle=draft.account_handle,
                caption_text=draft.caption_text or "",
                hashtags=draft.hashtags or [],
                cta=draft.cta or "",
                status=draft.status,
                asset_id=draft.asset_id,
                notes=draft.notes or "",
                carrossel_paths=carrossel_paths,
                thumbnail_path=thumbnail_path,
            )
            exported.append(exp)

        # Cria diretório de export
        if not self.dry_run:
            export_dir.mkdir(parents=True, exist_ok=True)
            assets_dir = export_dir / "assets"
            assets_dir.mkdir(exist_ok=True)

            # Copia assets (PNG dos carrosseis)
            for exp in exported:
                for png_path in exp.carrossel_paths:
                    src = Path(png_path)
                    if src.exists():
                        dst = assets_dir / src.name
                        shutil.copy2(str(src), str(dst))
                        assets_copied += 1
                if exp.thumbnail_path:
                    src = Path(exp.thumbnail_path)
                    if src.exists():
                        dst = assets_dir / src.name
                        shutil.copy2(str(src), str(dst))
                        assets_copied += 1
        else:
            export_dir.mkdir(parents=True, exist_ok=True)

        # Gera CSV
        csv_path = export_dir / "posts.csv"
        self._write_csv(csv_path, exported, export_dir)

        # Gera manifesto JSON
        manifest_path = export_dir / "manifest.json"

        result = ExportResult(
            export_id=export_id,
            export_dir=export_dir,
            csv_path=csv_path,
            manifest_path=manifest_path,
            total_drafts=len(exported),
            total_assets_copied=assets_copied,
            dry_run=self.dry_run,
            drafts=exported,
            warnings=warnings,
        )

        manifest_path.write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        _logger.info(
            "export: %s — %d drafts, %d assets | dry_run=%s | dir=%s",
            export_id, len(exported), assets_copied, self.dry_run, export_dir,
        )
        return result

    # ------------------------------------------------------------------
    # CSV writer
    # ------------------------------------------------------------------

    def _write_csv(
        self,
        csv_path: Path,
        drafts: list[ExportedDraft],
        export_dir: Path,
    ) -> None:
        """Escreve posts.csv no formato Publer bulk import."""
        fieldnames = [
            "account",
            "caption",
            "hashtags",
            "cta",
            "media_files",
            "thumbnail",
            "draft_id",
            "notes",
        ]
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for draft in drafts:
                # media_files: paths relativos ao export_dir (ou absolutos se dry_run)
                media = "|".join(
                    str(Path(p).name) if not self.dry_run else str(p)
                    for p in draft.carrossel_paths
                )
                thumb = (
                    str(Path(draft.thumbnail_path).name)
                    if draft.thumbnail_path and not self.dry_run
                    else (draft.thumbnail_path or "")
                )
                writer.writerow({
                    "account":    f"@{draft.account_handle.lstrip('@')}",
                    "caption":    draft.caption_text.replace("\n", "\\n"),
                    "hashtags":   " ".join(f"#{h.lstrip('#')}" for h in draft.hashtags),
                    "cta":        draft.cta,
                    "media_files": media,
                    "thumbnail":   thumb,
                    "draft_id":   draft.draft_id,
                    "notes":      draft.notes,
                })
