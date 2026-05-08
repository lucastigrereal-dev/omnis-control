"""Tests para OAuth Readiness Checker — P1.2a."""
from __future__ import annotations

import pytest

from src.oauth_readiness.checker import OAuthReadinessChecker
from src.oauth_readiness.models import OAuthReadinessStatus, OAuthReadinessReport, OAuthReadinessCheck


class TestOAuthReadinessChecker:
    def test_checker_returns_report(self):
        checker = OAuthReadinessChecker()
        report = checker.check_all()
        assert isinstance(report, OAuthReadinessReport)
        assert report.total_checks == 12
        assert len(report.checks) == 12

    def test_checker_all_checks_have_ids(self):
        checker = OAuthReadinessChecker()
        report = checker.check_all()
        ids = {c.check_id for c in report.checks}
        assert "docker_running" in ids
        assert "publisher_os_healthy" in ids
        assert "supabase_db_accessible" in ids
        assert "redis_accessible" in ids
        assert "disk_space" in ids
        assert "meta_app_id_exists" in ids
        assert "meta_app_secret_exists" in ids
        assert "meta_app_id_configured" in ids
        assert "meta_app_secret_configured" in ids
        assert "meta_callback_url_documented" in ids
        assert "instagram_accounts_registered" in ids
        assert "network_outbound" in ids

    def test_checker_produces_aggregated_counts(self):
        checker = OAuthReadinessChecker()
        report = checker.check_all()
        assert report.passed + report.failed == 12
        assert report.passed >= 0
        assert report.failed >= 0
        assert report.blocked_by_required >= 0

    def test_checker_has_checked_at_timestamp(self):
        checker = OAuthReadinessChecker()
        report = checker.check_all()
        assert len(report.checked_at) > 0
        assert "T" in report.checked_at

    def test_checker_produces_next_action(self):
        checker = OAuthReadinessChecker()
        report = checker.check_all()
        assert len(report.next_action) > 0

    def test_checker_overall_status_is_valid(self):
        checker = OAuthReadinessChecker()
        report = checker.check_all()
        assert report.overall_status in OAuthReadinessStatus.ALL

    def test_checker_checks_are_valid(self):
        checker = OAuthReadinessChecker()
        report = checker.check_all()
        for c in report.checks:
            assert isinstance(c, OAuthReadinessCheck)
            assert len(c.check_id) > 0
            assert len(c.label) > 0
            assert c.status in OAuthReadinessStatus.ALL
            assert isinstance(c.passed, bool)
            assert isinstance(c.required, bool)

    def test_checker_no_env_read(self, monkeypatch):
        """Garante que o checker nao tenta ler .env real."""
        call_count = 0
        original_open = open

        def _tracked_open(*args, **kwargs):
            nonlocal call_count
            path = args[0] if args else ""
            if ".env" in str(path) and ".env.example" not in str(path):
                call_count += 1
            return original_open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", _tracked_open)
        checker = OAuthReadinessChecker()
        checker.check_all()
        # O checker so deve abrir .env.example, nunca .env
        # (pode abrir .env.example para checks de documentacao)
        assert call_count == 0, f"Checker abriu .env {call_count}x — nao deveria ler .env"
