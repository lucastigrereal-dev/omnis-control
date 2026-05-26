"""Testes — MissionLogger (WAVE 5).

Cobre: context manager, start/finish, add_input/output/warning,
       erro capturado, leitura de histórico, filtros, anti-teatro.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from src.mission_logger import MissionLogger, MissionRun


# ------------------------------------------------------------------
# Testes — context manager
# ------------------------------------------------------------------

class TestContextManager:
    def test_cria_run_ao_entrar(self, tmp_path):
        with MissionLogger("carrossel", log_path=tmp_path / "runs.jsonl", dry_run=True) as ml:
            assert ml.run is not None
            assert ml.run.command == "carrossel"

    def test_status_success_ao_sair_sem_erro(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        with MissionLogger("export", log_path=log_path) as ml:
            ml.add_output("files", 3)
        runs = MissionLogger.read_runs(log_path=log_path)
        assert len(runs) == 1
        assert runs[0].status == "success"

    def test_status_error_quando_excecao(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        try:
            with MissionLogger("batch", log_path=log_path) as ml:
                raise ValueError("simulando erro")
        except ValueError:
            pass
        runs = MissionLogger.read_runs(log_path=log_path)
        assert runs[0].status == "error"
        assert "ValueError" in runs[0].errors[0]

    def test_nao_suprime_excecao(self, tmp_path):
        with pytest.raises(RuntimeError):
            with MissionLogger("cmd", log_path=tmp_path / "r.jsonl") as ml:
                raise RuntimeError("deve propagar")

    def test_duration_ms_presente(self, tmp_path):
        """duration_ms deve ser um inteiro >= 0 (resolução do timer varia no Windows)."""
        log_path = tmp_path / "runs.jsonl"
        with MissionLogger("cmd", log_path=log_path) as ml:
            time.sleep(0.05)  # 50ms — mais que o tick mínimo do timer do Windows (~15ms)
        runs = MissionLogger.read_runs(log_path=log_path)
        assert isinstance(runs[0].duration_ms, int)
        assert runs[0].duration_ms >= 0

    def test_dry_run_nao_persiste(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        with MissionLogger("cmd", log_path=log_path, dry_run=True) as ml:
            ml.add_output("x", 1)
        assert not log_path.exists()


# ------------------------------------------------------------------
# Testes — builder API
# ------------------------------------------------------------------

class TestBuilderAPI:
    def test_add_input_salvo(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        with MissionLogger("carrossel", log_path=log_path) as ml:
            ml.add_input("perfil", "oinatalrn")
            ml.add_input("slides_count", 5)
        runs = MissionLogger.read_runs(log_path=log_path)
        assert runs[0].inputs["perfil"] == "oinatalrn"
        assert runs[0].inputs["slides_count"] == 5

    def test_add_output_salvo(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        with MissionLogger("export", log_path=log_path) as ml:
            ml.add_output("total_drafts", 3)
        runs = MissionLogger.read_runs(log_path=log_path)
        assert runs[0].outputs["total_drafts"] == 3

    def test_add_warning_salvo(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        with MissionLogger("wave", log_path=log_path) as ml:
            ml.add_warning("assets nao encontrados")
        runs = MissionLogger.read_runs(log_path=log_path)
        assert "assets nao encontrados" in runs[0].warnings

    def test_add_metadata(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        with MissionLogger("wave", log_path=log_path) as ml:
            ml.add_metadata("git_commit", "abc123")
        runs = MissionLogger.read_runs(log_path=log_path)
        assert runs[0].metadata["git_commit"] == "abc123"


# ------------------------------------------------------------------
# Testes — start/finish (sem context manager)
# ------------------------------------------------------------------

class TestStartFinish:
    def test_start_finish_success(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        ml = MissionLogger.start("carrossel", log_path=log_path)
        ml.add_output("slides", 5)
        run = ml.finish(status="success")
        assert run.status == "success"
        runs = MissionLogger.read_runs(log_path=log_path)
        assert len(runs) == 1

    def test_start_finish_error(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        ml = MissionLogger.start("cmd", log_path=log_path)
        run = ml.finish(status="error", error="timeout atingido")
        assert run.status == "error"
        assert "timeout" in run.errors[0]


# ------------------------------------------------------------------
# Testes — leitura de histórico
# ------------------------------------------------------------------

class TestHistorico:
    def test_multiplos_runs_salvos(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        for i in range(5):
            with MissionLogger(f"cmd{i}", log_path=log_path):
                pass
        runs = MissionLogger.read_runs(log_path=log_path)
        assert len(runs) == 5

    def test_ordem_mais_recente_primeiro(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        with MissionLogger("primeiro", log_path=log_path):
            pass
        with MissionLogger("segundo", log_path=log_path):
            pass
        runs = MissionLogger.read_runs(log_path=log_path)
        assert runs[0].command == "segundo"

    def test_filtro_por_command(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        with MissionLogger("carrossel", log_path=log_path):
            pass
        with MissionLogger("export", log_path=log_path):
            pass
        runs = MissionLogger.read_runs(log_path=log_path, command_filter="carrossel")
        assert all(r.command == "carrossel" for r in runs)

    def test_filtro_por_status(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        with MissionLogger("ok", log_path=log_path):
            pass
        try:
            with MissionLogger("fail", log_path=log_path):
                raise ValueError("x")
        except ValueError:
            pass
        runs = MissionLogger.read_runs(log_path=log_path, status_filter="error")
        assert len(runs) == 1
        assert runs[0].command == "fail"

    def test_limite_respeitado(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        for _ in range(10):
            with MissionLogger("cmd", log_path=log_path):
                pass
        runs = MissionLogger.read_runs(log_path=log_path, limit=3)
        assert len(runs) == 3

    def test_log_inexistente_retorna_vazio(self, tmp_path):
        runs = MissionLogger.read_runs(log_path=tmp_path / "nao_existe.jsonl")
        assert runs == []


# ------------------------------------------------------------------
# Anti-teatro
# ------------------------------------------------------------------

class TestAntiTeatro:
    def test_output_reflete_valor_real(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        VALOR_UNICO = "ANTI_TEATRO_WAVE5_MISSION_LOGGER"
        with MissionLogger("carrossel", log_path=log_path) as ml:
            ml.add_output("session_id", VALOR_UNICO)
        runs = MissionLogger.read_runs(log_path=log_path)
        assert runs[0].outputs["session_id"] == VALOR_UNICO

    def test_to_dict_round_trip(self, tmp_path):
        log_path = tmp_path / "runs.jsonl"
        with MissionLogger("export", module="agencia.export", log_path=log_path) as ml:
            ml.add_input("account", "oinatalrn")
            ml.add_output("total", 5)
        runs = MissionLogger.read_runs(log_path=log_path)
        d = runs[0].to_dict()
        assert d["command"] == "export"
        assert d["module"] == "agencia.export"
        assert d["inputs"]["account"] == "oinatalrn"
        assert d["outputs"]["total"] == 5
