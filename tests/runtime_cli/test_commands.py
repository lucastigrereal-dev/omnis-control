from src.runtime_cli.commands import run_command, list_commands


class TestCommands:
    def test_status(self):
        result = run_command("status")
        assert result["ok"] is True
        assert result["health"] == "HEALTHY"

    def test_briefing(self):
        result = run_command("briefing")
        assert result["ok"] is True

    def test_approve_with_id(self):
        result = run_command("approve", {"request_id": "apr_1"})
        assert result["ok"] is True
        assert result["action"] == "APPROVED"

    def test_approve_without_id(self):
        result = run_command("approve")
        assert result["ok"] is False

    def test_reject_with_id(self):
        result = run_command("reject", {"request_id": "apr_2", "reason": "unsafe"})
        assert result["ok"] is True
        assert result["action"] == "REJECTED"

    def test_pending(self):
        result = run_command("pending")
        assert result["ok"] is True
        assert result["pending_count"] == 0

    def test_run_skill(self):
        result = run_command("run", {"skill": "seogram"})
        assert result["ok"] is True
        assert result["status"] == "DRY_RUN_OK"

    def test_run_missing_skill(self):
        result = run_command("run")
        assert result["ok"] is False

    def test_unknown_command(self):
        result = run_command("nonexistent")
        assert result["ok"] is False

    def test_list_commands(self):
        cmds = list_commands()
        assert len(cmds) == 6
        assert "status" in cmds
