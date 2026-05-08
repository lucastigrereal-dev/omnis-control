"""Smoke E2E — fluxo completo sem Meta real.

Simula: probe → account readiness → callback dry-run → first post blocked.
Nao chama rede. Nao le .env real. Nao chama Meta.
"""
from __future__ import annotations

import pytest

from src.oauth_readiness.account_readiness import (
    AccountRisk,
    build_account_readiness,
    build_accounts_readiness,
    is_allowed_first_test,
    risk_for_handle,
)


class TestE2ESmoke:
    """Fluxo completo simulado sem OAuth real."""

    def test_probe_mocked_env_to_readiness(self):
        """Simula probe com variaveis mock e gera readiness."""
        mock_env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "present",
            "FACEBOOK_PAGE_ID": "present",
            "META_APP_SECRET": "present",
            "META_GRAPH_VERSION": "present",
            "META_ACCESS_TOKEN": "present",
        }
        r = build_account_readiness(
            "afamiliatigrereal",
            env_probe_results=mock_env,
            has_asset=True,
            has_caption=True,
            callback_http_200=True,
        )
        assert r.ready_for_oauth is True
        assert r.ready_for_first_post is True
        assert r.risk_level == AccountRisk.MEDIUM
        assert r.is_test_candidate is True

    def test_missing_credentials_blocks_oauth(self):
        """Simula cenario real atual: META_APP_SECRET vazio."""
        mock_env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "empty",
            "FACEBOOK_PAGE_ID": "missing",
            "META_APP_SECRET": "empty",
            "META_GRAPH_VERSION": "missing",
            "META_ACCESS_TOKEN": "missing",
        }
        r = build_account_readiness(
            "afamiliatigrereal",
            env_probe_results=mock_env,
            has_asset=False,
            has_caption=False,
            callback_http_200=True,
        )
        assert r.ready_for_oauth is False
        assert r.ready_for_first_post is False
        assert len(r.blockers) >= 3

    def test_critical_account_blocked_for_first_test(self):
        """@lucastigrereal nunca pode ser primeiro teste."""
        mock_env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "present",
            "FACEBOOK_PAGE_ID": "present",
            "META_APP_SECRET": "present",
            "META_GRAPH_VERSION": "present",
        }
        r = build_account_readiness(
            "lucastigrereal",
            env_probe_results=mock_env,
            has_asset=True,
            has_caption=True,
            callback_http_200=True,
        )
        assert r.risk_level == AccountRisk.CRITICAL
        assert r.is_test_candidate is False
        assert r.ready_for_first_post is False
        assert any("CRITICO" in b for b in r.blockers)

    def test_first_post_blocked_by_missing_asset(self):
        """Mesmo com OAuth ok, sem asset = first post blocked."""
        mock_env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "present",
            "META_APP_SECRET": "present",
            "META_GRAPH_VERSION": "present",
        }
        r = build_account_readiness(
            "afamiliatigrereal",
            env_probe_results=mock_env,
            has_asset=False,
            has_caption=True,
            callback_http_200=True,
        )
        assert r.ready_for_oauth is True
        assert r.ready_for_first_post is False
        assert any("asset" in w.lower() for w in r.warnings)

    def test_callback_dry_run_mocked(self):
        """Simula callback HTTP 200 (dry-run, sem token exchange real)."""
        mock_env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "present",
            "META_APP_SECRET": "present",
            "META_GRAPH_VERSION": "present",
        }
        # callback_http_200=True simula o stub P1.5
        r = build_account_readiness(
            "afamiliatigrereal",
            env_probe_results=mock_env,
            has_asset=True,
            has_caption=True,
            callback_http_200=True,
        )
        assert r.callback_status == "present"

    def test_callback_404_scenario(self):
        """Simula cenario antigo (P1.4) com callback 404."""
        mock_env = {
            "INSTAGRAM_BUSINESS_ACCOUNT_ID": "present",
            "META_APP_SECRET": "present",
            "META_GRAPH_VERSION": "present",
        }
        r = build_account_readiness(
            "afamiliatigrereal",
            env_probe_results=mock_env,
            callback_http_200=False,
        )
        assert r.callback_status == "not_configured"

    def test_full_pipeline_mocked(self):
        """Pipeline completo: 6 contas, 2 registradas, 1 candidata."""
        # Only 2 registered in OMNIS
        registered = ["afamiliatigrereal", "lucastigrereal"]
        # Full known handles
        all_handles = [
            "lucastigrereal", "oinatalrn", "agenteviajabrasil",
            "afamiliatigrereal", "oquecomernatalrn", "natalaivoueu",
        ]

        results = build_accounts_readiness(
            all_handles,
            callback_http_200=True,
        )

        assert len(results) == 6

        # Conta recomendada (afamiliatigrereal deve estar entre candidatas)
        candidates = [r for r in results if r.is_test_candidate]
        assert len(candidates) >= 1
        candidate_handles = [c.account_handle for c in candidates]
        assert "afamiliatigrereal" in candidate_handles

        # @lucastigrereal bloqueado
        lucas = [r for r in results if r.account_handle == "lucastigrereal"][0]
        assert lucas.risk_level == AccountRisk.CRITICAL
        assert lucas.is_test_candidate is False

        # Contas high risk tem warning
        high_risk = [r for r in results if r.risk_level == AccountRisk.HIGH]
        assert len(high_risk) == 2  # oinatalrn, agenteviajabrasil
        for hr in high_risk:
            assert any("HIGH" in w or "high" in str(r.warnings) for r in [hr] for w in hr.warnings)

    def test_no_secrets_in_any_output(self):
        """Garante que nenhum cenario produz output com secrets."""
        scenarios = [
            # (handle, env, asset, caption, callback)
            ("afamiliatigrereal", {"META_APP_SECRET": "present"}, True, True, True),
            ("lucastigrereal", {"META_APP_SECRET": "empty"}, False, False, True),
            ("afamiliatigrereal", {"META_APP_SECRET": "missing"}, False, False, False),
        ]
        for handle, env, asset, caption, callback in scenarios:
            r = build_account_readiness(
                handle,
                env_probe_results=env,
                has_asset=asset,
                has_caption=caption,
                callback_http_200=callback,
            )
            d = r.model_dump()
            for key, val in d.items():
                if isinstance(val, str):
                    assert "sk-" not in val, f"Potential secret in {key}"
            summary = r.safe_summary()
            assert "sk-" not in summary
