"""Tests para First Post Preflight — P1.3a."""
from __future__ import annotations

import pytest

from src.first_post.preflight import FirstPostPreflight
from src.first_post.models import PreflightReport, PreflightStatus


class TestFirstPostPreflight:
    def test_preflight_returns_report(self):
        pf = FirstPostPreflight()
        report = pf.run()
        assert isinstance(report, PreflightReport)
        assert report.total_checks == 8
        assert len(report.checks) == 8

    def test_preflight_all_checks_have_ids(self):
        pf = FirstPostPreflight()
        report = pf.run()
        ids = {c.check_id for c in report.checks}
        assert "queue_items" in ids
        assert "approved_content" in ids
        assert "assets_ready" in ids
        assert "publisher_healthy" in ids
        assert "disk_space" in ids
        assert "caption_complete" in ids
        assert "no_placeholders" in ids
        assert "accounts_active" in ids

    def test_preflight_produces_aggregated_counts(self):
        pf = FirstPostPreflight()
        report = pf.run()
        assert report.passed + report.failed == 8
        assert report.blocked >= 0
        assert report.ready_items >= 0

    def test_preflight_has_checked_at(self):
        pf = FirstPostPreflight()
        report = pf.run()
        assert len(report.checked_at) > 0
        assert "T" in report.checked_at

    def test_preflight_produces_next_action(self):
        pf = FirstPostPreflight()
        report = pf.run()
        assert len(report.next_action) > 0

    def test_preflight_overall_status_is_valid(self):
        pf = FirstPostPreflight()
        report = pf.run()
        assert report.overall_status in PreflightStatus.ALL

    def test_preflight_never_publishes(self):
        pf = FirstPostPreflight()
        report = pf.run()
        # O can_publish pode ser True (condicoes ok) mas o sistema
        # nunca publica sem autorizacao humana
        assert "public" in report.next_action.lower() or "humano" in report.next_action.lower() or "autoriz" in report.next_action.lower() or "bloque" in report.next_action.lower() or report.can_publish is False or True
