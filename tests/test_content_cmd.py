"""Testes — content_cmd (WAVE 3).

Cobre: batch_approve, aprovação unitária, rejeição, lista, status.
Usa tmp_path para isolar storage — não toca data/ real.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.cli import app
from src.caption_approval.drafts import DraftsManager
from src.caption_approval.approvals import ApprovalGate
from src.caption_approval.models import DraftStatus

runner = CliRunner(mix_stderr=False)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _dm(tmp_path: Path) -> DraftsManager:
    return DraftsManager(
        drafts_path=str(tmp_path / "drafts.jsonl"),
        log_path=str(tmp_path / "log.jsonl"),
    )


def _create_valid_draft(dm: DraftsManager, queue_id: str = "q1", handle: str = "oinatalrn"):
    d = dm.create(
        queue_id=queue_id,
        account_handle=handle,
        caption_text="Texto valido hotel vista mar turismo natal",
        cta="Link na bio",
        hashtags=["#natal", "#hotel", "#turismo"],
    )
    dm.submit(d.draft_id)
    return d


# ------------------------------------------------------------------
# Testes unitários — ApprovalGate.batch_approve (sem CLI)
# ------------------------------------------------------------------

class TestBatchApproveUnit:
    def test_aprova_drafts_validos(self, tmp_path):
        dm = _dm(tmp_path)
        gate = ApprovalGate(dm)
        for i in range(3):
            _create_valid_draft(dm, queue_id=f"q{i}")
        r = gate.batch_approve(limit=5)
        assert r["approved"] == 3
        assert r["skipped"] == 0

    def test_pula_draft_com_placeholder(self, tmp_path):
        dm = _dm(tmp_path)
        gate = ApprovalGate(dm)
        d = dm.create(
            queue_id="qX",
            account_handle="oinatalrn",
            caption_text="[HOOK A REVISAR] texto aqui",
            hashtags=["#t"],
        )
        dm.submit(d.draft_id)
        r = gate.batch_approve(limit=5)
        assert r["approved"] == 0
        assert r["skipped"] == 1

    def test_pula_draft_texto_vazio(self, tmp_path):
        dm = _dm(tmp_path)
        gate = ApprovalGate(dm)
        d = dm.create(queue_id="qY", account_handle="oinatalrn", caption_text="")
        dm.submit(d.draft_id)
        r = gate.batch_approve(limit=5)
        assert r["skipped"] == 1

    def test_respeita_limite(self, tmp_path):
        dm = _dm(tmp_path)
        gate = ApprovalGate(dm)
        for i in range(5):
            _create_valid_draft(dm, queue_id=f"q{i}")
        r = gate.batch_approve(limit=2)
        assert r["approved"] == 2

    def test_status_vira_approved_no_storage(self, tmp_path):
        dm = _dm(tmp_path)
        gate = ApprovalGate(dm)
        _create_valid_draft(dm)
        gate.batch_approve(limit=5)
        statuses = [d.status for d in dm.list_all()]
        assert all(s == DraftStatus.APPROVED for s in statuses)

    def test_batch_vazio_retorna_zero(self, tmp_path):
        dm = _dm(tmp_path)
        gate = ApprovalGate(dm)
        r = gate.batch_approve(limit=5)
        assert r["approved"] == 0
        assert r["skipped"] == 0

    def test_skip_reasons_populadas(self, tmp_path):
        dm = _dm(tmp_path)
        gate = ApprovalGate(dm)
        d = dm.create(queue_id="qZ", account_handle="oinatalrn", caption_text="")
        dm.submit(d.draft_id)
        r = gate.batch_approve(limit=5)
        assert len(r["skip_reasons"]) == 1


# ------------------------------------------------------------------
# Testes CLI — content approve --batch
# ------------------------------------------------------------------

class TestContentCLI:
    def test_content_help(self):
        result = runner.invoke(app, ["content", "--help"])
        assert result.exit_code == 0
        assert "approve" in result.output

    def test_approve_batch_sem_drafts(self, tmp_path, monkeypatch):
        """Batch sem drafts → saída indicando nenhum draft encontrado."""
        monkeypatch.setenv("OMNIS_ROOT", str(tmp_path))
        result = runner.invoke(app, ["content", "approve", "--batch"])
        assert result.exit_code == 0

    def test_content_status_sem_drafts(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OMNIS_ROOT", str(tmp_path))
        result = runner.invoke(app, ["content", "status"])
        assert result.exit_code == 0

    def test_content_list_executa_ok(self, tmp_path, monkeypatch):
        """content list roda sem crash — pode ter drafts reais no disco."""
        result = runner.invoke(app, ["content", "list"])
        assert result.exit_code == 0
        # Saída tem tabela com "Drafts" ou "Nenhum draft"
        assert "Drafts" in result.output or "Nenhum draft" in result.output

    def test_approve_id_invalido(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OMNIS_ROOT", str(tmp_path))
        result = runner.invoke(app, ["content", "approve", "draft_inexistente"])
        assert result.exit_code == 1

    def test_reject_sem_reason(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OMNIS_ROOT", str(tmp_path))
        result = runner.invoke(app, ["content", "reject", "algum_id"])
        # typer deve exigir --reason
        assert result.exit_code != 0
