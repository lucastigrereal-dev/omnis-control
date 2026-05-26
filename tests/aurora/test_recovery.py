"""Tests for AuroraRecovery — A2 fio mental (project_resume).

Cobertura:
  - save_checkpoint dry_run=True: retorna checkpoint, nao persiste
  - save_checkpoint dry_run=False: persiste em disco
  - load_last sem arquivo: None
  - load_last com checkpoints: retorna o mais recente
  - load_all: ordem cronologica
  - resume sem checkpoint: has_checkpoint=False, suggested_next nao vazio
  - resume com checkpoint: has_checkpoint=True, summary, suggested_next
  - to_dict() round-trip de checkpoint e resume
  - from_dict() round-trip
  - linha invalida em JSONL: ignorada, resto carregado
  - checkpoint_id gerado automaticamente
  - checkpoint_id custom aceito
  - metadata preservado
  - anti-teatro: next_action reflete o que foi gravado
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.aurora.recovery import AuroraRecovery, RecoveryCheckpoint, RecoveryResume


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_data(tmp_path: Path) -> Path:
    return tmp_path / "data"


@pytest.fixture
def rec_dry(tmp_data: Path) -> AuroraRecovery:
    """Recovery em dry_run=True (nao persiste em disco)."""
    return AuroraRecovery(dry_run=True, data_dir=tmp_data)


@pytest.fixture
def rec_real(tmp_data: Path) -> AuroraRecovery:
    """Recovery em dry_run=False (persiste em disco)."""
    return AuroraRecovery(dry_run=False, data_dir=tmp_data)


# ---------------------------------------------------------------------------
# 1. save_checkpoint — dry_run=True
# ---------------------------------------------------------------------------

class TestSaveCheckpointDryRun:
    def test_returns_checkpoint(self, rec_dry):
        ckpt = rec_dry.save_checkpoint(
            session_context="Implementando A2",
            last_action="Escreveu dataclasses",
            next_action="Escrever testes",
        )
        assert isinstance(ckpt, RecoveryCheckpoint)

    def test_does_not_persist(self, rec_dry, tmp_data):
        rec_dry.save_checkpoint("ctx", "last", "next")
        ckpt_path = tmp_data / "recovery_checkpoints.jsonl"
        assert not ckpt_path.exists()

    def test_checkpoint_id_generated(self, rec_dry):
        ckpt = rec_dry.save_checkpoint("ctx", "last", "next")
        assert ckpt.checkpoint_id and len(ckpt.checkpoint_id) == 8

    def test_checkpoint_id_custom(self, rec_dry):
        ckpt = rec_dry.save_checkpoint("ctx", "last", "next", checkpoint_id="custom42")
        assert ckpt.checkpoint_id == "custom42"

    def test_saved_at_iso(self, rec_dry):
        ckpt = rec_dry.save_checkpoint("ctx", "last", "next")
        assert ckpt.saved_at[:4].isdigit()

    def test_phase_preserved(self, rec_dry):
        ckpt = rec_dry.save_checkpoint("ctx", "last", "next", phase="A2")
        assert ckpt.phase == "A2"

    def test_metadata_preserved(self, rec_dry):
        ckpt = rec_dry.save_checkpoint("ctx", "last", "next", metadata={"wave": 3})
        assert ckpt.metadata["wave"] == 3


# ---------------------------------------------------------------------------
# 2. save_checkpoint — dry_run=False (persiste)
# ---------------------------------------------------------------------------

class TestSaveCheckpointReal:
    def test_persists_to_disk(self, rec_real, tmp_data):
        rec_real.save_checkpoint("ctx", "last", "next")
        ckpt_path = tmp_data / "recovery_checkpoints.jsonl"
        assert ckpt_path.exists()

    def test_creates_data_dir(self, tmp_path):
        non_existent = tmp_path / "novo_data"
        rec = AuroraRecovery(dry_run=False, data_dir=non_existent)
        rec.save_checkpoint("ctx", "last", "next")
        assert (non_existent / "recovery_checkpoints.jsonl").exists()

    def test_jsonl_is_valid(self, rec_real, tmp_data):
        rec_real.save_checkpoint("ctx A", "last A", "next A")
        rec_real.save_checkpoint("ctx B", "last B", "next B")
        ckpt_path = tmp_data / "recovery_checkpoints.jsonl"
        lines = [l for l in ckpt_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 2
        for line in lines:
            data = json.loads(line)
            assert "checkpoint_id" in data

    def test_append_not_overwrite(self, rec_real, tmp_data):
        rec_real.save_checkpoint("ctx 1", "last 1", "next 1")
        rec_real.save_checkpoint("ctx 2", "last 2", "next 2")
        ckpt_path = tmp_data / "recovery_checkpoints.jsonl"
        lines = [l for l in ckpt_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 2


# ---------------------------------------------------------------------------
# 3. load_last
# ---------------------------------------------------------------------------

class TestLoadLast:
    def test_none_when_no_file(self, rec_dry):
        assert rec_dry.load_last() is None

    def test_returns_most_recent(self, rec_real):
        rec_real.save_checkpoint("ctx A", "last A", "next A")
        rec_real.save_checkpoint("ctx B", "last B", "next B")
        last = rec_real.load_last()
        assert last is not None
        assert last.session_context == "ctx B"

    def test_returns_only_entry(self, rec_real):
        rec_real.save_checkpoint("unico", "last", "next")
        last = rec_real.load_last()
        assert last is not None
        assert last.session_context == "unico"


# ---------------------------------------------------------------------------
# 4. load_all
# ---------------------------------------------------------------------------

class TestLoadAll:
    def test_empty_when_no_file(self, rec_dry):
        assert rec_dry.load_all() == []

    def test_chronological_order(self, rec_real):
        for i in range(3):
            rec_real.save_checkpoint(f"ctx {i}", f"last {i}", f"next {i}")
        all_ckpts = rec_real.load_all()
        assert len(all_ckpts) == 3
        assert all_ckpts[0].session_context == "ctx 0"
        assert all_ckpts[-1].session_context == "ctx 2"

    def test_invalid_line_ignored(self, tmp_data):
        tmp_data.mkdir(parents=True, exist_ok=True)
        ckpt_path = tmp_data / "recovery_checkpoints.jsonl"
        ckpt_path.write_text(
            '{"checkpoint_id":"a1","saved_at":"2026-01-01","session_context":"ok",'
            '"last_action":"x","next_action":"y","phase":"","metadata":{}}\n'
            'LINHA_INVALIDA\n'
            '{"checkpoint_id":"b2","saved_at":"2026-01-02","session_context":"ok2",'
            '"last_action":"x2","next_action":"y2","phase":"","metadata":{}}\n',
            encoding="utf-8",
        )
        rec = AuroraRecovery(dry_run=True, data_dir=tmp_data)
        all_ckpts = rec.load_all()
        assert len(all_ckpts) == 2
        assert all_ckpts[0].checkpoint_id == "a1"
        assert all_ckpts[1].checkpoint_id == "b2"


# ---------------------------------------------------------------------------
# 5. resume()
# ---------------------------------------------------------------------------

class TestResume:
    def test_no_checkpoint_has_checkpoint_false(self, rec_dry):
        r = rec_dry.resume()
        assert isinstance(r, RecoveryResume)
        assert r.has_checkpoint is False

    def test_no_checkpoint_suggested_next_not_empty(self, rec_dry):
        r = rec_dry.resume()
        assert r.suggested_next  # nunca vazio

    def test_no_checkpoint_total_zero(self, rec_dry):
        r = rec_dry.resume()
        assert r.total_checkpoints == 0

    def test_with_checkpoint_has_checkpoint_true(self, rec_real):
        rec_real.save_checkpoint("ctx real", "last real", "next real", phase="A2")
        r = rec_real.resume()
        assert r.has_checkpoint is True

    def test_with_checkpoint_suggested_next_matches(self, rec_real):
        next_step = "Implementar metodo save_checkpoint com persistencia"
        rec_real.save_checkpoint("ctx", "last", next_step)
        r = rec_real.resume()
        assert r.suggested_next == next_step

    def test_with_checkpoint_summary_has_context(self, rec_real):
        rec_real.save_checkpoint(
            session_context="Retomada da sessao A2",
            last_action="Escreveu recovery.py",
            next_action="Escrever testes",
            phase="A2",
        )
        r = rec_real.resume()
        assert "Retomada da sessao A2" in r.summary

    def test_with_checkpoint_total_matches(self, rec_real):
        for i in range(4):
            rec_real.save_checkpoint(f"ctx {i}", f"last {i}", f"next {i}")
        r = rec_real.resume()
        assert r.total_checkpoints == 4


# ---------------------------------------------------------------------------
# 6. to_dict / from_dict round-trip
# ---------------------------------------------------------------------------

class TestToDict:
    def test_checkpoint_to_dict_has_keys(self, rec_dry):
        ckpt = rec_dry.save_checkpoint("ctx", "last", "next", phase="A2")
        d = ckpt.to_dict()
        for key in ("checkpoint_id", "saved_at", "session_context",
                    "last_action", "next_action", "phase", "metadata"):
            assert key in d

    def test_checkpoint_from_dict_roundtrip(self, rec_dry):
        ckpt = rec_dry.save_checkpoint(
            "contexto de teste", "acao anterior", "proxima acao", phase="A2",
            metadata={"info": "valor"},
        )
        restored = RecoveryCheckpoint.from_dict(ckpt.to_dict())
        assert restored.checkpoint_id == ckpt.checkpoint_id
        assert restored.session_context == "contexto de teste"
        assert restored.next_action == "proxima acao"
        assert restored.phase == "A2"
        assert restored.metadata == {"info": "valor"}

    def test_resume_to_dict_no_checkpoint(self, rec_dry):
        r = rec_dry.resume()
        d = r.to_dict()
        assert d["has_checkpoint"] is False
        assert d["checkpoint"] is None
        assert d["suggested_next"]

    def test_resume_to_dict_with_checkpoint(self, rec_real):
        rec_real.save_checkpoint("ctx", "last", "next to do")
        r = rec_real.resume()
        d = r.to_dict()
        assert d["has_checkpoint"] is True
        assert d["checkpoint"] is not None
        assert d["checkpoint"]["next_action"] == "next to do"


# ---------------------------------------------------------------------------
# 7. Anti-teatro
# ---------------------------------------------------------------------------

class TestAntiTeatro:
    def test_next_action_exact_match(self, rec_real):
        """O next_action gravado deve aparecer exatamente no resume."""
        expected = "Iniciar A3 guardrail.py — bloqueia acao perigosa"
        rec_real.save_checkpoint(
            session_context="Sessao A2 completa",
            last_action="Commitou recovery.py + 30 testes",
            next_action=expected,
            phase="A3",
        )
        r = rec_real.resume()
        assert r.suggested_next == expected
        assert expected in r.summary

    def test_multiple_saves_last_wins(self, rec_real):
        rec_real.save_checkpoint("ctx 1", "last 1", "proximo 1")
        rec_real.save_checkpoint("ctx 2", "last 2", "proximo 2")
        r = rec_real.resume()
        assert r.suggested_next == "proximo 2"

    def test_summary_line_readable(self, rec_dry):
        ckpt = rec_dry.save_checkpoint(
            session_context="Sessao em andamento",
            last_action="Gravou checkpoint",
            next_action="Retomar de onde parou",
            phase="A2",
        )
        line = ckpt.summary_line()
        assert "A2" in line
        assert "Gravou checkpoint" in line[:120] or "Retomar" in line
