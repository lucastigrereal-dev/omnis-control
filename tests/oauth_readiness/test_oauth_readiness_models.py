"""Tests para OAuth Readiness models — P1.2a."""
from __future__ import annotations

import json
import pytest

from src.oauth_readiness.models import (
    OAuthReadinessStatus,
    OAuthReadinessCheck,
    OAuthReadinessReport,
)


class TestOAuthReadinessStatus:
    def test_all_statuses_defined(self):
        assert OAuthReadinessStatus.READY == "ready"
        assert OAuthReadinessStatus.BLOCKED == "blocked"
        assert OAuthReadinessStatus.HUMAN_REQUIRED == "human_required"
        assert OAuthReadinessStatus.NOT_CONFIGURED == "not_configured"
        assert OAuthReadinessStatus.FAILED == "failed"
        assert len(OAuthReadinessStatus.ALL) == 5


class TestOAuthReadinessCheck:
    def test_check_creation_minimal(self):
        c = OAuthReadinessCheck(
            check_id="test_check",
            label="Test check",
            passed=True,
        )
        assert c.check_id == "test_check"
        assert c.label == "Test check"
        assert c.passed is True
        assert c.required is True
        assert c.status == OAuthReadinessStatus.READY
        assert c.detail == ""
        assert c.recommendation == ""

    def test_check_creation_failed(self):
        c = OAuthReadinessCheck(
            check_id="docker_running",
            label="Docker daemon acessivel",
            passed=False,
            detail="Docker nao respondeu",
            recommendation="Inicie o Docker",
        )
        assert c.passed is False
        assert c.status == OAuthReadinessStatus.BLOCKED
        assert c.detail == "Docker nao respondeu"

    def test_check_human_required(self):
        c = OAuthReadinessCheck(
            check_id="meta_app_id_configured",
            label="META_APP_ID preenchido",
            passed=False,
            status=OAuthReadinessStatus.HUMAN_REQUIRED,
        )
        assert c.passed is False
        assert c.status == OAuthReadinessStatus.HUMAN_REQUIRED

    def test_check_optional(self):
        c = OAuthReadinessCheck(
            check_id="network_outbound",
            label="Network check",
            passed=False,
            required=False,
        )
        assert c.required is False

    def test_check_serialization(self):
        c = OAuthReadinessCheck(
            check_id="test",
            label="Test",
            passed=True,
            detail="ok",
        )
        d = c.model_dump()
        assert d["check_id"] == "test"
        assert d["passed"] is True
        assert d["required"] is True

    def test_check_json(self):
        c = OAuthReadinessCheck(
            check_id="test",
            label="Test",
            passed=True,
        )
        raw = c.model_dump_json()
        data = json.loads(raw)
        assert data["check_id"] == "test"


class TestOAuthReadinessReport:
    def test_report_defaults(self):
        r = OAuthReadinessReport()
        assert r.overall_status == OAuthReadinessStatus.NOT_CONFIGURED
        assert r.total_checks == 12
        assert r.passed == 0
        assert r.failed == 0
        assert r.blocked_by_required == 0
        assert r.can_proceed is False
        assert len(r.checks) == 0
        assert len(r.checked_at) > 0

    def test_report_with_checks(self):
        checks = [
            OAuthReadinessCheck(check_id="c1", label="C1", passed=True),
            OAuthReadinessCheck(check_id="c2", label="C2", passed=False, detail="falhou"),
            OAuthReadinessCheck(check_id="c3", label="C3", passed=True, required=False),
        ]
        r = OAuthReadinessReport(
            overall_status=OAuthReadinessStatus.BLOCKED,
            passed=2,
            failed=1,
            blocked_by_required=1,
            checks=checks,
            can_proceed=False,
            next_action="Corrija c2",
        )
        assert len(r.checks) == 3
        assert r.passed == 2
        assert r.failed == 1
        assert r.blocked_by_required == 1

    def test_report_serialization(self):
        r = OAuthReadinessReport(
            overall_status=OAuthReadinessStatus.READY,
            passed=12,
            failed=0,
            can_proceed=True,
            next_action="Execute omnis oauth start",
        )
        d = r.model_dump()
        assert d["overall_status"] == "ready"
        assert d["passed"] == 12
        assert d["can_proceed"] is True
