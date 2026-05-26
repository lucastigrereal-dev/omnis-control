"""Testes — PublisherPrepare (WAVE 9).

Cobre: dry_run, geração real de CSV/JSON, slots de horário,
       filtro por perfil, ManyChat stub, anti-teatro.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from src.agencia.publisher_prepare import PublisherPrepare, PublishPackage


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _setup_approved_drafts(tmp_path: Path, count: int = 2, handle: str = "oinatalrn") -> tuple[str, str]:
    from src.caption_approval.drafts import DraftsManager
    from src.caption_approval.models import DraftStatus

    dp = str(tmp_path / "drafts.jsonl")
    lp = str(tmp_path / "log.jsonl")
    dm = DraftsManager(drafts_path=dp, log_path=lp)
    for i in range(count):
        d = dm.create(
            queue_id=f"q{i}",
            account_handle=handle,
            caption_text=f"Post {i} hotel vista mar natal turismo",
            hashtags=["natal", "hotel", "turismo"],
            cta="Link na bio",
        )
        dm.submit(d.draft_id)
        items = dm.list_all()
        for item in items:
            if item.draft_id == d.draft_id:
                item.status = DraftStatus.APPROVED
        dm._rewrite(items)
    return dp, lp


def _future_date():
    return datetime.now(timezone.utc) + timedelta(days=1)


# ------------------------------------------------------------------
# Testes dry_run
# ------------------------------------------------------------------

class TestDryRun:
    def test_retorna_publish_package(self, tmp_path):
        dp, lp = _setup_approved_drafts(tmp_path)
        prep = PublisherPrepare(dry_run=True, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())
        assert isinstance(pkg, PublishPackage)

    def test_total_posts_correto(self, tmp_path):
        dp, lp = _setup_approved_drafts(tmp_path, count=3)
        prep = PublisherPrepare(dry_run=True, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())
        assert pkg.total_posts == 3

    def test_manifesto_criado(self, tmp_path):
        dp, lp = _setup_approved_drafts(tmp_path)
        prep = PublisherPrepare(dry_run=True, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())
        assert pkg.manifest_path.exists()

    def test_dry_run_nao_cria_csv(self, tmp_path):
        dp, lp = _setup_approved_drafts(tmp_path)
        prep = PublisherPrepare(dry_run=True, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())
        assert pkg.publer_csv_path is None
        assert not (tmp_path / "out" / "publer_bulk.csv").exists()

    def test_dry_run_nao_cria_manychat(self, tmp_path):
        dp, lp = _setup_approved_drafts(tmp_path)
        prep = PublisherPrepare(dry_run=True, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())
        assert pkg.manychat_stub_path is None

    def test_sem_drafts_gera_warning(self, tmp_path):
        prep = PublisherPrepare(
            dry_run=True,
            drafts_path=tmp_path / "empty.jsonl",
            log_path=tmp_path / "log.jsonl",
        )
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())
        assert pkg.total_posts == 0
        assert len(pkg.warnings) > 0

    def test_to_dict_round_trip(self, tmp_path):
        dp, lp = _setup_approved_drafts(tmp_path)
        prep = PublisherPrepare(dry_run=True, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())
        d = pkg.to_dict()
        assert d["total_posts"] == pkg.total_posts
        assert d["dry_run"] is True
        assert isinstance(d["slots"], list)


# ------------------------------------------------------------------
# Testes real (dry_run=False)
# ------------------------------------------------------------------

class TestGeracaoReal:
    def test_cria_publer_csv(self, tmp_path):
        dp, lp = _setup_approved_drafts(tmp_path)
        prep = PublisherPrepare(dry_run=False, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())
        assert pkg.publer_csv_path is not None
        assert pkg.publer_csv_path.exists()

    def test_csv_colunas_corretas(self, tmp_path):
        dp, lp = _setup_approved_drafts(tmp_path, count=1)
        prep = PublisherPrepare(dry_run=False, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())
        rows = list(csv.DictReader(pkg.publer_csv_path.open(encoding="utf-8")))
        assert len(rows) == 1
        assert "Account" in rows[0]
        assert "Date" in rows[0]
        assert "Caption" in rows[0]

    def test_csv_account_com_arroba(self, tmp_path):
        dp, lp = _setup_approved_drafts(tmp_path, count=1)
        prep = PublisherPrepare(dry_run=False, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())
        rows = list(csv.DictReader(pkg.publer_csv_path.open(encoding="utf-8")))
        assert rows[0]["Account"].startswith("@")

    def test_cria_manychat_stub(self, tmp_path):
        dp, lp = _setup_approved_drafts(tmp_path)
        prep = PublisherPrepare(dry_run=False, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())
        assert pkg.manychat_stub_path is not None
        assert pkg.manychat_stub_path.exists()

    def test_manychat_stub_e_json_valido(self, tmp_path):
        dp, lp = _setup_approved_drafts(tmp_path)
        prep = PublisherPrepare(dry_run=False, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())
        stub = json.loads(pkg.manychat_stub_path.read_text())
        assert "STUB" in stub["_status"]
        assert "trigger" in stub
        assert "flow" in stub
        assert "posts" in stub


# ------------------------------------------------------------------
# Slots de horário
# ------------------------------------------------------------------

class TestSlots:
    def test_slots_tem_data_futura(self, tmp_path):
        dp, lp = _setup_approved_drafts(tmp_path, count=1)
        prep = PublisherPrepare(dry_run=True, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        start = datetime(2030, 6, 1, 12, 0, tzinfo=timezone.utc)
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=start)
        assert all(s.scheduled_date >= "2030-06-01" for s in pkg.slots)

    def test_filtro_account(self, tmp_path):
        dp1, _ = _setup_approved_drafts(tmp_path / "a", count=2, handle="oinatalrn")
        dp2, _ = _setup_approved_drafts(tmp_path / "b", count=1, handle="lucastigrereal")
        # Combina os dois arquivos
        combined = tmp_path / "combined.jsonl"
        combined.write_text(
            (tmp_path / "a" / "drafts.jsonl").read_text() +
            (tmp_path / "b" / "drafts.jsonl").read_text(),
            encoding="utf-8",
        )
        prep = PublisherPrepare(
            dry_run=True,
            drafts_path=combined,
            log_path=tmp_path / "log.jsonl",
        )
        pkg = prep.prepare(
            account_filter="oinatalrn",
            output_dir=tmp_path / "out",
            start_date=_future_date(),
        )
        assert pkg.total_posts == 2
        assert all(s.account == "@oinatalrn" for s in pkg.slots)


# ------------------------------------------------------------------
# Anti-teatro
# ------------------------------------------------------------------

class TestAntiTeatro:
    def test_manifesto_reflete_caption_real(self, tmp_path):
        CAPTION_UNICO = "ANTI_TEATRO_WAVE9_PUBLISHER_PREPARE"
        from src.caption_approval.drafts import DraftsManager
        from src.caption_approval.models import DraftStatus

        dp = str(tmp_path / "drafts.jsonl")
        lp = str(tmp_path / "log.jsonl")
        dm = DraftsManager(drafts_path=dp, log_path=lp)
        d = dm.create(
            queue_id="q-at",
            account_handle="oinatalrn",
            caption_text=CAPTION_UNICO,
            hashtags=["#at"],
        )
        dm.submit(d.draft_id)
        items = dm.list_all()
        for item in items:
            if item.draft_id == d.draft_id:
                item.status = DraftStatus.APPROVED
        dm._rewrite(items)

        prep = PublisherPrepare(dry_run=True, drafts_path=tmp_path / "drafts.jsonl", log_path=tmp_path / "log.jsonl")
        pkg = prep.prepare(output_dir=tmp_path / "out", start_date=_future_date())

        data = json.loads(pkg.manifest_path.read_text())
        captions = [s["caption"] for s in data["slots"]]
        assert CAPTION_UNICO in captions
