"""Testes — ContentExporter (WAVE 4).

Cobre: dry_run, geração de CSV, manifesto, cópia de assets,
       filtro por perfil, anti-teatro (manifest reflete dados reais).
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import pytest

from src.agencia.export import ContentExporter, ExportResult


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _setup_drafts(tmp_path: Path, count: int = 2) -> tuple[str, str]:
    """Cria N drafts approved no tmp_path, retorna (drafts_path, log_path)."""
    from src.caption_approval.drafts import DraftsManager
    from src.caption_approval.models import DraftStatus

    dp = str(tmp_path / "drafts.jsonl")
    lp = str(tmp_path / "log.jsonl")
    dm = DraftsManager(drafts_path=dp, log_path=lp)

    for i in range(count):
        d = dm.create(
            queue_id=f"q{i}",
            account_handle="oinatalrn",
            caption_text=f"Hotel vista mar post {i} texto aqui",
            hashtags=["#natal", "#hotel"],
            cta="Link na bio",
        )
        dm.submit(d.draft_id)
        # Aprova diretamente no storage (sem ApprovalGate para simplificar)
        items = dm.list_all()
        for item in items:
            if item.draft_id == d.draft_id:
                item.status = DraftStatus.APPROVED
        dm._rewrite(items)

    return dp, lp


# ------------------------------------------------------------------
# Testes dry_run
# ------------------------------------------------------------------

class TestExportDryRun:
    def test_retorna_export_result(self, tmp_path):
        dp, lp = _setup_drafts(tmp_path)
        exp = ContentExporter(dry_run=True)
        result = exp.export(
            export_dir=tmp_path / "export",
            drafts_path=dp,
            log_path=lp,
        )
        assert isinstance(result, ExportResult)

    def test_csv_criado(self, tmp_path):
        dp, lp = _setup_drafts(tmp_path)
        exp = ContentExporter(dry_run=True)
        result = exp.export(
            export_dir=tmp_path / "export",
            drafts_path=dp,
            log_path=lp,
        )
        assert result.csv_path.exists()

    def test_manifesto_criado(self, tmp_path):
        dp, lp = _setup_drafts(tmp_path)
        exp = ContentExporter(dry_run=True)
        result = exp.export(
            export_dir=tmp_path / "export",
            drafts_path=dp,
            log_path=lp,
        )
        assert result.manifest_path.exists()
        data = json.loads(result.manifest_path.read_text())
        assert data["total_drafts"] == 2
        assert data["dry_run"] is True

    def test_sem_drafts_aprovados_gera_csv_vazio(self, tmp_path):
        dp = str(tmp_path / "empty.jsonl")
        lp = str(tmp_path / "log.jsonl")
        exp = ContentExporter(dry_run=True)
        result = exp.export(
            export_dir=tmp_path / "export",
            drafts_path=dp,
            log_path=lp,
        )
        assert result.total_drafts == 0
        assert result.csv_path.exists()

    def test_dry_run_nao_cria_pasta_assets(self, tmp_path):
        dp, lp = _setup_drafts(tmp_path)
        exp = ContentExporter(dry_run=True)
        result = exp.export(
            export_dir=tmp_path / "export",
            drafts_path=dp,
            log_path=lp,
        )
        assets_dir = result.export_dir / "assets"
        assert not assets_dir.exists()


# ------------------------------------------------------------------
# Testes CSV formato
# ------------------------------------------------------------------

class TestCSVFormato:
    def test_csv_tem_colunas_corretas(self, tmp_path):
        dp, lp = _setup_drafts(tmp_path, count=1)
        exp = ContentExporter(dry_run=True)
        result = exp.export(
            export_dir=tmp_path / "export",
            drafts_path=dp,
            log_path=lp,
        )
        with result.csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cols = reader.fieldnames
        assert "account" in cols
        assert "caption" in cols
        assert "hashtags" in cols
        assert "cta" in cols

    def test_csv_linha_contem_texto_do_draft(self, tmp_path):
        dp, lp = _setup_drafts(tmp_path, count=1)
        exp = ContentExporter(dry_run=True)
        result = exp.export(
            export_dir=tmp_path / "export",
            drafts_path=dp,
            log_path=lp,
        )
        rows = list(csv.DictReader(result.csv_path.open(encoding="utf-8")))
        assert len(rows) == 1
        assert "Hotel vista mar" in rows[0]["caption"]

    def test_csv_account_tem_arroba(self, tmp_path):
        dp, lp = _setup_drafts(tmp_path, count=1)
        exp = ContentExporter(dry_run=True)
        result = exp.export(
            export_dir=tmp_path / "export",
            drafts_path=dp,
            log_path=lp,
        )
        rows = list(csv.DictReader(result.csv_path.open(encoding="utf-8")))
        assert rows[0]["account"].startswith("@")


# ------------------------------------------------------------------
# Testes filtro por perfil
# ------------------------------------------------------------------

class TestFiltroAccount:
    def test_filtra_por_perfil(self, tmp_path):
        """2 perfis diferentes → filtro por oinatalrn retorna só os seus."""
        from src.caption_approval.drafts import DraftsManager
        from src.caption_approval.models import DraftStatus

        dp = str(tmp_path / "drafts.jsonl")
        lp = str(tmp_path / "log.jsonl")
        dm = DraftsManager(drafts_path=dp, log_path=lp)

        for handle in ["oinatalrn", "lucastigrereal"]:
            d = dm.create(
                queue_id=f"q-{handle}",
                account_handle=handle,
                caption_text=f"Post de {handle}",
                hashtags=["#t"],
            )
            dm.submit(d.draft_id)
            items = dm.list_all()
            for item in items:
                if item.draft_id == d.draft_id:
                    item.status = DraftStatus.APPROVED
            dm._rewrite(items)

        exp = ContentExporter(dry_run=True)
        result = exp.export(
            account_filter="oinatalrn",
            export_dir=tmp_path / "export",
            drafts_path=dp,
            log_path=lp,
        )
        assert result.total_drafts == 1
        assert result.drafts[0].account_handle == "oinatalrn"


# ------------------------------------------------------------------
# Anti-teatro
# ------------------------------------------------------------------

class TestAntiTeatro:
    def test_manifesto_reflete_texto_real_dos_drafts(self, tmp_path):
        from src.caption_approval.drafts import DraftsManager
        from src.caption_approval.models import DraftStatus

        TEXTO_UNICO = "ANTI_TEATRO_EXPORT_WAVE4_CHECK"
        dp = str(tmp_path / "drafts.jsonl")
        lp = str(tmp_path / "log.jsonl")
        dm = DraftsManager(drafts_path=dp, log_path=lp)
        d = dm.create(
            queue_id="q-at",
            account_handle="oinatalrn",
            caption_text=TEXTO_UNICO,
            hashtags=["#at"],
        )
        dm.submit(d.draft_id)
        items = dm.list_all()
        for item in items:
            if item.draft_id == d.draft_id:
                item.status = DraftStatus.APPROVED
        dm._rewrite(items)

        exp = ContentExporter(dry_run=True)
        result = exp.export(
            export_dir=tmp_path / "export",
            drafts_path=dp,
            log_path=lp,
        )
        data = json.loads(result.manifest_path.read_text())
        textos = [d["caption_text"] for d in data["drafts"]]
        assert TEXTO_UNICO in textos, f"Texto não encontrado no manifesto: {textos}"

    def test_to_dict_round_trip(self, tmp_path):
        dp, lp = _setup_drafts(tmp_path)
        exp = ContentExporter(dry_run=True)
        result = exp.export(
            export_dir=tmp_path / "export",
            drafts_path=dp,
            log_path=lp,
        )
        d = result.to_dict()
        assert d["total_drafts"] == result.total_drafts
        assert d["export_id"] == result.export_id
