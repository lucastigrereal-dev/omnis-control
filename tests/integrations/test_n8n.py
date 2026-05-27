"""W15 — Tests for N8NClient graceful degradation and webhook receiver."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.integrations.n8n_client import N8NClient


# ---------------------------------------------------------------------------
# N8NClient — offline / graceful degradation
# ---------------------------------------------------------------------------

def test_n8n_client_graceful():
    """N8NClient with n8n off → trigger_workflow returns {"status": "unavailable"}."""
    client = N8NClient(base_url="http://127.0.0.1:19999")  # porta inexistente
    result = client.trigger_workflow("test-path", {"foo": "bar"})
    assert result.get("status") == "unavailable"
    assert "error" in result


def test_health_check_false():
    """health_check() with n8n off → False."""
    client = N8NClient(base_url="http://127.0.0.1:19999")
    assert client.health_check() is False


def test_trigger_lead():
    """trigger_lead_processing returns dict with status."""
    client = N8NClient(base_url="http://127.0.0.1:19999")
    result = client.trigger_lead_processing("mensagem de teste", "instagram")
    assert isinstance(result, dict)
    assert "status" in result


def test_trigger_content():
    """trigger_content_production returns dict with status."""
    client = N8NClient(base_url="http://127.0.0.1:19999")
    result = client.trigger_content_production("viagem", "Casa Segura")
    assert isinstance(result, dict)
    assert "status" in result


def test_trigger_sprint():
    """trigger_sprint_creation returns dict with status."""
    client = N8NClient(base_url="http://127.0.0.1:19999")
    result = client.trigger_sprint_creation([{"titulo": "ideia1"}, {"titulo": "ideia2"}])
    assert isinstance(result, dict)
    assert "status" in result


# ---------------------------------------------------------------------------
# Webhook receiver — FastAPI routes
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    from src.api.main import app
    return TestClient(app)


def test_webhook_nova_ideia(api_client):
    """POST /webhooks/n8n/nova-ideia → 200 with task_id."""
    payload = {"ideia": "viagem para Natal", "paginas": ["@oinatalrn"]}
    response = api_client.post("/webhooks/n8n/nova-ideia", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert "task_id" in data
    assert data["task_id"].startswith("ideia_")


def test_webhook_novo_lead(api_client):
    """POST /webhooks/n8n/novo-lead → 200 with task_id."""
    payload = {"mensagem": "Quero collab!", "origem": "instagram"}
    response = api_client.post("/webhooks/n8n/novo-lead", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert "task_id" in data
    assert data["task_id"].startswith("lead_")


def test_webhook_publicacao_ok(api_client):
    """POST /webhooks/n8n/publicacao-ok → 200."""
    payload = {"post_id": "123", "plataforma": "instagram"}
    response = api_client.post("/webhooks/n8n/publicacao-ok", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "received"


def test_webhook_metricas(api_client):
    """POST /webhooks/n8n/metricas → 200."""
    payload = {"alcance": 50000, "engajamento": 3.2}
    response = api_client.post("/webhooks/n8n/metricas", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "received"
