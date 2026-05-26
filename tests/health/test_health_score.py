"""Testes — HealthScorer (WAVE 10).

Cobre: checks individuais, thresholds de cor, persistência,
       graceful quando serviços offline, anti-teatro.
"""
from __future__ import annotations

import json
import socket
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.health.score import HealthScorer, HealthScore, CheckResult


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_scorer(tmp_path: Path, persist: bool = False) -> HealthScorer:
    return HealthScorer(
        mission_log=tmp_path / "mission_runs.jsonl",
        agencia_output=tmp_path / "output" / "agencia",
        drafts_path=tmp_path / "caption_drafts.jsonl",
        health_log=tmp_path / "health_scores.jsonl",
        persist=persist,
    )


def _write_mission_run(log_path: Path, status: str = "success", command: str = "test") -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "run_id": "abc123", "command": command, "module": "test",
        "status": status,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 100, "inputs": {}, "outputs": {},
        "warnings": [], "errors": [], "metadata": {},
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _write_manifest(agencia_dir: Path, age_days: int = 0) -> None:
    agencia_dir.mkdir(parents=True, exist_ok=True)
    m = agencia_dir / "carrossel_test.manifest.json"
    m.write_text(json.dumps({"session_id": "s1", "slides": []}), encoding="utf-8")
    if age_days > 0:
        import os, time as t
        mtime = (datetime.now(timezone.utc) - timedelta(days=age_days)).timestamp()
        os.utime(m, (mtime, mtime))


def _write_draft(drafts_path: Path, status: str, count: int = 1) -> None:
    drafts_path.parent.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        d = {
            "draft_id": f"d{i}", "queue_id": "q1",
            "account_handle": "test", "caption_text": "texto",
            "hashtags": [], "cta": "", "status": status,
            "version": 1, "objective": "alcance", "format": "reel", "notes": "",
            "rejection_reason": None, "asset_id": None,
            "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
        }
        with drafts_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(d) + "\n")


# ------------------------------------------------------------------
# CheckResult
# ------------------------------------------------------------------

class TestCheckResult:
    def test_to_dict_tem_campos_esperados(self):
        cr = CheckResult("teste", 10, 20, "ok", "detalhe")
        d = cr.to_dict()
        assert d["name"] == "teste"
        assert d["score"] == 10
        assert d["max_score"] == 20
        assert d["status"] == "ok"
        assert d["detail"] == "detalhe"


# ------------------------------------------------------------------
# HealthScore
# ------------------------------------------------------------------

class TestHealthScore:
    def test_to_dict_estavel(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        hs = scorer.calculate()
        d = hs.to_dict()
        assert "score" in d
        assert "color" in d
        assert "checks" in d
        assert "generated_at" in d
        assert "warnings" in d

    def test_summary_contem_score(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        hs = scorer.calculate()
        s = hs.summary()
        assert str(hs.score) in s

    def test_summary_contem_checks(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        hs = scorer.calculate()
        s = hs.summary()
        assert "ollama" in s
        assert "mission-logger" in s


# ------------------------------------------------------------------
# Thresholds de cor
# ------------------------------------------------------------------

class TestThresholds:
    def test_score_100_e_verde(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        # Força todos checks como 'ok' com score máximo
        with patch.object(scorer, '_check_ollama',         return_value=CheckResult("o", 20, 20, "ok")), \
             patch.object(scorer, '_check_akasha_docker',   return_value=CheckResult("a", 15, 15, "ok")), \
             patch.object(scorer, '_check_drafts_pending',  return_value=CheckResult("d", 15, 15, "ok")), \
             patch.object(scorer, '_check_recent_content',  return_value=CheckResult("r", 20, 20, "ok")), \
             patch.object(scorer, '_check_mission_logger',  return_value=CheckResult("m", 10, 10, "ok")):
            hs = scorer.calculate()
        assert hs.score == 100
        assert hs.color == "green"

    def test_score_0_e_vermelho(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        with patch.object(scorer, '_check_ollama',         return_value=CheckResult("o", 0, 20, "fail")), \
             patch.object(scorer, '_check_akasha_docker',   return_value=CheckResult("a", 0, 15, "fail")), \
             patch.object(scorer, '_check_drafts_pending',  return_value=CheckResult("d", 0, 15, "fail")), \
             patch.object(scorer, '_check_recent_content',  return_value=CheckResult("r", 0, 20, "fail")), \
             patch.object(scorer, '_check_mission_logger',  return_value=CheckResult("m", 0, 10, "fail")):
            hs = scorer.calculate()
        assert hs.score == 0
        assert hs.color == "red"

    def test_score_50_e_amarelo(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        # 50pts em 80 total = ~62 → yellow (≥40 < 70)
        with patch.object(scorer, '_check_ollama',         return_value=CheckResult("o", 10, 20, "warn")), \
             patch.object(scorer, '_check_akasha_docker',   return_value=CheckResult("a", 8, 15, "warn")), \
             patch.object(scorer, '_check_drafts_pending',  return_value=CheckResult("d", 7, 15, "warn")), \
             patch.object(scorer, '_check_recent_content',  return_value=CheckResult("r", 10, 20, "warn")), \
             patch.object(scorer, '_check_mission_logger',  return_value=CheckResult("m", 5, 10, "warn")):
            hs = scorer.calculate()
        assert hs.color == "yellow"

    def test_threshold_verde_exato_70(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        # 70% de 80 = 56pts → score=70
        with patch.object(scorer, '_check_ollama',         return_value=CheckResult("o", 14, 20, "ok")), \
             patch.object(scorer, '_check_akasha_docker',   return_value=CheckResult("a", 10, 15, "ok")), \
             patch.object(scorer, '_check_drafts_pending',  return_value=CheckResult("d", 10, 15, "ok")), \
             patch.object(scorer, '_check_recent_content',  return_value=CheckResult("r", 14, 20, "ok")), \
             patch.object(scorer, '_check_mission_logger',  return_value=CheckResult("m", 8, 10, "ok")):
            hs = scorer.calculate()
        assert hs.score >= 70
        assert hs.color == "green"


# ------------------------------------------------------------------
# Check Ollama
# ------------------------------------------------------------------

class TestCheckOllama:
    def test_porta_aberta_retorna_ok(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        with patch("socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 0
            mock_sock_cls.return_value = mock_sock
            cr = scorer._check_ollama()
        assert cr.status == "ok"
        assert cr.score == cr.max_score

    def test_porta_fechada_retorna_fail(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        with patch("socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 111
            mock_sock_cls.return_value = mock_sock
            cr = scorer._check_ollama()
        assert cr.status == "fail"
        assert cr.score == 0

    def test_excecao_retorna_fail_gracioso(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        with patch("socket.socket", side_effect=OSError("no route")):
            cr = scorer._check_ollama()
        assert cr.status == "fail"
        assert cr.score == 0


# ------------------------------------------------------------------
# Check Akasha Docker
# ------------------------------------------------------------------

class TestCheckAkashaDocker:
    def test_container_running(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="running\n", returncode=0)
            cr = scorer._check_akasha_docker()
        assert cr.status == "ok"
        assert cr.score == cr.max_score

    def test_container_exited(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="exited\n", returncode=0)
            cr = scorer._check_akasha_docker()
        assert cr.status == "warn"
        assert cr.score == 0

    def test_docker_nao_instalado(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        with patch("subprocess.run", side_effect=FileNotFoundError("docker")):
            cr = scorer._check_akasha_docker()
        assert cr.status == "skip"
        assert cr.score == 0


# ------------------------------------------------------------------
# Check Drafts Pending
# ------------------------------------------------------------------

class TestCheckDraftsPending:
    def test_sem_arquivo_retorna_ok(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        cr = scorer._check_drafts_pending()
        assert cr.status == "ok"
        assert cr.score == cr.max_score

    def test_zero_pendentes_ok(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        _write_draft(tmp_path / "caption_drafts.jsonl", "approved")
        cr = scorer._check_drafts_pending()
        assert cr.status == "ok"

    def test_ate_5_pendentes_warn(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        _write_draft(tmp_path / "caption_drafts.jsonl", "needs_review", count=3)
        cr = scorer._check_drafts_pending()
        assert cr.status == "warn"
        assert 0 < cr.score < cr.max_score

    def test_mais_de_5_pendentes_fail(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        _write_draft(tmp_path / "caption_drafts.jsonl", "needs_review", count=6)
        cr = scorer._check_drafts_pending()
        assert cr.status == "fail"
        assert cr.score == 0


# ------------------------------------------------------------------
# Check Recent Content
# ------------------------------------------------------------------

class TestCheckRecentContent:
    def test_pasta_ausente_warn(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        cr = scorer._check_recent_content()
        assert cr.status == "warn"
        assert cr.score == 0

    def test_manifesto_recente_5plus_ok(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        out = tmp_path / "output" / "agencia"
        for i in range(5):
            sub = out / f"subdir{i}"
            sub.mkdir(parents=True, exist_ok=True)
            (sub / f"c{i}.manifest.json").write_text("{}", encoding="utf-8")
        cr = scorer._check_recent_content()
        assert cr.status == "ok"
        assert cr.score == cr.max_score

    def test_manifesto_recente_1a4_warn(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        out = tmp_path / "output" / "agencia"
        out.mkdir(parents=True, exist_ok=True)
        (out / "c1.manifest.json").write_text("{}", encoding="utf-8")
        cr = scorer._check_recent_content()
        assert cr.status == "warn"
        assert 0 < cr.score < cr.max_score

    def test_manifesto_antigo_fail(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        out = tmp_path / "output" / "agencia"
        _write_manifest(out, age_days=10)
        cr = scorer._check_recent_content()
        assert cr.status == "fail"
        assert cr.score == 0


# ------------------------------------------------------------------
# Check Mission Logger
# ------------------------------------------------------------------

class TestCheckMissionLogger:
    def test_sem_arquivo_warn(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        cr = scorer._check_mission_logger()
        assert cr.status == "warn"
        assert cr.score == 0

    def test_ultimo_run_success_ok(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        _write_mission_run(tmp_path / "mission_runs.jsonl", status="success")
        cr = scorer._check_mission_logger()
        assert cr.status == "ok"
        assert cr.score == cr.max_score

    def test_ultimo_run_error_warn(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        _write_mission_run(tmp_path / "mission_runs.jsonl", status="success")
        _write_mission_run(tmp_path / "mission_runs.jsonl", status="error")
        cr = scorer._check_mission_logger()
        assert cr.status == "warn"
        assert cr.score == 0


# ------------------------------------------------------------------
# Persistência
# ------------------------------------------------------------------

class TestPersistencia:
    def test_persiste_score(self, tmp_path):
        scorer = _make_scorer(tmp_path, persist=True)
        scorer.calculate()
        log = tmp_path / "health_scores.jsonl"
        assert log.exists()
        lines = [l for l in log.read_text().splitlines() if l.strip()]
        assert len(lines) == 1
        d = json.loads(lines[0])
        assert "score" in d
        assert "color" in d
        assert "date" in d

    def test_historico_leitura(self, tmp_path):
        scorer = _make_scorer(tmp_path, persist=True)
        scorer.calculate()
        scorer.calculate()
        history = scorer.read_history(limit=5)
        assert len(history) == 2

    def test_persist_false_nao_cria_arquivo(self, tmp_path):
        scorer = _make_scorer(tmp_path, persist=False)
        scorer.calculate()
        assert not (tmp_path / "health_scores.jsonl").exists()

    def test_historico_vazio_sem_arquivo(self, tmp_path):
        scorer = _make_scorer(tmp_path, persist=False)
        history = scorer.read_history()
        assert history == []


# ------------------------------------------------------------------
# Anti-teatro
# ------------------------------------------------------------------

class TestAntiTeatro:
    def test_score_reflete_checks_reais(self, tmp_path):
        """Score calculado deve bater com a soma dos checks retornados."""
        scorer = _make_scorer(tmp_path)
        hs = scorer.calculate()
        total = sum(c.score for c in hs.checks)
        max_t = sum(c.max_score for c in hs.checks)
        expected = round(total / max_t * 100) if max_t else 0
        assert hs.score == expected

    def test_color_e_score_consistentes(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        hs = scorer.calculate()
        if hs.score >= 70:
            assert hs.color == "green"
        elif hs.score >= 40:
            assert hs.color == "yellow"
        else:
            assert hs.color == "red"

    def test_warnings_refletem_checks_warn(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        # Sem arquivos → mission-logger = warn, recent-content = warn
        hs = scorer.calculate()
        warn_checks = [c for c in hs.checks if c.status == "warn"]
        # warnings list deve ter mesma qtd de itens (detail strings)
        assert len(hs.warnings) == len(warn_checks)

    def test_generated_at_e_utc_iso(self, tmp_path):
        scorer = _make_scorer(tmp_path)
        hs = scorer.calculate()
        # Deve parsear sem erro
        dt = datetime.fromisoformat(hs.generated_at.replace("Z", "+00:00"))
        assert dt.tzinfo is not None
