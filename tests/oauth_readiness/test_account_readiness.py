"""Testes para account_readiness — modelo de prontidao OAuth por conta."""
from __future__ import annotations

import pytest

from src.oauth_readiness.account_readiness import (
    AccountRisk,
    AccountOAuthReadiness,
    ReadinessStatus,
    normalize_handle,
    risk_for_handle,
    is_allowed_first_test,
    build_account_readiness,
    build_accounts_readiness,
    KNOWN_HANDLES,
    CRITICAL_BLOCKED_HANDLES,
)


class TestNormalizeHandle:
    def test_strips_at(self):
        assert normalize_handle("@lucastigrereal") == "lucastigrereal"

    def test_strips_whitespace(self):
        assert normalize_handle("  afamiliatigrereal  ") == "afamiliatigrereal"

    def test_lowercases(self):
        assert normalize_handle("@LucasTigreReal") == "lucastigrereal"


class TestRiskForHandle:
    def test_lucastigrereal_is_critical(self):
        assert risk_for_handle("lucastigrereal") == AccountRisk.CRITICAL
        assert risk_for_handle("@lucastigrereal") == AccountRisk.CRITICAL

    def test_afamiliatigrereal_is_medium(self):
        assert risk_for_handle("afamiliatigrereal") == AccountRisk.MEDIUM

    def test_oinatalrn_is_high(self):
        assert risk_for_handle("oinatalrn") == AccountRisk.HIGH

    def test_unknown_handle_is_medium(self):
        assert risk_for_handle("conta_inexistente_123") == AccountRisk.MEDIUM

    def test_followers_over_500k_is_critical(self):
        assert risk_for_handle("unknown_big", followers=600_000) == AccountRisk.CRITICAL

    def test_followers_over_300k_is_high(self):
        assert risk_for_handle("unknown_mid", followers=350_000) == AccountRisk.HIGH

    def test_followers_under_100k_is_low(self):
        assert risk_for_handle("unknown_small", followers=50_000) == AccountRisk.LOW


class TestIsAllowedFirstTest:
    def test_lucastigrereal_blocked(self):
        assert is_allowed_first_test("lucastigrereal") is False

    def test_afamiliatigrereal_allowed(self):
        assert is_allowed_first_test("afamiliatigrereal") is True

    def test_natalaivoueu_allowed(self):
        assert is_allowed_first_test("natalaivoueu") is True

    def test_critical_by_level_blocked(self):
        assert is_allowed_first_test("unknown", risk_level=AccountRisk.CRITICAL) is False

    def test_high_by_level_allowed(self):
        assert is_allowed_first_test("unknown", risk_level=AccountRisk.HIGH) is True


class TestBuildAccountReadiness:
    def test_critical_account_blocked(self):
        r = build_account_readiness("lucastigrereal")
        assert r.risk_level == AccountRisk.CRITICAL
        assert r.is_test_candidate is False
        assert r.ready_for_oauth is False
        assert r.ready_for_first_post is False
        assert len(r.blockers) > 0

    def test_medium_account_with_all_ok(self):
        env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "present",
            "FACEBOOK_PAGE_ID": "present",
            "META_APP_SECRET": "present",
            "META_GRAPH_VERSION": "present",
        }
        r = build_account_readiness(
            "afamiliatigrereal",
            env_probe_results=env,
            has_asset=True,
            has_caption=True,
            callback_http_200=True,
        )
        assert r.risk_level == AccountRisk.MEDIUM
        assert r.is_test_candidate is True
        assert r.ready_for_oauth is True
        assert r.ready_for_first_post is True

    def test_missing_business_id_blocks_oauth(self):
        env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "missing",
            "META_APP_SECRET": "present",
            "META_GRAPH_VERSION": "present",
        }
        r = build_account_readiness("afamiliatigrereal", env_probe_results=env)
        assert r.ready_for_oauth is False
        assert any("BUSINESS_ACCOUNT_ID" in b for b in r.blockers)

    def test_empty_app_secret_blocks_oauth(self):
        env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "present",
            "META_APP_SECRET": "empty",
            "META_GRAPH_VERSION": "present",
        }
        r = build_account_readiness("afamiliatigrereal", env_probe_results=env)
        assert r.ready_for_oauth is False
        assert any("APP_SECRET" in b for b in r.blockers)

    def test_missing_graph_version_blocks_oauth(self):
        env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "present",
            "META_APP_SECRET": "present",
            "META_GRAPH_VERSION": "missing",
        }
        r = build_account_readiness("afamiliatigrereal", env_probe_results=env)
        assert r.ready_for_oauth is False
        assert any("GRAPH_VERSION" in b for b in r.blockers)

    def test_no_asset_blocks_first_post(self):
        env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "present",
            "META_APP_SECRET": "present",
            "META_GRAPH_VERSION": "present",
        }
        r = build_account_readiness(
            "afamiliatigrereal",
            env_probe_results=env,
            has_asset=False,
            has_caption=True,
            callback_http_200=True,
        )
        assert r.ready_for_oauth is True
        assert r.ready_for_first_post is False
        assert any("asset" in w.lower() for w in r.warnings)

    def test_no_caption_warns_for_first_post(self):
        env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "present",
            "META_APP_SECRET": "present",
            "META_GRAPH_VERSION": "present",
        }
        r = build_account_readiness(
            "afamiliatigrereal",
            env_probe_results=env,
            has_asset=True,
            has_caption=False,
        )
        assert any("caption" in w.lower() for w in r.warnings)

    def test_missing_page_id_is_warning_not_blocker(self):
        env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "present",
            "META_APP_SECRET": "present",
            "META_GRAPH_VERSION": "present",
            "FACEBOOK_PAGE_ID": "missing",
        }
        r = build_account_readiness(
            "afamiliatigrereal",
            env_probe_results=env,
            has_asset=True,
            has_caption=True,
            callback_http_200=True,
        )
        assert any("FACEBOOK_PAGE_ID" in w for w in r.warnings)

    def test_callback_not_200(self):
        env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "present",
            "META_APP_SECRET": "present",
            "META_GRAPH_VERSION": "present",
        }
        r = build_account_readiness(
            "afamiliatigrereal",
            env_probe_results=env,
            has_asset=True,
            has_caption=True,
            callback_http_200=False,
        )
        assert r.callback_status == "not_configured"

    def test_next_actions_populated_when_missing(self):
        r = build_account_readiness("afamiliatigrereal")
        assert len(r.next_actions) > 0
        assert any("META_APP_SECRET" in a for a in r.next_actions)
        assert any("GRAPH_VERSION" in a for a in r.next_actions)

    def test_high_account_has_warning(self):
        r = build_account_readiness("oinatalrn")
        assert r.risk_level == AccountRisk.HIGH
        assert any("HIGH" in w for w in r.warnings)


class TestBuildAccountsReadiness:
    def test_multiple_handles(self):
        results = build_accounts_readiness(["afamiliatigrereal", "lucastigrereal"])
        assert len(results) == 2
        assert results[0].risk_level == AccountRisk.MEDIUM
        assert results[1].risk_level == AccountRisk.CRITICAL

    def test_empty_handles(self):
        results = build_accounts_readiness([])
        assert results == []


class TestAccountOAuthReadinessModel:
    def test_no_extra_fields(self):
        with pytest.raises(Exception):
            AccountOAuthReadiness(
                account_handle="test",
                risk_level=AccountRisk.LOW,
                campo_inventado="nope",
            )

    def test_safe_summary_no_values(self):
        r = build_account_readiness("lucastigrereal")
        summary = r.safe_summary()
        assert "lucastigrereal" in summary
        # "token" pode aparecer como nome de campo (ACCESS_TOKEN), mas nao como valor real
        assert "sk-" not in summary

    def test_model_dump_has_no_secrets(self):
        r = build_account_readiness("afamiliatigrereal")
        d = r.model_dump()
        for v in d.values():
            if isinstance(v, str):
                assert "sk-" not in v
                assert "secret" not in v.lower() or v == "meta_app_secret_status"


class TestKnownHandlesRegistry:
    def test_six_handles_known(self):
        assert len(KNOWN_HANDLES) == 6

    def test_all_known_handles_have_risk(self):
        for handle, info in KNOWN_HANDLES.items():
            assert "risk" in info
            assert isinstance(info["risk"], AccountRisk)

    def test_lucastigrereal_in_blocked(self):
        assert "lucastigrereal" in CRITICAL_BLOCKED_HANDLES

    def test_afamiliatigrereal_not_in_blocked(self):
        assert "afamiliatigrereal" not in CRITICAL_BLOCKED_HANDLES
