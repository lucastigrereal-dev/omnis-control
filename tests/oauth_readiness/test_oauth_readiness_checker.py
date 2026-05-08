"""Tests para OAuth Readiness Checker — P1.4."""
from __future__ import annotations

import pytest

from src.oauth_readiness.checker import OAuthReadinessChecker
from src.oauth_readiness.models import OAuthReadinessStatus, OAuthReadinessReport, OAuthReadinessCheck


class TestOAuthReadinessChecker:
    def test_checker_returns_report(self):
        checker = OAuthReadinessChecker()
        report = checker.check_all()
        assert isinstance(report, OAuthReadinessReport)
        assert report.total_checks > 0
        assert report.total_checks == len(report.checks)

    def test_checker_infra_checks_exist(self):
        checker = OAuthReadinessChecker()
        report = checker.check_all()
        ids = {c.check_id for c in report.checks}
        infra_ids = {
            "docker_running", "publisher_os_healthy",
            "supabase_db_accessible", "redis_accessible", "disk_space",
            "callback_route_exists", "instagram_accounts_registered", "network_outbound",
        }
        assert infra_ids.issubset(ids), f"Faltam checks de infra: {infra_ids - ids}"

    def test_checker_env_var_checks_exist(self):
        checker = OAuthReadinessChecker()
        report = checker.check_all()
        ids = {c.check_id for c in report.checks}
        expected_env = {
            "env_meta_app_id",
            "env_meta_app_secret",
            "env_meta_redirect_uri",
            "env_meta_graph_version",
            "env_instagram_business_account_id",
            "env_facebook_page_id",
            "env_meta_access_token",
        }
        assert expected_env.issubset(ids), f"Faltam checks de env vars: {expected_env - ids}"

    def test_checker_produces_aggregated_counts(self):
        checker = OAuthReadinessChecker()
        report = checker.check_all()
        assert report.passed + report.failed == report.total_checks
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

    def test_checker_docker_running_returns_bool(self):
        """Garante que _check_docker_running sempre retorna bool em passed.

        Bug P1.3b: result.returncode == 0 and result.stdout.strip()
        retornava a string '29.2.1' em vez de True.
        """
        from src.oauth_readiness.checklist import _check_docker_running
        check = _check_docker_running()
        assert isinstance(check.passed, bool), f"passed deve ser bool, recebeu {type(check.passed)}: {check.passed!r}"

    def test_env_probe_never_leaks_values(self):
        """Garante que checks de env vars nunca contem valores reais no output."""
        checker = OAuthReadinessChecker()
        report = checker.check_all()
        for c in report.checks:
            if c.check_id.startswith("env_"):
                # Detail nao deve conter nada parecido com segredo
                assert "sk_" not in c.detail.lower()
                assert c.detail != ""
