"""Tests for mission CLI commands."""
import pytest
from typer.testing import CliRunner
from pathlib import Path

from src.cli import app


@pytest.fixture
def runner():
    return CliRunner()


class TestMissionCLI:
    def test_mission_run_dry_run(self, runner, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.agentic.mission_engine.MISSIONS_ROOT",
            tmp_path,
        )
        result = runner.invoke(app, ["mission", "run", "cria campanha hotel"])
        assert result.exit_code == 0
        assert "DRY-RUN" in result.stdout
        assert "Entregáveis previstos" in result.stdout

    def test_mission_run_with_executar(self, runner, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.agentic.mission_engine.MISSIONS_ROOT",
            tmp_path,
        )
        result = runner.invoke(app, ["mission", "run", "--executar", "criar campanha hotel 7 dias"])
        assert result.exit_code == 0
        assert "Missão aberta:" in result.stdout
        # Verify mission folder was created
        mission_dirs = list(tmp_path.glob("MIS-*"))
        assert len(mission_dirs) == 1
        # Verify contract exists
        contract = mission_dirs[0] / "mission_contract.json"
        assert contract.exists()
        # Verify relatorio_final.md exists
        report = mission_dirs[0] / "relatorio_final.md"
        assert report.exists()

    def test_mission_run_with_setor(self, runner, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.agentic.mission_engine.MISSIONS_ROOT",
            tmp_path,
        )
        result = runner.invoke(app, ["mission", "run", "--executar", "--setor", "sales", "faz algo"])
        assert result.exit_code == 0
        mission_dirs = list(tmp_path.glob("MIS-*"))
        assert len(mission_dirs) == 1
        import json
        contract = json.loads((mission_dirs[0] / "mission_contract.json").read_text(encoding="utf-8"))
        assert contract["setor"] == "sales"

    def test_mission_list_empty(self, runner, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.agentic.mission_engine.MISSIONS_ROOT",
            tmp_path,
        )
        result = runner.invoke(app, ["mission", "list"])
        assert result.exit_code == 0
        assert "Nenhuma missão encontrada" in result.stdout

    def test_mission_list_with_missions(self, runner, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.agentic.mission_engine.MISSIONS_ROOT",
            tmp_path,
        )
        # Create a mission first
        runner.invoke(app, ["mission", "run", "--executar", "teste listagem"])
        result = runner.invoke(app, ["mission", "list"])
        assert result.exit_code == 0
        assert "MIS-" in result.stdout

    def test_mission_show_not_found(self, runner, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.agentic.mission_engine.MISSIONS_ROOT",
            tmp_path,
        )
        result = runner.invoke(app, ["mission", "show", "MIS-99999999-999"])
        assert result.exit_code == 1
        assert "não encontrada" in result.stdout

    def test_mission_show_found(self, runner, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.agentic.mission_engine.MISSIONS_ROOT",
            tmp_path,
        )
        exec_result = runner.invoke(app, ["mission", "run", "--executar", "mostrar missao"])
        assert exec_result.exit_code == 0
        import re
        m = re.search(r"(MIS-\d{8}-\d{3})", exec_result.stdout)
        assert m is not None
        mission_id = m.group(1)

        result = runner.invoke(app, ["mission", "show", mission_id])
        assert result.exit_code == 0
        assert mission_id in result.stdout
        assert "mostrar missao" in result.stdout

    def test_mission_close(self, runner, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.agentic.mission_engine.MISSIONS_ROOT",
            tmp_path,
        )
        exec_result = runner.invoke(app, ["mission", "run", "--executar", "missao para fechar"])
        assert exec_result.exit_code == 0
        import re
        m = re.search(r"(MIS-\d{8}-\d{3})", exec_result.stdout)
        mission_id = m.group(1)

        result = runner.invoke(app, ["mission", "close", mission_id])
        assert result.exit_code == 0
        assert "fechada" in result.stdout.lower()

    def test_mission_close_not_found(self, runner, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "src.agentic.mission_engine.MISSIONS_ROOT",
            tmp_path,
        )
        result = runner.invoke(app, ["mission", "close", "MIS-00000000-000"])
        assert result.exit_code == 1
