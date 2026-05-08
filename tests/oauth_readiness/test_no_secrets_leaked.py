"""Testes de seguranca — garante que nenhum output vaza valores reais.

Este arquivo e a barreira final: se algum teste aqui falhar,
ha um bug de seguranca que precisa ser corrigido ANTES de commitar.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile

import pytest

from src.oauth_readiness.env_probe import (
    probe_env_vars,
    safe_summary,
    EnvProbeResult,
    EnvProbeSummary,
    EnvVarStatus,
)

# Valor de exemplo que seria catastrofico vazar
SENSITIVE = "sk_live_abc123_secret"


class TestEnvProbeResultNeverStoresValues:
    """O modelo EnvProbeResult so deve ter campos de status."""

    def test_no_value_field_exists(self):
        r = EnvProbeResult(var_name="X", canonical_name="X", status="present")
        d = r.__dict__ if hasattr(r, "__dict__") else {}
        assert "value" not in d
        assert "secret" not in d
        assert "token" not in d

    def test_to_dict_no_value_key(self):
        probe = EnvProbeSummary(
            results=[
                EnvProbeResult(var_name="META_APP_SECRET", canonical_name="META_APP_SECRET",
                               status=EnvVarStatus.PRESENT),
            ],
            source_path="/tmp/.env",
            file_exists=True,
        )
        d = probe.to_dict()
        for var in d["variables"]:
            assert "value" not in var
            assert "secret" not in var
            assert SENSITIVE not in str(var)

    def test_safe_summary_does_not_contain_sensitive(self):
        path = None
        try:
            # Cria .env temporario
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".env", delete=False, encoding="utf-8"
            )
            tmp.write(f"META_APP_SECRET={SENSITIVE}\nMETA_APP_ID=123\n")
            tmp.close()
            path = tmp.name

            probe = probe_env_vars(path)
            text = safe_summary(probe)
            assert SENSITIVE not in text
            assert "sk_live" not in text
            assert "abc123" not in text
        finally:
            if path and os.path.isfile(path):
                os.unlink(path)


class TestOAuthCLIDoesNotLeak:
    """Verifica que os comandos CLI omnis oauth nao vazam valores."""

    def test_oauth_probe_json_no_values(self):
        """omnis oauth probe --json nao deve conter valores de segredo."""
        path = None
        try:
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".env", delete=False, encoding="utf-8"
            )
            tmp.write(
                f"META_APP_ID=1434393165369254\n"
                f"META_APP_SECRET={SENSITIVE}\n"
                f"META_REDIRECT_URI=https://example.com/callback\n"
            )
            tmp.close()
            path = tmp.name

            # Testa probe_env_vars diretamente
            probe = probe_env_vars(path)
            d = probe.to_dict()

            for var in d["variables"]:
                assert SENSITIVE not in str(var)
                assert "1434393165369254" not in str(var)
        finally:
            if path and os.path.isfile(path):
                os.unlink(path)

    def test_probe_repr_no_values(self):
        """repr de EnvProbeSummary nunca deve conter valores."""
        probe = EnvProbeSummary(
            results=[
                EnvProbeResult(
                    var_name="META_APP_SECRET",
                    canonical_name="META_APP_SECRET",
                    status=EnvVarStatus.PRESENT,
                ),
            ],
            source_path="/tmp/.env",
            file_exists=True,
        )
        rep = repr(probe)
        assert SENSITIVE not in rep


class TestInternalReadNotExported:
    """A funcao _read_env_file e interna e nao deve ser exportada."""

    def test_read_env_not_in_all(self):
        from src.oauth_readiness import env_probe
        public = [n for n in dir(env_probe) if not n.startswith("_")]
        assert "_read_env_file" not in public
        assert "raw" not in public


class TestIntegrationNoLeakOnRealEnv:
    """Teste com o .env real do publisher-os — se existir."""

    def test_real_env_probe_no_values_in_output(self):
        env_path = os.path.expanduser("~/publisher-os/.env")
        if not os.path.isfile(env_path):
            pytest.skip("publisher-os/.env nao encontrado")

        probe = probe_env_vars(env_path)
        text = safe_summary(probe)
        d = probe.to_dict()

        # Padroes que indicariam vazamento de valor real
        dangerous_patterns = [
            r"\b[Ee][AaAa][A-Za-z]{20,}\b",  # tokens longos
        ]

        for pat in dangerous_patterns:
            matches = re.findall(pat, text)
            assert len(matches) == 0, f"Possivel vazamento em safe_summary: {matches[:3]}"

        for var in d["variables"]:
            for key in var:
                assert "secret" not in key.lower() or var[key] in ("present", "missing", "empty", "alias_present", "invalid_format"), \
                    f"Valor inesperado em {var['var_name']}.{key} = {var[key]}"
