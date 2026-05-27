"""W18-B2 — Event Bus SSE para KRATOS.

Pub/Sub assíncrono para broadcasting de eventos OMNIS → KRATOS via SSE.

Padrão:
    - Publisher: qualquer módulo OMNIS importa get_event_bus() e chama publish()
    - Subscriber: SSE endpoint chama subscribe() e itera o gerador

Eventos publicados automaticamente:
    - mission_started / mission_completed / mission_failed
    - cost_updated
    - agent_result
    - heartbeat (keepalive a cada 30s pelo SSE endpoint)

Thread-safety: asyncio.Queue — seguro para uso com asyncio.gather()
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator
from weakref import WeakSet

_MISSION_UPDATE_STATUS_BY_LEGACY_EVENT: dict[str, str] = {
    "mission_started": "running",
    "mission_completed": "completed",
    "mission_failed": "failed",
    "mission_paused": "paused",
    "mission_resumed": "running",
    "mission_cancelled": "cancelled",
}


@dataclass
class OmnisEvent:
    """Envelope de evento OMNIS."""

    event_type: str
    data: dict
    ts: float = field(default_factory=time.time)

    def to_sse(self) -> str:
        """Serializa para formato SSE (text/event-stream)."""
        payload = json.dumps({"type": self.event_type, "data": self.data, "ts": self.ts})
        return f"event: {self.event_type}\ndata: {payload}\n\n"

    def to_dict(self) -> dict:
        return {"type": self.event_type, "data": self.data, "ts": self.ts}


class EventBus:
    """Bus de eventos pub/sub baseado em asyncio.Queue.

    Cada subscriber recebe seu próprio queue — sem broadcast bloqueante.
    Subscribers são removidos automaticamente via WeakSet quando desconectados.
    """

    def __init__(self, maxsize: int = 100) -> None:
        self._queues: list[asyncio.Queue[OmnisEvent | None]] = []
        self._maxsize = maxsize
        self._lock = asyncio.Lock()

    async def subscribe(self) -> AsyncGenerator[OmnisEvent, None]:
        """Context-managed subscriber. Cede eventos até o cliente desconectar.

        Uso:
            async for event in bus.subscribe():
                yield event.to_sse()
        """
        q: asyncio.Queue[OmnisEvent | None] = asyncio.Queue(maxsize=self._maxsize)
        async with self._lock:
            self._queues.append(q)
        try:
            while True:
                event = await q.get()
                if event is None:
                    # Sinal de encerramento
                    break
                yield event
        finally:
            async with self._lock:
                try:
                    self._queues.remove(q)
                except ValueError:
                    pass

    async def publish(self, event_type: str, data: dict) -> int:
        """Publica um evento para todos os subscribers conectados.

        Returns: número de subscribers que receberam o evento.
        """
        event = OmnisEvent(event_type=event_type, data=data)
        compat_event = _build_contract_v1_alias_event(event_type, data)
        count = 0
        async with self._lock:
            queues = list(self._queues)
        for q in queues:
            try:
                q.put_nowait(event)
                count += 1
                if compat_event is not None:
                    q.put_nowait(compat_event)
            except asyncio.QueueFull:
                # Subscriber lento — descarta evento (non-blocking)
                pass
        return count

    def publish_sync(self, event_type: str, data: dict) -> None:
        """Versão síncrona de publish — cria task no loop corrente se disponível.

        Seguro para chamar de código síncrono (ex: nodes do grafo).
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.publish(event_type, data))
        except RuntimeError:
            # Sem event loop ativo — ignora silenciosamente (testes, CLI)
            pass

    def subscriber_count(self) -> int:
        return len(self._queues)

    async def shutdown(self) -> None:
        """Envia sinal de encerramento para todos os subscribers."""
        async with self._lock:
            queues = list(self._queues)
        for q in queues:
            try:
                q.put_nowait(None)
            except asyncio.QueueFull:
                pass


# ── Singleton global ──────────────────────────────────────────────────────────

_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Retorna o singleton global do EventBus.

    Thread-safe (Python GIL + asyncio single-threaded).
    """
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


def reset_event_bus() -> None:
    """Reseta o singleton — usado apenas em testes."""
    global _bus
    _bus = None


def _build_contract_v1_alias_event(event_type: str, data: dict) -> OmnisEvent | None:
    """Gera alias canônico v1 para eventos de missão sem quebrar legado."""
    status = _MISSION_UPDATE_STATUS_BY_LEGACY_EVENT.get(event_type)
    if status is None:
        return None

    alias_data = {
        "mission_id": data.get("mission_id"),
        "status": status,
        "legacy_event": event_type,
        **data,
    }
    return OmnisEvent(event_type="mission:update", data=alias_data)


# ── Helpers de publicação ─────────────────────────────────────────────────────

async def publish_mission_started(mission_id: str, brief: dict | None = None) -> None:
    bus = get_event_bus()
    await bus.publish("mission_started", {"mission_id": mission_id, "brief": brief or {}})


async def publish_mission_completed(mission_id: str, cost_usd: float = 0.0) -> None:
    bus = get_event_bus()
    await bus.publish("mission_completed", {"mission_id": mission_id, "cost_usd": cost_usd})


async def publish_mission_failed(mission_id: str, error: str) -> None:
    bus = get_event_bus()
    await bus.publish("mission_failed", {"mission_id": mission_id, "error": error})


async def publish_cost_updated(mission_id: str, cost_usd: float, token_count: int) -> None:
    bus = get_event_bus()
    await bus.publish(
        "cost_updated",
        {"mission_id": mission_id, "cost_usd": cost_usd, "token_count": token_count},
    )


async def publish_agent_result(
    mission_id: str, agent_name: str, squad: str, success: bool
) -> None:
    bus = get_event_bus()
    await bus.publish(
        "agent_result",
        {
            "mission_id": mission_id,
            "agent": agent_name,
            "squad": squad,
            "success": success,
        },
    )
