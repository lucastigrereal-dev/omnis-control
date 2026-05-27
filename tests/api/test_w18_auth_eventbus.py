"""Testes W18: Auth API key + SSE EventBus."""
from __future__ import annotations

import asyncio
import json
import os
import time

import pytest
from fastapi.testclient import TestClient

from src.api.auth import dev_mode, require_api_key, _configured_key
from src.api.event_bus import (
    EventBus,
    OmnisEvent,
    get_event_bus,
    publish_mission_started,
    publish_mission_completed,
    publish_mission_failed,
    publish_cost_updated,
    publish_agent_result,
    reset_event_bus,
)


# ──────────────────────────────────────────────────────────────────────────────
# Auth tests
# ──────────────────────────────────────────────────────────────────────────────


class TestDevMode:
    def test_dev_mode_when_no_env_var(self, monkeypatch):
        """Sem OMNIS_API_KEY → dev_mode=True."""
        monkeypatch.delenv("OMNIS_API_KEY", raising=False)
        # Limpa cache do lru_cache para refletir mudança
        _configured_key.cache_clear()
        assert dev_mode() is True

    def test_dev_mode_off_when_key_set(self, monkeypatch):
        """Com OMNIS_API_KEY → dev_mode=False."""
        monkeypatch.setenv("OMNIS_API_KEY", "test-secret-123")
        _configured_key.cache_clear()
        assert dev_mode() is False

    def teardown_method(self):
        """Limpa cache após cada teste."""
        _configured_key.cache_clear()


class TestRequireApiKey:
    def test_dev_mode_allows_all(self, monkeypatch):
        """Dev mode: qualquer requisição passa."""
        monkeypatch.delenv("OMNIS_API_KEY", raising=False)
        _configured_key.cache_clear()
        result = require_api_key(x_api_key=None, authorization=None)
        assert result is True

    def test_prod_mode_correct_x_api_key(self, monkeypatch):
        """Prod mode: X-API-Key correto → passa."""
        monkeypatch.setenv("OMNIS_API_KEY", "my-secret")
        _configured_key.cache_clear()
        result = require_api_key(x_api_key="my-secret", authorization=None)
        assert result is True

    def test_prod_mode_correct_bearer(self, monkeypatch):
        """Prod mode: Authorization: Bearer <key> correto → passa."""
        monkeypatch.setenv("OMNIS_API_KEY", "my-secret")
        _configured_key.cache_clear()
        result = require_api_key(x_api_key=None, authorization="Bearer my-secret")
        assert result is True

    def test_prod_mode_wrong_key_raises_403(self, monkeypatch):
        """Prod mode: chave errada → HTTPException 403."""
        from fastapi import HTTPException
        monkeypatch.setenv("OMNIS_API_KEY", "my-secret")
        _configured_key.cache_clear()
        with pytest.raises(HTTPException) as exc_info:
            require_api_key(x_api_key="wrong-key", authorization=None)
        assert exc_info.value.status_code == 403

    def test_prod_mode_no_key_raises_403(self, monkeypatch):
        """Prod mode: sem chave → HTTPException 403."""
        from fastapi import HTTPException
        monkeypatch.setenv("OMNIS_API_KEY", "my-secret")
        _configured_key.cache_clear()
        with pytest.raises(HTTPException) as exc_info:
            require_api_key(x_api_key=None, authorization=None)
        assert exc_info.value.status_code == 403

    def teardown_method(self):
        _configured_key.cache_clear()


class TestApiEndpointAuth:
    """Testes de integração: endpoints que usam require_api_key."""

    def setup_method(self):
        # Garante dev mode para testes de integração
        _configured_key.cache_clear()
        os.environ.pop("OMNIS_API_KEY", None)

    def test_events_status_dev_mode(self):
        """Em dev mode, /events/status não requer auth."""
        _configured_key.cache_clear()
        from src.api.main import app
        with TestClient(app) as client:
            r = client.get("/events/status")
        assert r.status_code == 200
        data = r.json()
        assert "subscribers" in data

    def test_root_shows_auth_dev(self):
        """Root endpoint informa modo dev."""
        _configured_key.cache_clear()
        from src.api.main import app
        with TestClient(app) as client:
            r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["auth"] == "dev"
        # Version bumps with each wave; just check it exists and looks like semver
        assert "version" in data
        assert "." in data["version"]

    def teardown_method(self):
        _configured_key.cache_clear()
        os.environ.pop("OMNIS_API_KEY", None)


# ──────────────────────────────────────────────────────────────────────────────
# EventBus tests
# ──────────────────────────────────────────────────────────────────────────────


class TestOmnisEvent:
    def test_to_sse_format(self):
        """Evento serializa para SSE correto."""
        event = OmnisEvent(event_type="test_event", data={"key": "value"}, ts=1000.0)
        sse = event.to_sse()
        assert sse.startswith("event: test_event\n")
        assert "data:" in sse
        assert sse.endswith("\n\n")
        payload = json.loads(sse.split("data: ", 1)[1].strip())
        assert payload["type"] == "test_event"
        assert payload["data"] == {"key": "value"}
        assert payload["ts"] == 1000.0

    def test_to_dict(self):
        event = OmnisEvent(event_type="x", data={"a": 1}, ts=500.0)
        d = event.to_dict()
        assert d == {"type": "x", "data": {"a": 1}, "ts": 500.0}


class TestEventBus:
    def setup_method(self):
        reset_event_bus()

    def teardown_method(self):
        reset_event_bus()

    def test_subscriber_count_empty(self):
        bus = EventBus()
        assert bus.subscriber_count() == 0

    @pytest.mark.asyncio
    async def test_publish_to_no_subscribers(self):
        """Publicar sem subscribers → retorna 0, sem erro."""
        bus = EventBus()
        count = await bus.publish("test", {"x": 1})
        assert count == 0

    @pytest.mark.asyncio
    async def test_single_subscriber_receives_event(self):
        """Subscriber recebe evento publicado."""
        bus = EventBus()
        received: list[OmnisEvent] = []

        async def consume():
            async for event in bus.subscribe():
                received.append(event)
                break  # Para após primeiro evento

        task = asyncio.create_task(consume())
        await asyncio.sleep(0.01)  # Subscriber precisa estar pronto

        count = await bus.publish("mission_started", {"mission_id": "m1"})
        await task

        assert count == 1
        assert len(received) == 1
        assert received[0].event_type == "mission_started"
        assert received[0].data["mission_id"] == "m1"

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        """Múltiplos subscribers recebem o mesmo evento."""
        bus = EventBus()
        results: dict[int, list[OmnisEvent]] = {0: [], 1: []}

        async def consume(idx: int):
            async for event in bus.subscribe():
                results[idx].append(event)
                break

        t0 = asyncio.create_task(consume(0))
        t1 = asyncio.create_task(consume(1))
        await asyncio.sleep(0.01)

        count = await bus.publish("heartbeat", {"ts": 1.0})
        await t0
        await t1

        assert count == 2
        assert len(results[0]) == 1
        assert len(results[1]) == 1

    @pytest.mark.asyncio
    async def test_subscriber_count_updates(self):
        """subscriber_count reflete conexões ativas."""
        bus = EventBus()
        assert bus.subscriber_count() == 0

        received: list[OmnisEvent] = []

        async def consume():
            async for event in bus.subscribe():
                received.append(event)
                break

        task = asyncio.create_task(consume())
        await asyncio.sleep(0.02)  # Subscriber registrado
        assert bus.subscriber_count() == 1

        await bus.publish("x", {})
        await task
        await asyncio.sleep(0.01)  # Cleanup

        assert bus.subscriber_count() == 0

    @pytest.mark.asyncio
    async def test_shutdown_disconnects_subscribers(self):
        """shutdown() envia None para todos os subscribers."""
        bus = EventBus()
        received: list[OmnisEvent] = []

        async def consume():
            async for event in bus.subscribe():
                received.append(event)

        task = asyncio.create_task(consume())
        await asyncio.sleep(0.01)

        await bus.shutdown()
        await task  # Deve terminar após shutdown

        assert len(received) == 0  # Nenhum evento real, só sinal de encerramento

    def test_publish_sync_no_loop(self):
        """publish_sync sem event loop não explode."""
        bus = EventBus()
        # Fora de asyncio context — deve ser silencioso
        bus.publish_sync("test", {"x": 1})


class TestSingletonBus:
    def setup_method(self):
        reset_event_bus()

    def teardown_method(self):
        reset_event_bus()

    def test_get_event_bus_returns_same_instance(self):
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_reset_creates_new_instance(self):
        bus1 = get_event_bus()
        reset_event_bus()
        bus2 = get_event_bus()
        assert bus1 is not bus2


class TestPublishHelpers:
    def setup_method(self):
        reset_event_bus()

    def teardown_method(self):
        reset_event_bus()

    @pytest.mark.asyncio
    async def test_publish_mission_started(self):
        bus = get_event_bus()
        received: list[OmnisEvent] = []

        async def consume():
            async for e in bus.subscribe():
                received.append(e)
                break

        task = asyncio.create_task(consume())
        await asyncio.sleep(0.01)
        await publish_mission_started("m1", {"goal": "test"})
        await task

        assert received[0].event_type == "mission_started"
        assert received[0].data["mission_id"] == "m1"

    @pytest.mark.asyncio
    async def test_publish_mission_completed(self):
        bus = get_event_bus()
        received: list[OmnisEvent] = []

        async def consume():
            async for e in bus.subscribe():
                received.append(e)
                break

        task = asyncio.create_task(consume())
        await asyncio.sleep(0.01)
        await publish_mission_completed("m2", cost_usd=0.05)
        await task

        assert received[0].event_type == "mission_completed"
        assert received[0].data["cost_usd"] == 0.05

    @pytest.mark.asyncio
    async def test_publish_cost_updated(self):
        bus = get_event_bus()
        received: list[OmnisEvent] = []

        async def consume():
            async for e in bus.subscribe():
                received.append(e)
                break

        task = asyncio.create_task(consume())
        await asyncio.sleep(0.01)
        await publish_cost_updated("m3", 0.002, 200)
        await task

        assert received[0].event_type == "cost_updated"
        assert received[0].data["token_count"] == 200
