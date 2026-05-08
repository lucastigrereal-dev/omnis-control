"""Tests para First Post models — P1.3a."""
from __future__ import annotations

import json
import pytest

from src.first_post.models import (
    PreflightStatus,
    PreflightCheck,
    PreflightReport,
    PostPackage,
)


class TestPreflightStatus:
    def test_all_statuses_defined(self):
        assert PreflightStatus.READY == "ready"
        assert PreflightStatus.BLOCKED == "blocked"
        assert PreflightStatus.PARTIAL == "partial"
        assert PreflightStatus.EMPTY == "empty"
        assert PreflightStatus.FAILED == "failed"
        assert len(PreflightStatus.ALL) == 5


class TestPreflightCheck:
    def test_check_creation_minimal(self):
        c = PreflightCheck(check_id="test", label="Test", passed=True)
        assert c.check_id == "test"
        assert c.passed is True
        assert c.required is True

    def test_check_creation_failed(self):
        c = PreflightCheck(
            check_id="queue_items",
            label="Queue check",
            passed=False,
            detail="Vazia",
            recommendation="Gere fila",
        )
        assert c.passed is False
        assert c.recommendation == "Gere fila"

    def test_check_optional(self):
        c = PreflightCheck(check_id="assets", label="Assets", passed=False, required=False)
        assert c.required is False


class TestPreflightReport:
    def test_report_defaults(self):
        r = PreflightReport()
        assert r.overall_status == PreflightStatus.EMPTY
        assert r.total_checks == 8
        assert r.passed == 0
        assert r.can_publish is False
        assert len(r.checked_at) > 0

    def test_report_ready(self):
        checks = [PreflightCheck(check_id=f"c{i}", label=f"C{i}", passed=True) for i in range(8)]
        r = PreflightReport(
            overall_status=PreflightStatus.READY,
            passed=8,
            checks=checks,
            can_publish=True,
            ready_items=3,
            next_action="Pronto para revisao",
        )
        assert r.ready_items == 3
        assert r.can_publish is True

    def test_report_serialization(self):
        r = PreflightReport(
            overall_status=PreflightStatus.BLOCKED,
            passed=4,
            failed=4,
            blocked=4,
            can_publish=False,
            ready_items=0,
            next_action="Corrija bloqueios",
        )
        d = r.model_dump()
        assert d["overall_status"] == "blocked"
        assert d["blocked"] == 4


class TestPostPackage:
    def test_package_defaults(self):
        p = PostPackage()
        assert p.ready is False
        assert p.warnings == []
        assert len(p.created_at) > 0

    def test_package_ready(self):
        p = PostPackage(
            queue_id="q_001",
            account_handle="lucastigrereal",
            format="carrossel",
            caption_text="Teste de legenda valida com texto suficiente",
            cta="Link na bio",
            hashtags=["viagem", "brasil"],
            asset_id="a_001",
            ready=True,
        )
        assert p.ready is True
        assert p.account_handle == "lucastigrereal"
        assert len(p.hashtags) == 2

    def test_package_with_warnings(self):
        p = PostPackage(
            queue_id="q_002",
            account_handle="oinatalrn",
            format="reels",
            caption_text="",
            warnings=["Legenda vazia", "Sem asset"],
            ready=False,
        )
        assert not p.ready
        assert len(p.warnings) == 2

    def test_package_serialization(self):
        p = PostPackage(
            queue_id="q_003",
            account_handle="teste",
            format="feed",
            caption_text="Legenda aqui",
            cta="Comente",
            hashtags=["teste"],
            ready=True,
        )
        d = p.model_dump()
        assert d["queue_id"] == "q_003"
        assert d["ready"] is True
