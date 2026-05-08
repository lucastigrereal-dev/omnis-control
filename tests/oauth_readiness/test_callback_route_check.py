"""Testes para o check de callback route — P1.5."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from src.oauth_readiness.checklist import _check_callback_route_exists
from src.oauth_readiness.models import OAuthReadinessStatus


class TestCallbackRouteCheck:
    """Varios cenarios de resposta da rota de callback."""

    def test_200_human_required_json(self):
        """Rota retorna 200 com status human_required — check passa."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "status": "human_required",
            "message": "OAuth callback route is reachable.",
        }).encode()

        with patch("urllib.request.urlopen", return_value=mock_resp):
            check = _check_callback_route_exists()
            assert check.passed is True
            assert "200" in check.detail

    def test_200_received_code_dry_run(self):
        """Rota retorna 200 com received_code_dry_run — check passa."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "status": "received_code_dry_run",
            "code_received": True,
        }).encode()

        with patch("urllib.request.urlopen", return_value=mock_resp):
            check = _check_callback_route_exists()
            assert check.passed is True

    def test_200_oauth_error_json(self):
        """Rota retorna 200 com oauth_error (usuario negou) — check passa (rota funciona)."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "status": "oauth_error",
            "error": "access_denied",
        }).encode()

        with patch("urllib.request.urlopen", return_value=mock_resp):
            check = _check_callback_route_exists()
            assert check.passed is True

    def test_404_blocked_callback(self):
        """404 — rota nao implementada."""
        import urllib.error
        mock_error = urllib.error.HTTPError(
            url="http://localhost:8000/callback",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

        with patch("urllib.request.urlopen", side_effect=mock_error):
            check = _check_callback_route_exists()
            assert check.passed is False
            assert check.status == OAuthReadinessStatus.BLOCKED
            assert "404" in check.detail

    def test_connection_refused(self):
        """Conexao recusada — Publisher OS offline."""
        import urllib.error
        mock_error = urllib.error.URLError("Connection refused")

        with patch("urllib.request.urlopen", side_effect=mock_error):
            check = _check_callback_route_exists()
            assert check.passed is False
            assert check.status == OAuthReadinessStatus.BLOCKED
            assert "recusada" in check.detail.lower() or "refused" in check.detail.lower()

    def test_timeout(self):
        """Timeout — Publisher OS nao respondeu."""
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
            check = _check_callback_route_exists()
            assert check.passed is False
            assert "timeout" in check.detail.lower() or "time" in check.detail.lower()
