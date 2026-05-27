"""Shared fixtures for OMNIS tests.

Padrão anti-travamento (mesmo que KRATOS setup.ts):
  - `block_external_network` — autouse global — intercepta httpx + requests
    para qualquer host não-localhost → retorna 503 INSTANTÂNEO.
  - Nenhum teste toca Qdrant:6333, LiteLLM:4000, n8n:5678 ou API externa.
  - Testes que precisam de container real → @pytest.mark.integration.
"""
from __future__ import annotations

import pytest

# ── Hosts permitidos em testes (localhost / testserver do FastAPI TestClient) ──
_ALLOWED_HOSTS = frozenset({"localhost", "127.0.0.1", "testserver", "0.0.0.0", "::1"})


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch):
    """Bloqueia toda chamada HTTP(S) para hosts não-localhost.

    httpx e requests interceptados. Retorna 503 instantâneo em vez de
    tentar conectar a serviços externos (Qdrant, LiteLLM, n8n, APIs externas).

    Testes que precisam de rede real devem ser marcados @pytest.mark.integration
    e rodar separado: pytest --timeout=30 -m integration
    """
    # ── httpx.Client (sync) ─────────────────────────────────────────────────
    try:
        import httpx

        _orig_client_send = httpx.Client.send

        def _mock_client_send(self, request, *args, **kwargs):
            if request.url.host not in _ALLOWED_HOSTS:
                return httpx.Response(
                    503,
                    request=request,
                    text=f"[test-block] host '{request.url.host}' bloqueado — use @pytest.mark.integration",
                )
            return _orig_client_send(self, request, *args, **kwargs)

        monkeypatch.setattr(httpx.Client, "send", _mock_client_send)

        # ── httpx.AsyncClient (async) ────────────────────────────────────────
        _orig_async_send = httpx.AsyncClient.send

        async def _mock_async_send(self, request, *args, **kwargs):
            if request.url.host not in _ALLOWED_HOSTS:
                return httpx.Response(
                    503,
                    request=request,
                    text=f"[test-block] host '{request.url.host}' bloqueado — use @pytest.mark.integration",
                )
            return await _orig_async_send(self, request, *args, **kwargs)

        monkeypatch.setattr(httpx.AsyncClient, "send", _mock_async_send)

    except ImportError:
        pass  # httpx não instalado — sem problema

    # ── requests.Session (sync) ─────────────────────────────────────────────
    try:
        import requests
        from urllib.parse import urlparse

        _orig_req_send = requests.Session.send

        def _mock_req_send(self, prepared, *args, **kwargs):
            host = urlparse(prepared.url).hostname or ""
            if host not in _ALLOWED_HOSTS:
                from requests.models import Response as _R
                r = _R()
                r.status_code = 503
                r._content = (
                    f"[test-block] host '{host}' bloqueado — use @pytest.mark.integration"
                ).encode()
                r.encoding = "utf-8"
                return r
            return _orig_req_send(self, prepared, *args, **kwargs)

        monkeypatch.setattr(requests.Session, "send", _mock_req_send)

    except ImportError:
        pass  # requests não instalado — sem problema


@pytest.fixture
def empty_data(tmp_path):
    """Redirect data dirs to tmp for isolation."""
    import src.creative_production.briefs as bmod
    import src.creative_production.production_queue as qmod
    import src.creative_production.exporter as emod
    original_briefs = bmod.BRIEFS_FILE
    original_queue = bmod.DATA_DIR
    original_exp = emod.EXPORT_DIR
    bmod.BRIEFS_FILE = tmp_path / "creative_briefs.jsonl"
    bmod.REVIEW_LOG = tmp_path / "creative_review_log.jsonl"
    bmod.DATA_DIR = tmp_path
    qmod.QUEUE_FILE = tmp_path / "production_queue.jsonl"
    qmod.DATA_DIR = tmp_path
    emod.EXPORT_DIR = tmp_path / "exports"
    yield tmp_path
    bmod.BRIEFS_FILE = original_briefs
    bmod.DATA_DIR = original_queue
    emod.EXPORT_DIR = original_exp


@pytest.fixture
def sample_brief_data():
    """Standard creative brief data with all fields filled."""
    return {
        "queue_id": "q-001",
        "caption_draft_id": "cd-001",
        "account_handle": "@lucastigrereal",
        "format": "carrossel",
        "objective": "engajar",
        "visual_direction": "colorido e moderno",
        "script": "Veja como foi incrível nossa viagem para Natal! #viagem #familia\n\nO litoral norte tem praias deslumbrantes e piscinas naturais.",
        "shot_list": "- Cena 1: Abertura drone\n- Cena 2: Família na praia\n- Cena 3: Close comidas típicas",
        "design_notes": "Usar fontes arredondadas. Paleta: azul, branco, laranja.",
        "editing_notes": "Transições suaves. Música: instrumental animada.",
        "asset_requirements": {"resolution": "1080x1080", "format": "png", "max_size_mb": 10},
        "tool_suggestions": ["canva", "capcut", "runway"],
    }
