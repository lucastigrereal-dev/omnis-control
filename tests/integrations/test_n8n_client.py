"""Smoke tests for n8n_client (no live calls)."""
from src.integrations.n8n_client import N8NClient


def test_client_instantiates_with_defaults():
    c = N8NClient()
    assert c.base_url.startswith("http")
    assert isinstance(c.api_key, str)


def test_client_accepts_overrides():
    c = N8NClient(base_url="http://test:9999", api_key="secret")
    assert c.base_url == "http://test:9999"
    assert c.api_key == "secret"


def test_headers_without_api_key():
    c = N8NClient(base_url="http://x", api_key="")
    h = c._headers()
    assert h.get("Content-Type") == "application/json"
    assert "X-N8N-API-KEY" not in h


def test_headers_with_api_key():
    c = N8NClient(base_url="http://x", api_key="abc")
    h = c._headers()
    assert h.get("X-N8N-API-KEY") == "abc"
