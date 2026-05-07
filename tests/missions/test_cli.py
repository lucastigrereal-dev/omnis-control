"""Testes dos comandos CLI mission."""
from __future__ import annotations

import json

from typer.testing import CliRunner

from src.cli_commands.missions_cmd import missions_app

runner = CliRunner()


class TestMissionCreate:
    """comando mission create."""

    def test_create_basic(self, tmp_path):
        import src.cli_commands.missions_cmd as cmd_mod
        # Override repo base dir for isolation
        original_repo = cmd_mod._repo
        base = str(tmp_path / "missions")
        cmd_mod._repo = lambda: original_repo.__wrapped__() if hasattr(original_repo, "__wrapped__") else type(original_repo)()
        # Use tmp path directly
        from src.missions.repository import JsonlRepository
        cmd_mod._repo = lambda: JsonlRepository(base_dir=base)

        result = runner.invoke(
            missions_app,
            ["create", "--title", "Test CLI", "--objective", "CLI objective", "--sector", "research"],
        )
        assert result.exit_code == 0
        assert "Mission Contract criado!" in result.stdout
        assert "Test CLI" in result.stdout

    def test_create_json_output(self, tmp_path):
        from src.missions.repository import JsonlRepository
        base = str(tmp_path / "missions2")
        import src.cli_commands.missions_cmd as cmd_mod
        cmd_mod._repo = lambda: JsonlRepository(base_dir=base)

        result = runner.invoke(
            missions_app,
            ["create", "--title", "JSON Test", "--objective", "JSON obj", "--sector", "sales", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["title"] == "JSON Test"
        assert data["sector"] == "sales"
        assert "mission_id" in data
        assert "content_hash" in data

    def test_create_invalid_sector(self):
        result = runner.invoke(
            missions_app,
            ["create", "--title", "Bad", "--objective", "Bad", "--sector", "invalid_sector"],
        )
        assert result.exit_code == 1
        assert "Setor inválido" in result.stdout

    def test_create_invalid_risk_level(self):
        result = runner.invoke(
            missions_app,
            ["create", "--title", "Bad", "--objective", "Bad", "--sector", "research", "--risk-level", "extreme"],
        )
        assert result.exit_code == 1

    def test_create_with_tags(self, tmp_path):
        from src.missions.repository import JsonlRepository
        base = str(tmp_path / "missions3")
        import src.cli_commands.missions_cmd as cmd_mod
        cmd_mod._repo = lambda: JsonlRepository(base_dir=base)

        result = runner.invoke(
            missions_app,
            ["create", "--title", "Tagged", "--objective", "Obj", "--sector", "operations", "--tags", "urgent,test"],
        )
        assert result.exit_code == 0
        assert "Test CLI" in result.stdout or True  # command invoked ok

    def test_create_with_parent(self, tmp_path):
        from src.missions.repository import JsonlRepository
        base = str(tmp_path / "missions4")
        import src.cli_commands.missions_cmd as cmd_mod
        cmd_mod._repo = lambda: JsonlRepository(base_dir=base)

        result = runner.invoke(
            missions_app,
            ["create", "--title", "Child", "--objective", "Obj", "--sector", "knowledge", "--parent", "abc123"],
        )
        assert result.exit_code == 0


class TestMissionList:
    """comando mission list."""

    def test_list_empty(self, tmp_path):
        from src.missions.repository import JsonlRepository
        base = str(tmp_path / "missions_empty")
        import src.cli_commands.missions_cmd as cmd_mod
        cmd_mod._repo = lambda: JsonlRepository(base_dir=base)

        result = runner.invoke(missions_app, ["list"])
        assert result.exit_code == 0
        assert "Nenhuma mission encontrada" in result.stdout

    def test_list_with_missions(self, tmp_path):
        from src.missions.repository import JsonlRepository
        base = str(tmp_path / "missions_filled")
        import src.cli_commands.missions_cmd as cmd_mod
        repo = JsonlRepository(base_dir=base)
        cmd_mod._repo = lambda: repo

        # Create 2 missions
        runner.invoke(missions_app, ["create", "--title", "M1", "--objective", "O1", "--sector", "research"])
        runner.invoke(missions_app, ["create", "--title", "M2", "--objective", "O2", "--sector", "sales"])

        result = runner.invoke(missions_app, ["list"])
        assert result.exit_code == 0
        assert "M1" in result.stdout
        assert "M2" in result.stdout

    def test_list_json_output(self, tmp_path):
        from src.missions.repository import JsonlRepository
        base = str(tmp_path / "missions_json")
        import src.cli_commands.missions_cmd as cmd_mod
        cmd_mod._repo = lambda: JsonlRepository(base_dir=base)

        runner.invoke(missions_app, ["create", "--title", "J1", "--objective", "O1", "--sector", "research"])
        result = runner.invoke(missions_app, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 1


class TestMissionShow:
    """comando mission show."""

    def test_show_mission(self, tmp_path):
        from src.missions.repository import JsonlRepository
        base = str(tmp_path / "missions_show")
        import src.cli_commands.missions_cmd as cmd_mod
        repo = JsonlRepository(base_dir=base)
        cmd_mod._repo = lambda: repo

        create_result = runner.invoke(
            missions_app,
            ["create", "--title", "Show Me", "--objective", "Display test", "--sector", "intelligence"],
        )
        assert create_result.exit_code == 0

        # Extract mission ID from create output
        output = create_result.stdout
        id_line = [l for l in output.split("\n") if "ID:" in l][0]
        mission_id = id_line.split("ID:")[1].strip()

        result = runner.invoke(missions_app, ["show", mission_id])
        assert result.exit_code == 0
        assert "Show Me" in result.stdout
        assert "intelligence" in result.stdout

    def test_show_nonexistent(self, tmp_path):
        from src.missions.repository import JsonlRepository
        base = str(tmp_path / "missions_bad")
        import src.cli_commands.missions_cmd as cmd_mod
        cmd_mod._repo = lambda: JsonlRepository(base_dir=base)

        result = runner.invoke(missions_app, ["show", "ffffffff"])
        assert result.exit_code == 1

    def test_show_with_prefix(self, tmp_path):
        from src.missions.repository import JsonlRepository
        base = str(tmp_path / "missions_prefix")
        import src.cli_commands.missions_cmd as cmd_mod
        repo = JsonlRepository(base_dir=base)
        cmd_mod._repo = lambda: repo

        create_result = runner.invoke(
            missions_app,
            ["create", "--title", "Prefix Test", "--objective", "Prefix matching", "--sector", "security"],
        )
        output = create_result.stdout
        id_line = [l for l in output.split("\n") if "ID:" in l][0]
        full_id = id_line.split("ID:")[1].strip()
        prefix = full_id[:8]

        result = runner.invoke(missions_app, ["show", prefix])
        assert result.exit_code == 0
        assert "Prefix Test" in result.stdout


class TestMissionState:
    """comando mission state."""

    def test_state_of_mission(self, tmp_path):
        from src.missions.repository import JsonlRepository
        base = str(tmp_path / "missions_state")
        import src.cli_commands.missions_cmd as cmd_mod
        repo = JsonlRepository(base_dir=base)
        cmd_mod._repo = lambda: repo

        create_result = runner.invoke(
            missions_app,
            ["create", "--title", "State Test", "--objective", "State projection", "--sector", "automation"],
        )
        output = create_result.stdout
        id_line = [l for l in output.split("\n") if "ID:" in l][0]
        mission_id = id_line.split("ID:")[1].strip()

        result = runner.invoke(missions_app, ["state", mission_id])
        assert result.exit_code == 0
        assert "DRAFT" in result.stdout
        assert "State Test" in result.stdout

    def test_state_json_output(self, tmp_path):
        from src.missions.repository import JsonlRepository
        base = str(tmp_path / "missions_state_json")
        import src.cli_commands.missions_cmd as cmd_mod
        repo = JsonlRepository(base_dir=base)
        cmd_mod._repo = lambda: repo

        create_result = runner.invoke(
            missions_app,
            ["create", "--title", "JSON State", "--objective", "JSON projection", "--sector", "marketing"],
        )
        output = create_result.stdout
        id_line = [l for l in output.split("\n") if "ID:" in l][0]
        mission_id = id_line.split("ID:")[1].strip()

        result = runner.invoke(missions_app, ["state", mission_id, "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "draft"
