"""Testes para env_probe — validacao segura de variaveis .env."""
from __future__ import annotations

import os
import tempfile

import pytest

from src.oauth_readiness.env_probe import (
    EnvVarStatus,
    EnvProbeResult,
    EnvProbeSummary,
    probe_env_vars,
    safe_summary,
    DEFAULT_META_VARS,
)


def _write_env(content: str) -> str:
    """Cria .env temporario e retorna path."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8")
    tmp.write(content)
    tmp.close()
    return tmp.name


class TestProbeEnvVars:
    """Testes basicos do probe_env_vars."""

    def test_file_not_found(self):
        probe = probe_env_vars("/nonexistent/path/.env")
        assert probe.file_exists is False
        assert all(r.status == EnvVarStatus.MISSING for r in probe.results)

    def test_all_present_valid(self):
        path = _write_env(
            "META_APP_ID=123456789\n"
            "META_APP_SECRET=abc123def456\n"
            "META_REDIRECT_URI=https://example.com/callback\n"
            "META_GRAPH_VERSION=v20.0\n"
            "INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000\n"
            "FACEBOOK_PAGE_ID=123456789012345\n"
            "META_ACCESS_TOKEN=EAAxxx\n"
        )
        try:
            probe = probe_env_vars(path)
            assert probe.file_exists is True
            assert probe.present_count == 7
            assert probe.missing_count == 0
            assert probe.empty_count == 0
            assert probe.all_required_present is True
        finally:
            os.unlink(path)

    def test_some_missing(self):
        path = _write_env(
            "META_APP_ID=123456789\n"
            "META_APP_SECRET=abc\n"
            "META_REDIRECT_URI=https://example.com/callback\n"
        )
        try:
            probe = probe_env_vars(path)
            assert probe.present_count >= 2
            assert probe.missing_count >= 3
            assert probe.all_required_present is False
        finally:
            os.unlink(path)

    def test_empty_value_detected(self):
        path = _write_env(
            "META_APP_ID=123456789\n"
            "META_APP_SECRET=\n"
            "META_REDIRECT_URI=https://example.com/callback\n"
        )
        try:
            probe = probe_env_vars(path)
            secret = next(r for r in probe.results if r.canonical_name == "META_APP_SECRET")
            assert secret.status == EnvVarStatus.EMPTY
        finally:
            os.unlink(path)

    def test_invalid_format_app_id(self):
        path = _write_env("META_APP_ID=not_a_number\n")
        try:
            probe = probe_env_vars(path)
            app_id = next(r for r in probe.results if r.canonical_name == "META_APP_ID")
            assert app_id.status == EnvVarStatus.INVALID_FORMAT
        finally:
            os.unlink(path)

    def test_invalid_format_graph_version(self):
        path = _write_env(
            "META_APP_ID=123456789\n"
            "META_GRAPH_VERSION=20.0\n"
        )
        try:
            probe = probe_env_vars(path)
            v = next(r for r in probe.results if r.canonical_name == "META_GRAPH_VERSION")
            assert v.status == EnvVarStatus.INVALID_FORMAT
        finally:
            os.unlink(path)

    def test_invalid_redirect_uri(self):
        path = _write_env(
            "META_APP_ID=123456789\n"
            "META_REDIRECT_URI=not_a_url\n"
        )
        try:
            probe = probe_env_vars(path)
            uri = next(r for r in probe.results if r.canonical_name == "META_REDIRECT_URI")
            assert uri.status == EnvVarStatus.INVALID_FORMAT
        finally:
            os.unlink(path)

    def test_redirect_uri_http_ok(self):
        path = _write_env(
            "META_APP_ID=123456789\n"
            "META_REDIRECT_URI=http://localhost:8000/callback\n"
            "META_APP_SECRET=abc123\n"
        )
        try:
            probe = probe_env_vars(path)
            uri = next(r for r in probe.results if r.canonical_name == "META_REDIRECT_URI")
            assert uri.status == EnvVarStatus.PRESENT
        finally:
            os.unlink(path)


class TestAliases:
    """Testes de aliases de variaveis."""

    def test_alias_found_reports_alias_present(self):
        path = _write_env("INSTAGRAM_BUSINESS_ID=17841400000000000\n")
        try:
            probe = probe_env_vars(path)
            result = next(r for r in probe.results
                         if r.canonical_name == "INSTAGRAM_BUSINESS_ACCOUNT_ID")
            assert result.status == EnvVarStatus.ALIAS_PRESENT
            assert result.var_name == "INSTAGRAM_BUSINESS_ID"
            assert result.found_via_alias == "INSTAGRAM_BUSINESS_ID"
        finally:
            os.unlink(path)

    def test_alias_empty_treated_as_empty(self):
        path = _write_env("INSTAGRAM_BUSINESS_ID=\n")
        try:
            probe = probe_env_vars(path)
            result = next(r for r in probe.results
                         if r.canonical_name == "INSTAGRAM_BUSINESS_ACCOUNT_ID")
            assert result.status == EnvVarStatus.EMPTY
        finally:
            os.unlink(path)

    def test_canonical_wins_over_alias(self):
        path = _write_env(
            "INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000\n"
            "INSTAGRAM_BUSINESS_ID=99999999\n"
        )
        try:
            probe = probe_env_vars(path)
            result = next(r for r in probe.results
                         if r.canonical_name == "INSTAGRAM_BUSINESS_ACCOUNT_ID")
            assert result.status == EnvVarStatus.PRESENT
            assert result.var_name == "INSTAGRAM_BUSINESS_ACCOUNT_ID"
        finally:
            os.unlink(path)

    def test_meta_secret_alias(self):
        path = _write_env("META_SECRET=somevalue123\n")
        try:
            probe = probe_env_vars(path)
            result = next(r for r in probe.results
                         if r.canonical_name == "META_APP_SECRET")
            assert result.status == EnvVarStatus.ALIAS_PRESENT
            assert result.var_name == "META_SECRET"
        finally:
            os.unlink(path)

    def test_callback_url_alias(self):
        path = _write_env("CALLBACK_URL=https://example.com/callback\n")
        try:
            probe = probe_env_vars(path)
            result = next(r for r in probe.results
                         if r.canonical_name == "META_REDIRECT_URI")
            assert result.status == EnvVarStatus.ALIAS_PRESENT
        finally:
            os.unlink(path)


class TestSafeSummary:
    """Testes do safe_summary."""

    def test_summary_contains_no_values(self):
        path = _write_env(
            "META_APP_ID=1434393165369254\n"
            "META_APP_SECRET=super_secret_abc123\n"
            "META_REDIRECT_URI=https://example.com/callback\n"
        )
        try:
            probe = probe_env_vars(path)
            text = safe_summary(probe)
            assert "1434393165369254" not in text
            assert "super_secret_abc123" not in text
            assert "present" in text.lower()
        finally:
            os.unlink(path)

    def test_summary_file_not_found(self):
        probe = probe_env_vars("/no/.env")
        text = safe_summary(probe)
        assert "nao encontrado" in text.lower()


class TestEnvProbeResult:
    """Testes de seguranca dos modelos."""

    def test_repr_does_not_leak_value(self):
        r = EnvProbeResult(var_name="META_APP_SECRET", canonical_name="META_APP_SECRET",
                           status=EnvVarStatus.PRESENT)
        rep = repr(r)
        assert "present" in rep
        # Nunca deve ter valor — so status
        assert "secret_value" not in rep

    def test_str_does_not_leak_value(self):
        r = EnvProbeResult(var_name="META_APP_SECRET", canonical_name="META_APP_SECRET",
                           status=EnvVarStatus.PRESENT)
        s = str(r)
        assert "present" in s

    def test_to_dict_no_values(self):
        probe = EnvProbeSummary(
            results=[
                EnvProbeResult(var_name="META_APP_ID", canonical_name="META_APP_ID",
                               status=EnvVarStatus.PRESENT),
            ],
            source_path="/tmp/.env",
            file_exists=True,
        )
        d = probe.to_dict()
        assert "value" not in d["variables"][0]
        assert d["variables"][0]["status"] == "present"
        assert d["variables"][0]["var_name"] == "META_APP_ID"


class TestNonEmptyOrMissing:
    """META_ACCESS_TOKEN com regra non_empty_or_missing — nao deve falhar se ausente."""

    def test_access_token_missing_is_ok(self):
        path = _write_env("META_APP_ID=123\n")
        try:
            probe = probe_env_vars(path)
            r = next(r for r in probe.results if r.canonical_name == "META_ACCESS_TOKEN")
            assert r.status == EnvVarStatus.MISSING
            assert r.required is False
        finally:
            os.unlink(path)

    def test_access_token_present_is_ok(self):
        path = _write_env("META_ACCESS_TOKEN=EAAxxx123\n")
        try:
            probe = probe_env_vars(path)
            r = next(r for r in probe.results if r.canonical_name == "META_ACCESS_TOKEN")
            assert r.status == EnvVarStatus.PRESENT
        finally:
            os.unlink(path)


class TestCommentsAndQuotes:
    """Testes de parsing robusto."""

    def test_comments_ignored(self):
        path = _write_env(
            "# META_APP_ID=commented_value\n"
            "META_APP_ID=123456789\n"
        )
        try:
            probe = probe_env_vars(path)
            r = next(r for r in probe.results if r.canonical_name == "META_APP_ID")
            assert r.status == EnvVarStatus.PRESENT
        finally:
            os.unlink(path)

    def test_quoted_value(self):
        path = _write_env('META_APP_ID="123456789"\n')
        try:
            probe = probe_env_vars(path)
            r = next(r for r in probe.results if r.canonical_name == "META_APP_ID")
            assert r.status == EnvVarStatus.PRESENT
        finally:
            os.unlink(path)

    def test_empty_lines_ignored(self):
        path = _write_env(
            "\n\nMETA_APP_ID=123456789\n\n"
            "META_APP_SECRET=abc\n\n"
        )
        try:
            probe = probe_env_vars(path)
            assert probe.file_exists
        finally:
            os.unlink(path)

    def test_custom_expected_vars(self):
        path = _write_env("MY_VAR=hello\n")
        try:
            custom = {"MY_VAR": {"required": True, "validate": "non_empty", "aliases": []}}
            probe = probe_env_vars(path, expected_vars=custom)
            assert probe.total_checked == 1
            assert probe.present_count == 1
        finally:
            os.unlink(path)
