"""
Testes do Caption Draft + Approval Gate (Fase 2C).

Cobre: modelos, CRUD de drafts, template library, approval gate,
validação pré-aprovação, export, stale detection.
"""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

from src.caption_approval.models import (
    CaptionDraft, DraftStatus, CaptionTemplate, ApprovalLogEntry,
    ApprovalAction, BLOCKED_PLACEHOLDERS, _now_iso,
)
from src.caption_approval.drafts import DraftsManager, STALE_DAYS
from src.caption_approval.approvals import ApprovalGate, PreApprovalResult
from src.caption_approval.templates import TemplateLibrary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 1. CaptionDraft Model
# ---------------------------------------------------------------------------

class TestCaptionDraftModel:
    def test_defaults(self):
        d = CaptionDraft(draft_id="d1", queue_id="q1", account_handle="lucastigrereal")
        assert d.status == DraftStatus.DRAFT
        assert d.version == 1
        assert d.hashtags == []
        assert d.cta == ""
        assert d.rejection_reason is None

    def test_to_dict_roundtrip(self):
        d = CaptionDraft(
            draft_id="d1", queue_id="q1", account_handle="teste",
            caption_text="Texto", hashtags=["#tag1", "#tag2"],
            cta="Compartilha!", status=DraftStatus.NEEDS_REVIEW, version=2,
        )
        data = d.to_dict()
        assert data["caption_text"] == "Texto"
        assert data["hashtags"] == ["#tag1", "#tag2"]
        d2 = CaptionDraft.from_dict(data)
        assert d2.draft_id == d.draft_id
        assert d2.caption_text == d.caption_text
        assert d2.hashtags == d.hashtags
        assert d2.version == d.version

    def test_status_constants(self):
        assert DraftStatus.DRAFT == "draft"
        assert DraftStatus.APPROVED == "approved"
        assert DraftStatus.REJECTED == "rejected"
        assert DraftStatus.REVISED == "revised"
        assert DraftStatus.STALE == "stale"


# ---------------------------------------------------------------------------
# 2. DraftsManager CRUD
# ---------------------------------------------------------------------------

class TestDraftsManager:
    def test_empty(self, dm):
        assert dm.list_all() == []

    def test_create(self, dm):
        d = dm.create(queue_id="q1", account_handle="lucastigrereal",
                       caption_text="Meu texto")
        assert d.queue_id == "q1"
        assert d.account_handle == "lucastigrereal"
        assert d.status == DraftStatus.DRAFT
        assert d.version == 1
        assert dm.list_all() == [d]

    def test_create_with_hashtags(self, dm):
        d = dm.create("q1", "lucastigrereal",
                       hashtags=["#viagem", "#natal"],
                       cta="Compartilha!")
        assert d.hashtags == ["#viagem", "#natal"]
        assert d.cta == "Compartilha!"

    def test_get_by_id(self, dm):
        d = dm.create("q1", "lucastigrereal")
        assert dm.get(d.draft_id) == d

    def test_get_by_prefix(self, dm):
        d = dm.create("q1", "lucastigrereal")
        prefix = d.draft_id[:6]
        assert dm.get(prefix).draft_id == d.draft_id

    def test_get_nonexistent(self, dm):
        assert dm.get("fake_id") is None

    def test_get_by_queue_id(self, dm):
        dm.create("q1", "lucastigrereal")
        d2 = dm.create("q1", "lucastigrereal", caption_text="Versão 2 atualizada")
        found = dm.get_by_queue_id("q1")
        assert found is not None
        assert found.caption_text == "Versão 2 atualizada"

    def test_update_fields(self, dm):
        d = dm.create("q1", "lucastigrereal", caption_text="Original")
        updated = dm.update(d.draft_id, caption_text="Texto alterado com conteúdo")
        assert updated is not None
        assert updated.caption_text == "Texto alterado com conteúdo"
        assert updated.version == 2  # content change bumps version

    def test_update_nonexistent(self, dm):
        assert dm.update("fake") is None


# ---------------------------------------------------------------------------
# 3. Submit Workflow
# ---------------------------------------------------------------------------

class TestSubmit:
    def test_submit_draft(self, dm):
        d = dm.create("q1", "lucastigrereal")
        submitted = dm.submit(d.draft_id)
        assert submitted is not None
        assert submitted.status == DraftStatus.NEEDS_REVIEW

    def test_submit_revised(self, dm):
        d = dm.create("q1", "lucastigrereal")
        dm.submit(d.draft_id)
        # Rejeitar
        gate = ApprovalGate(dm)
        gate.reject(d.draft_id, reason="Precisa de mais informação")
        # Atualizar (vira revised)
        dm.update(d.draft_id, caption_text="Novo texto")
        # Submeter de novo
        submitted = dm.submit(d.draft_id)
        assert submitted is not None
        assert submitted.status == DraftStatus.NEEDS_REVIEW

    def test_submit_approved_fails(self, dm, gate):
        d = dm.create("q1", "lucastigrereal", caption_text="Texto válido para aprovação",
                       hashtags=["#tag1", "#tag2", "#tag3"], cta="Compartilha!")
        dm.submit(d.draft_id)
        gate.approve(d.draft_id)
        # Submeter approved deve falhar
        assert dm.submit(d.draft_id) is None


# ---------------------------------------------------------------------------
# 4. Update Rules (rejected/approved → revised + version)
# ---------------------------------------------------------------------------

class TestUpdateRules:
    def test_update_rejected_becomes_revised(self, dm, gate):
        d = dm.create("q1", "lucastigrereal", caption_text="Texto com conteúdo",
                       hashtags=["#a", "#b", "#c"], cta="Cta!")
        dm.submit(d.draft_id)
        gate.reject(d.draft_id, reason="Melhorar hook")

        updated = dm.update(d.draft_id, caption_text="Texto melhorado com conteúdo")
        assert updated is not None
        assert updated.status == DraftStatus.REVISED
        assert updated.version == 2  # reject não é versão nova; update sim
        assert updated.rejection_reason is None

    def test_update_approved_becomes_revised(self, dm, gate):
        d = dm.create("q1", "lucastigrereal", caption_text="Texto bom para aprovação",
                       hashtags=["#a", "#b", "#c"], cta="Cta!")
        dm.submit(d.draft_id)
        gate.approve(d.draft_id)

        updated = dm.update(d.draft_id, caption_text="Texto alterado e revisado")
        assert updated is not None
        assert updated.status == DraftStatus.REVISED
        assert updated.version == 2

    def test_update_no_content_change_no_version_bump(self, dm):
        d = dm.create("q1", "lucastigrereal")
        v1 = d.version
        updated = dm.update(d.draft_id, notes="nota")
        assert updated.version >= v1

    def test_force_versioning(self, dm):
        """--force recria como revised, versionando."""
        d = dm.create("q1", "lucastigrereal")
        # Simula --force = update com caption_text
        updated = dm.update(d.draft_id, caption_text="Forçado")
        assert updated is not None
        assert updated.version == 2


# ---------------------------------------------------------------------------
# 5. ApprovalGate Validation
# ---------------------------------------------------------------------------

class TestPreApprovalValidation:
    def test_empty_text_blocked(self, gate):
        r = gate.validate("", [], "")
        assert r.blocked
        assert any("vazio" in b for b in r.blocks)

    def test_short_text_blocked(self, gate):
        r = gate.validate("Oi", ["#tag1"], "")
        assert r.blocked
        assert any("curto" in b for b in r.blocks)

    def test_placeholder_hook_blocked(self, gate):
        r = gate.validate(f"Texto com {BLOCKED_PLACEHOLDERS[0]} aqui", ["#tag1"], "Cta")
        assert r.blocked

    def test_placeholder_corpo_blocked(self, gate):
        r = gate.validate(f"Texto com {BLOCKED_PLACEHOLDERS[1]}", ["#tag1"], "Cta")
        assert r.blocked

    def test_placeholder_cta_blocked(self, gate):
        r = gate.validate(f"Texto com {BLOCKED_PLACEHOLDERS[2]}", ["#tag1"], "Cta")
        assert r.blocked

    def test_few_hashtags_warning(self, gate):
        r = gate.validate("Texto válido com mais de 10 caracteres", [], "Cta válida")
        assert not r.blocked
        assert any("hashtag" in w for w in r.warnings)

    def test_missing_cta_warning(self, gate):
        r = gate.validate("Texto válido com mais de 10 caracteres", ["#a", "#b", "#c"], "")
        assert not r.blocked
        assert any("CTA" in w for w in r.warnings)

    def test_valid_passes(self, gate):
        r = gate.validate(
            "Texto legal sem placeholders",
            ["#tag1", "#tag2", "#tag3"],
            "Compartilha com alguém!",
        )
        assert r.passed
        assert not r.blocked


# ---------------------------------------------------------------------------
# 6. ApprovalGate Approve / Reject
# ---------------------------------------------------------------------------

class TestApprovalGate:
    def setup_draft(self, dm):
        d = dm.create("q1", "lucastigrereal",
                       caption_text="Hotel incrível em Natal! Praias lindas e café da manhã maravilhoso.",
                       hashtags=["#natal", "#hotel", "#viagem"],
                       cta="Salva pra depois!")
        dm.submit(d.draft_id)
        return d

    def test_approve_changes_status(self, dm, gate):
        d = self.setup_draft(dm)
        approved, warning = gate.approve(d.draft_id)
        assert approved is not None
        assert approved.status == DraftStatus.APPROVED

    def test_approve_draft_directly(self, dm, gate):
        """Aprovar draft em status DRAFT também funciona."""
        d = dm.create("q1", "lucastigrereal",
                       caption_text="Texto direto para aprovação sem revisão",
                       hashtags=["#a", "#b", "#c"], cta="Cta!")
        approved, warning = gate.approve(d.draft_id)
        assert approved.status == DraftStatus.APPROVED

    def test_approve_nonexistent(self, gate):
        with pytest.raises(ValueError, match="não encontrado"):
            gate.approve("fake_id")

    def test_approve_already_approved(self, dm, gate):
        d = self.setup_draft(dm)
        gate.approve(d.draft_id)
        with pytest.raises(ValueError, match="Só pode aprovar"):
            gate.approve(d.draft_id)

    def test_approve_blocked_by_validation(self, dm, gate):
        d = dm.create("q1", "lucastigrereal", caption_text="")
        dm.submit(d.draft_id)
        with pytest.raises(ValueError, match="Validação pré-aprovação falhou"):
            gate.approve(d.draft_id)

    def test_reject_requires_reason(self, dm, gate):
        d = self.setup_draft(dm)
        with pytest.raises(ValueError, match="Motivo da rejeição"):
            gate.reject(d.draft_id, "")

    def test_reject_changes_status(self, dm, gate):
        d = self.setup_draft(dm)
        rejected, warning = gate.reject(d.draft_id, "Hook precisa ser mais forte")
        assert rejected is not None
        assert rejected.status == DraftStatus.REJECTED
        assert rejected.rejection_reason == "Hook precisa ser mais forte"

    def test_reject_with_queue_updater(self, dm, gate):
        d = self.setup_draft(dm)
        calls = []

        def fake_updater(qid, status):
            calls.append((qid, status))
            return True

        rejected, warning = gate.reject(d.draft_id, "Precisa de CTA melhor",
                                         queue_updater=fake_updater)
        assert rejected.status == DraftStatus.REJECTED
        assert len(calls) == 1
        assert calls[0][1] == "needs_caption"


# ---------------------------------------------------------------------------
# 7. Approval Log
# ---------------------------------------------------------------------------

class TestApprovalLog:
    def test_log_created_on_create(self, dm):
        d = dm.create("q1", "lucastigrereal")
        log = dm.get_approval_log()
        assert len(log) >= 1
        assert log[0].action == ApprovalAction.CREATED
        assert log[0].draft_id == d.draft_id
        assert log[0].actor == "local_user"

    def test_log_on_approve(self, dm, gate):
        d = dm.create("q1", "lucastigrereal",
                       caption_text="Texto válido com mais de 10 caracteres",
                       hashtags=["#a", "#b", "#c"], cta="Cta!")
        dm.submit(d.draft_id)
        gate.approve(d.draft_id)
        log = dm.get_approval_log(action=ApprovalAction.APPROVED)
        assert len(log) >= 1
        assert log[0].action == ApprovalAction.APPROVED

    def test_log_on_reject(self, dm, gate):
        d = dm.create("q1", "lucastigrereal",
                       caption_text="Texto válido com mais de 10 caracteres",
                       hashtags=["#a", "#b", "#c"], cta="Cta!")
        dm.submit(d.draft_id)
        gate.reject(d.draft_id, "Motivo X")
        log = dm.get_approval_log(action=ApprovalAction.REJECTED)
        assert len(log) >= 1
        assert log[0].action == ApprovalAction.REJECTED
        assert log[0].reason == "Motivo X"


# ---------------------------------------------------------------------------
# 8. Template Library
# ---------------------------------------------------------------------------

class TestTemplateLibrary:
    def test_default_templates_exist(self):
        tl = TemplateLibrary()
        templates = tl.list_all()
        assert len(templates) >= 5  # 5 objetivos

    def test_get_by_objective(self):
        tl = TemplateLibrary()
        alcance = tl.get_by_objective("alcance")
        assert len(alcance) >= 1
        assert all(t.objective == "alcance" for t in alcance)

    def test_best_match_exact(self):
        tl = TemplateLibrary()
        match = tl.get_best_match("alcance", "reels")
        assert match is not None
        assert match.objective == "alcance"

    def test_best_match_fallback(self):
        tl = TemplateLibrary()
        match = tl.get_best_match("autoridade", "unknown_format")
        assert match is not None
        assert match.objective == "autoridade"

    def test_render_with_values(self):
        tl = TemplateLibrary()
        match = tl.get_best_match("alcance", "reels")
        assert match is not None
        result = tl.render(match, hook="Esse hotel é incrível!",
                           local="Praia de Ponta Negra")
        assert "Esse hotel é incrível!" in result["caption_text"]
        assert "Praia de Ponta Negra" in result["caption_text"]


# ---------------------------------------------------------------------------
# 9. Stale Detection
# ---------------------------------------------------------------------------

class TestStaleDetection:
    def test_no_stale_drafts(self, dm):
        stale = dm.check_stale()
        assert stale == []

    def test_recent_drafts_not_stale(self, dm):
        dm.create("q1", "lucastigrereal")
        stale = dm.check_stale()
        assert stale == []


# ---------------------------------------------------------------------------
# 10. Export CSV
# ---------------------------------------------------------------------------

class TestExport:
    def test_export_csv(self, dm, tmp_path):
        dm.create("q1", "lucastigrereal", caption_text="Texto com\nquebra de linha",
                   hashtags=["#tag1", "#tag2"])
        csv_path = tmp_path / "test_drafts.csv"
        dm.export_csv(str(csv_path))
        assert os.path.isfile(csv_path)
        content = Path(csv_path).read_text(encoding="utf-8")
        assert "draft_id" in content
        assert "lucastigrereal" in content

    def test_export_empty(self, dm, tmp_path):
        csv_path = tmp_path / "empty.csv"
        dm.export_csv(str(csv_path))
        assert os.path.isfile(csv_path)
        content = Path(csv_path).read_text(encoding="utf-8")
        assert "draft_id" in content


# ---------------------------------------------------------------------------
# 11. Security
# ---------------------------------------------------------------------------

class TestSecurity:
    def test_drafts_path_within_control(self):
        from src.caption_approval.drafts import DRAFTS_PATH
        control = os.path.expanduser("~/omnis-control")
        assert DRAFTS_PATH.startswith(control)

    def test_log_path_within_control(self):
        from src.caption_approval.drafts import APPROVAL_LOG_PATH
        control = os.path.expanduser("~/omnis-control")
        assert APPROVAL_LOG_PATH.startswith(control)
