"""Testes — PerformanceReporter (WAVE 8).

Cobre: fontes ausentes, geração com dados reais via tmp_path,
       command_stats, anti-teatro (dados refletem no relatório).
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

from src.agencia.performance_report import PerformanceReporter, PerformanceReport


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _write_mission_run(log_path: Path, command: str, status: str = "success", dur_ms: int = 50) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "run_id": "test1234",
        "command": command,
        "module": "test",
        "status": status,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": dur_ms,
        "inputs": {}, "outputs": {}, "warnings": [], "errors": [], "metadata": {},
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _write_carrossel_manifest(output_dir: Path, slides: int = 5) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "session_id": "sess01",
        "perfil": "oinatalrn",
        "slides": [f"slide{i}.png" for i in range(slides)],
        "thumbnail": "thumb.png",
        "output_dir": str(output_dir),
        "dry_run": True,
        "slides_count": slides,
        "metadata": {},
    }
    (output_dir / "carrossel_sess01.manifest.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


def _write_clip_manifest(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {"dry_run": True, "video_path": "v.mp4", "start": 0, "end": 5,
            "output_path": "clip.mp4", "duration": 5, "preset_name": "reel"}
    (output_dir / "clip_001.manifest.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


def _write_export_manifest(exports_dir: Path) -> None:
    sub = exports_dir / "2026-05-26-test"
    sub.mkdir(parents=True, exist_ok=True)
    data = {"export_id": "test", "total_drafts": 1, "dry_run": True}
    (sub / "manifest.json").write_text(json.dumps(data), encoding="utf-8")


def _write_draft(drafts_path: Path, status: str) -> None:
    drafts_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"draft_id": "abc", "queue_id": "q1", "account_handle": "oinatalrn",
            "caption_text": "texto", "hashtags": [], "cta": "", "status": status,
            "version": 1, "objective": "alcance", "format": "reel", "notes": "",
            "rejection_reason": None, "asset_id": None,
            "created_at": "2026-05-26T00:00:00Z", "updated_at": "2026-05-26T00:00:00Z"}
    with drafts_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")


# ------------------------------------------------------------------
# Testes — sem dados (graceful)
# ------------------------------------------------------------------

class TestSemDados:
    def test_gera_sem_crash_quando_arquivos_ausentes(self, tmp_path):
        reporter = PerformanceReporter(
            mission_log=tmp_path / "runs.jsonl",
            agencia_output=tmp_path / "output",
            exports_dir=tmp_path / "exports",
            drafts_path=tmp_path / "drafts.jsonl",
        )
        report = reporter.generate(period_days=7)
        assert isinstance(report, PerformanceReport)

    def test_total_runs_zero(self, tmp_path):
        reporter = PerformanceReporter(mission_log=tmp_path / "runs.jsonl")
        report = reporter.generate()
        assert report.total_runs == 0

    def test_cost_sempre_zero(self, tmp_path):
        reporter = PerformanceReporter(mission_log=tmp_path / "runs.jsonl")
        report = reporter.generate()
        assert report.cost_brl == 0.0

    def test_to_dict_retorna_estrutura_esperada(self, tmp_path):
        reporter = PerformanceReporter(mission_log=tmp_path / "runs.jsonl")
        report = reporter.generate()
        d = report.to_dict()
        assert "total_runs" in d
        assert "clips_generated" in d
        assert "carrosseis_generated" in d
        assert "cost_brl" in d
        assert "productivity_score" in d

    def test_summary_contem_periodo(self, tmp_path):
        reporter = PerformanceReporter(mission_log=tmp_path / "runs.jsonl")
        report = reporter.generate(period_days=14)
        s = report.summary()
        assert "14" in s

    def test_warning_quando_sem_runs(self, tmp_path):
        reporter = PerformanceReporter(mission_log=tmp_path / "runs.jsonl")
        report = reporter.generate()
        assert any("run" in w.lower() for w in report.warnings)


# ------------------------------------------------------------------
# Testes — com dados reais
# ------------------------------------------------------------------

class TestComDados:
    def test_conta_mission_runs(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_mission_run(log, "carrossel")
        _write_mission_run(log, "export")
        _write_mission_run(log, "carrossel", status="error")
        reporter = PerformanceReporter(mission_log=log)
        report = reporter.generate()
        assert report.total_runs == 3

    def test_command_stats_correto(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_mission_run(log, "carrossel", dur_ms=100)
        _write_mission_run(log, "carrossel", dur_ms=200)
        reporter = PerformanceReporter(mission_log=log)
        report = reporter.generate()
        cs = next(c for c in report.command_stats if c.command == "carrossel")
        assert cs.total == 2
        assert cs.success == 2
        assert cs.avg_duration_ms == 150.0

    def test_conta_carrosseis(self, tmp_path):
        out = tmp_path / "output"
        _write_carrossel_manifest(out / "oinatalrn" / "2026-05-26", slides=5)
        reporter = PerformanceReporter(agencia_output=out, mission_log=tmp_path / "r.jsonl")
        report = reporter.generate()
        assert report.carrosseis_generated == 1
        assert report.slides_total == 5

    def test_conta_clips(self, tmp_path):
        out = tmp_path / "output"
        _write_clip_manifest(out / "oinatalrn" / "2026-05-26")
        _write_clip_manifest(out / "lucastigrereal" / "2026-05-26")
        reporter = PerformanceReporter(agencia_output=out, mission_log=tmp_path / "r.jsonl")
        report = reporter.generate()
        assert report.clips_generated == 2

    def test_conta_exports(self, tmp_path):
        _write_export_manifest(tmp_path / "exports")
        reporter = PerformanceReporter(exports_dir=tmp_path / "exports", mission_log=tmp_path / "r.jsonl")
        report = reporter.generate()
        assert report.exports_done == 1

    def test_conta_drafts_aprovados(self, tmp_path):
        dp = tmp_path / "drafts.jsonl"
        _write_draft(dp, "approved")
        _write_draft(dp, "approved")
        _write_draft(dp, "needs_review")
        reporter = PerformanceReporter(drafts_path=dp, mission_log=tmp_path / "r.jsonl")
        report = reporter.generate()
        assert report.drafts_approved == 2
        assert report.drafts_pending == 1

    def test_productivity_score_maior_com_mais_atividade(self, tmp_path):
        # Totalmente isolado — sem dados
        empty_dir = tmp_path / "empty"
        reporter_empty = PerformanceReporter(
            mission_log=empty_dir / "runs.jsonl",
            agencia_output=empty_dir / "output",
            exports_dir=empty_dir / "exports",
            drafts_path=empty_dir / "drafts.jsonl",
        )
        report_empty = reporter_empty.generate()

        # Com atividade — todas fontes via tmp_path
        log = tmp_path / "runs.jsonl"
        _write_mission_run(log, "carrossel")
        out = tmp_path / "output"
        _write_carrossel_manifest(out / "oinatalrn" / "2026-05-26", slides=3)
        reporter_full = PerformanceReporter(
            mission_log=log,
            agencia_output=out,
            exports_dir=empty_dir / "exports",
            drafts_path=empty_dir / "drafts.jsonl",
        )
        report_full = reporter_full.generate()

        assert report_full.productivity_score > report_empty.productivity_score


# ------------------------------------------------------------------
# Anti-teatro
# ------------------------------------------------------------------

class TestAntiTeatro:
    def test_slides_refletem_valor_real(self, tmp_path):
        out = tmp_path / "output"
        _write_carrossel_manifest(out / "oinatalrn" / "2026-05-26", slides=7)
        reporter = PerformanceReporter(agencia_output=out, mission_log=tmp_path / "r.jsonl")
        report = reporter.generate()
        assert report.slides_total == 7

    def test_manifest_to_dict_round_trip(self, tmp_path):
        log = tmp_path / "runs.jsonl"
        _write_mission_run(log, "ANTI_TEATRO_W8")
        reporter = PerformanceReporter(mission_log=log)
        report = reporter.generate()
        d = report.to_dict()
        cmd_names = [c["command"] for c in d["command_stats"]]
        assert "ANTI_TEATRO_W8" in cmd_names
