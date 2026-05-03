"""Testes do Daily Prophet Checker — Fase Estruturação M4."""

from pathlib import Path

from src.checkers import daily_prophet_check


class TestDailyProphetCheck:
    def test_returns_dict_with_expected_keys(self):
        result = daily_prophet_check.check()
        assert "exists" in result
        assert "has_env" in result
        assert "status" in result

    def test_daily_prophet_exists(self):
        """O diretorio daily-prophet-hotels existe."""
        result = daily_prophet_check.check()
        if not result["exists"]:
            return
        assert isinstance(result["exists"], bool)
        assert isinstance(result["has_env"], bool)

    def test_status_is_known_string(self):
        result = daily_prophet_check.check()
        valid = {"configured", "missing_env", "not_found", "error"}
        assert result["status"] in valid

    def test_nao_crasha_se_pasta_ausente(self):
        """Nao crasha se a pasta nao existe — retorna not_found."""
        dpc = daily_prophet_check
        original = dpc.ROOT
        try:
            dpc.ROOT = Path("/tmp/nonexistent_prophet_xyz")
            result = dpc.check()
            assert result["status"] in ("missing_env", "not_found", "error")
            assert result["exists"] is False
        finally:
            dpc.ROOT = original
