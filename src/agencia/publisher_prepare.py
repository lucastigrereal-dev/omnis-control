"""PublisherPrepare — Gera payload pronto para Publer + stub ManyChat.

NUNCA publica. Só entrega arquivos em data/publish_ready/<date>/:
  publer_bulk.csv     — formato Publer bulk upload (scheduled posts)
  manychat_stub.json  — estrutura de automation ManyChat (stub, sem API real)
  manifest.json       — resumo do pacote gerado

Contexto:
  Publer: ferramenta de agendamento de posts com bulk upload via CSV.
  ManyChat: bot de Instagram DM para capturar leads após post.

Princípios:
- dry_run=True: gera apenas manifest.json sem criar os outros arquivos
- dry_run=False: cria todos os arquivos em data/publish_ready/
- Slots de horário gerados automaticamente (horários de pico configuráveis)
- Sem credencial, sem API, sem OAuth
- to_dict() estável para KRATOS consumir
"""
from __future__ import annotations

import csv
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("omnis.agencia.publisher_prepare")

_ROOT = Path(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))
_DEFAULT_OUT = Path("data/publish_ready")

# Horários de pico por dia da semana (0=seg, 6=dom)
_PEAK_HOURS: dict[int, list[str]] = {
    0: ["07:00", "12:00", "19:00"],   # segunda
    1: ["07:30", "12:00", "20:00"],   # terça
    2: ["08:00", "13:00", "19:00"],   # quarta
    3: ["07:00", "12:30", "20:00"],   # quinta
    4: ["07:00", "12:00", "18:00"],   # sexta
    5: ["09:00", "14:00", "20:00"],   # sábado
    6: ["10:00", "15:00", "19:00"],   # domingo
}

# Perfil → timezone offset Brasil (simplificado)
_TIMEZONE = "America/Sao_Paulo"


@dataclass
class PostSlot:
    account: str
    scheduled_date: str    # YYYY-MM-DD
    scheduled_time: str    # HH:MM
    caption: str
    hashtags: str
    cta: str
    media_files: str       # pipe-separated filenames
    draft_id: str
    post_type: str = "reel"  # reel | carousel | feed

    def to_dict(self) -> dict:
        return {
            "account": self.account,
            "scheduled_date": self.scheduled_date,
            "scheduled_time": self.scheduled_time,
            "caption": self.caption,
            "hashtags": self.hashtags,
            "cta": self.cta,
            "media_files": self.media_files,
            "draft_id": self.draft_id,
            "post_type": self.post_type,
        }


@dataclass
class PublishPackage:
    package_id: str
    created_at: str
    output_dir: Path
    total_posts: int
    slots: list[PostSlot]
    publer_csv_path: Optional[Path]
    manychat_stub_path: Optional[Path]
    manifest_path: Path
    dry_run: bool
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "created_at": self.created_at,
            "output_dir": str(self.output_dir),
            "total_posts": self.total_posts,
            "slots": [s.to_dict() for s in self.slots],
            "publer_csv_path": str(self.publer_csv_path) if self.publer_csv_path else None,
            "manychat_stub_path": str(self.manychat_stub_path) if self.manychat_stub_path else None,
            "manifest_path": str(self.manifest_path),
            "dry_run": self.dry_run,
            "warnings": self.warnings,
        }

    def summary(self) -> str:
        lines = [
            f"=== PUBLISH PACKAGE ===",
            f"package_id:  {self.package_id}",
            f"created_at:  {self.created_at[:19]}",
            f"output_dir:  {self.output_dir}",
            f"total_posts: {self.total_posts}",
            f"dry_run:     {self.dry_run}",
        ]
        for s in self.slots:
            lines.append(
                f"  [{s.scheduled_date} {s.scheduled_time}] @{s.account.lstrip('@'):20s} "
                f"— {s.caption[:40]}..."
            )
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  AVISO: {w}")
        lines += [
            f"",
            f"Publer CSV:    {self.publer_csv_path or 'N/A (dry_run)'}",
            f"ManyChat stub: {self.manychat_stub_path or 'N/A (dry_run)'}",
        ]
        return "\n".join(lines)


class PublisherPrepare:
    """Prepara payload de publicação para Publer + stub ManyChat.

    Uso:
        prep = PublisherPrepare(dry_run=False)
        pkg = prep.prepare(
            account_filter="oinatalrn",
            start_date=date.today() + timedelta(days=1),
        )
        print(pkg.summary())
    """

    def __init__(
        self,
        dry_run: bool = True,
        output_base: Path = _DEFAULT_OUT,
        drafts_path: Optional[Path] = None,
        log_path: Optional[Path] = None,
    ) -> None:
        self.dry_run = dry_run
        self.output_base = Path(output_base)
        self._drafts_path = Path(drafts_path) if drafts_path else _ROOT / "data" / "caption_drafts.jsonl"
        self._log_path = Path(log_path) if log_path else _ROOT / "data" / "approval_log.jsonl"

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def prepare(
        self,
        account_filter: Optional[str] = None,
        start_date: Optional["datetime"] = None,
        package_id: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ) -> PublishPackage:
        """Prepara o pacote de publicação com slots agendados.

        Args:
            account_filter: @perfil para filtrar (None = todos os aprovados)
            start_date:     Data inicial para agendamento (default: amanhã)
            package_id:     ID do pacote (gerado se omitido)
            output_dir:     Pasta de saída (default: data/publish_ready/<date>)

        Returns:
            PublishPackage com paths dos arquivos gerados.
        """
        from src.caption_approval.drafts import DraftsManager
        from src.caption_approval.models import DraftStatus

        if package_id is None:
            package_id = str(uuid.uuid4())[:8]

        if output_dir is None:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            output_dir = self.output_base / f"{today}-{package_id}"

        output_dir = Path(output_dir)

        if start_date is None:
            start_date = datetime.now(timezone.utc) + timedelta(days=1)

        # Carrega drafts aprovados
        dm = DraftsManager(
            drafts_path=str(self._drafts_path),
            log_path=str(self._log_path),
        )
        all_drafts = [d for d in dm.list_all() if d.status == DraftStatus.APPROVED]

        if account_filter:
            handle = account_filter.lstrip("@")
            all_drafts = [d for d in all_drafts if d.account_handle.lstrip("@") == handle]

        warnings: list[str] = []
        if not all_drafts:
            warnings.append("Nenhum draft aprovado encontrado para publicar")

        # Gera slots de horário
        slots = self._assign_slots(all_drafts, start_date)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Gera arquivos (somente se não dry_run)
        publer_path:   Optional[Path] = None
        manychat_path: Optional[Path] = None

        if not self.dry_run:
            publer_path = output_dir / "publer_bulk.csv"
            self._write_publer_csv(publer_path, slots)

            manychat_path = output_dir / "manychat_stub.json"
            self._write_manychat_stub(manychat_path, slots)

        # Manifesto sempre gerado
        manifest_path = output_dir / "manifest.json"
        pkg = PublishPackage(
            package_id=package_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            output_dir=output_dir,
            total_posts=len(slots),
            slots=slots,
            publer_csv_path=publer_path,
            manychat_stub_path=manychat_path,
            manifest_path=manifest_path,
            dry_run=self.dry_run,
            warnings=warnings,
        )
        manifest_path.write_text(
            json.dumps(pkg.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        _logger.info(
            "publisher_prepare: %s — %d posts | dry_run=%s",
            package_id, len(slots), self.dry_run,
        )
        return pkg

    # ------------------------------------------------------------------
    # Geração de slots
    # ------------------------------------------------------------------

    def _assign_slots(self, drafts, start_date: datetime) -> list[PostSlot]:
        """Distribui drafts em slots de horário de pico."""
        slots: list[PostSlot] = []
        current_date = start_date
        slot_pool: list[tuple[str, str]] = []  # (date_str, time_str)

        # Gera pool de slots para os próximos 14 dias
        for delta in range(14):
            d = current_date + timedelta(days=delta)
            day_of_week = d.weekday()
            date_str = d.strftime("%Y-%m-%d")
            for hour_str in _PEAK_HOURS.get(day_of_week, ["12:00"]):
                slot_pool.append((date_str, hour_str))
            if len(slot_pool) >= len(drafts) * 2:
                break

        for i, draft in enumerate(drafts):
            date_str, time_str = slot_pool[i % len(slot_pool)] if slot_pool else (
                (current_date + timedelta(days=i)).strftime("%Y-%m-%d"), "12:00"
            )

            hashtags_str = " ".join(f"#{h.lstrip('#')}" for h in (draft.hashtags or []))
            slots.append(PostSlot(
                account=f"@{draft.account_handle.lstrip('@')}",
                scheduled_date=date_str,
                scheduled_time=time_str,
                caption=draft.caption_text or "",
                hashtags=hashtags_str,
                cta=draft.cta or "",
                media_files="",  # preenchido quando carrossel estiver linkado
                draft_id=draft.draft_id,
                post_type="reel",
            ))

        return slots

    # ------------------------------------------------------------------
    # Publer CSV
    # ------------------------------------------------------------------

    def _write_publer_csv(self, path: Path, slots: list[PostSlot]) -> None:
        """CSV no formato Publer bulk upload."""
        fieldnames = [
            "Account", "Date", "Time", "Timezone",
            "Caption", "Hashtags", "CTA", "Media Files", "Type",
        ]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in slots:
                writer.writerow({
                    "Account":     s.account,
                    "Date":        s.scheduled_date,
                    "Time":        s.scheduled_time,
                    "Timezone":    _TIMEZONE,
                    "Caption":     s.caption.replace("\n", "\\n"),
                    "Hashtags":    s.hashtags,
                    "CTA":         s.cta,
                    "Media Files": s.media_files,
                    "Type":        s.post_type,
                })

    # ------------------------------------------------------------------
    # ManyChat stub
    # ------------------------------------------------------------------

    def _write_manychat_stub(self, path: Path, slots: list[PostSlot]) -> None:
        """JSON stub de automação ManyChat (sem API real)."""
        stub = {
            "_note": "ManyChat automation stub — configure no painel ManyChat com estes dados",
            "_status": "STUB — não conectado a API real",
            "trigger": {
                "type": "post_comment",
                "keyword": "QUERO",
                "match": "contains",
            },
            "flow": [
                {
                    "action": "send_dm",
                    "message": (
                        "Oi! Vi que você comentou no post. "
                        "Clica no link aqui pra saber mais: {{link}}"
                    ),
                },
                {
                    "action": "tag_subscriber",
                    "tag": "lead_instagram",
                },
                {
                    "action": "add_to_sequence",
                    "sequence": "nurturing_7dias",
                },
            ],
            "posts": [
                {
                    "draft_id": s.draft_id,
                    "account": s.account,
                    "scheduled": f"{s.scheduled_date} {s.scheduled_time}",
                }
                for s in slots
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(json.dumps(stub, ensure_ascii=False, indent=2), encoding="utf-8")
