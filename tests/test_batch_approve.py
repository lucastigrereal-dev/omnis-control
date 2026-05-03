"""Testes do batch_approve — Fase Cockpit.

Cobre: aprovacao em lote, skip de placeholders, limit, zero drafts.
Adaptado ao padrao de test_caption_approval.py (DraftsManager + ApprovalGate).
"""

import os
import tempfile

import pytest

from src.caption_approval.drafts import DraftsManager
from src.caption_approval.approvals import ApprovalGate
from src.caption_approval.models import DraftStatus


@pytest.fixture
def tmp_drafts_path():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8") as f:
        path = f.name
    yield path
    if os.path.isfile(path):
        os.unlink(path)


@pytest.fixture
def tmp_log_path():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8") as f:
        path = f.name
    yield path
    if os.path.isfile(path):
        os.unlink(path)


@pytest.fixture
def dm(tmp_drafts_path, tmp_log_path):
    return DraftsManager(drafts_path=tmp_drafts_path, log_path=tmp_log_path)


@pytest.fixture
def gate(dm):
    return ApprovalGate(dm)


class TestBatchApprove:
    def _create_and_submit(self, dm, text="Texto valido para aprovacao com mais de 10 caracteres",
                           hashtags=None, cta="Compartilha!", account="lucastigrereal",
                           queue_id="q1"):
        d = dm.create(queue_id, account, caption_text=text,
                       hashtags=hashtags or ["#tag1", "#tag2", "#tag3"],
                       cta=cta)
        dm.submit(d.draft_id)
        return d

    def test_draft_valido_aprovado(self, dm, gate):
        """Draft valido -> aprovado."""
        self._create_and_submit(dm)
        result = gate.batch_approve(limit=5)
        assert result["approved"] == 1
        assert result["skipped"] == 0

    def test_draft_com_placeholder_skipped(self, dm, gate):
        """Draft com placeholder -> skipped com reason."""
        self._create_and_submit(dm, text="Texto com [TODO] revisar")
        result = gate.batch_approve(limit=5)
        assert result["approved"] == 0
        assert result["skipped"] == 1
        reasons = " ".join(result["skip_reasons"])
        assert "placeholder" in reasons.lower()

    def test_draft_sem_content_skipped(self, dm, gate):
        """Draft sem content -> skipped."""
        self._create_and_submit(dm, text="")
        result = gate.batch_approve(limit=5)
        assert result["approved"] == 0
        assert result["skipped"] == 1
        reasons = " ".join(result["skip_reasons"])
        assert "vazio" in reasons.lower()

    def test_limit_2_com_5_validos(self, dm, gate):
        """limit=2 com 5 validos -> 2 aprovados."""
        for i in range(5):
            self._create_and_submit(dm, text=f"Texto valido numero {i} com conteudo suficiente")
        result = gate.batch_approve(limit=2)
        assert result["approved"] == 2
        assert result["skipped"] == 0

    def test_zero_drafts(self, dm, gate):
        """Nenhum draft -> approved=0."""
        result = gate.batch_approve(limit=5)
        assert result["approved"] == 0
        assert result["skipped"] == 0

    def test_approved_gera_csv(self, dm, gate, tmp_path):
        """Aprovados geram arquivo approved_latest.csv."""
        self._create_and_submit(dm)
        result = gate.batch_approve(limit=5)
        assert result["approved"] == 1

        csv_path = os.path.expanduser("~/omnis-control/data/exports/approved_latest.csv")
        if os.path.isfile(csv_path):
            content = open(csv_path, encoding="utf-8").read()
            assert "lucastigrereal" in content

    def test_mistura_validos_e_invalidos(self, dm, gate):
        """Mistura de validos e invalidos -> aprova so os validos."""
        # 2 validos
        self._create_and_submit(dm, text="Primeiro texto valido com bastante conteudo", account="lucastigrereal")
        self._create_and_submit(dm, text="Segundo texto valido com bastante conteudo", account="afamiliatigrereal",
                                queue_id="q2")
        # 2 invalidos
        self._create_and_submit(dm, text="Com [REVISAR] aqui", queue_id="q3")
        self._create_and_submit(dm, text="", queue_id="q4")
        result = gate.batch_approve(limit=5)
        assert result["approved"] == 2
        assert result["skipped"] == 2
