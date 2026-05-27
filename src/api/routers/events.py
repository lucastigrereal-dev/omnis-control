"""Router SSE — Server-Sent Events para KRATOS.

W18-B2: integrado ao EventBus para broadcasting real.
Subscribers recebem eventos publicados de qualquer módulo OMNIS.
Heartbeat a cada 30s para manter conexão viva.
"""
import asyncio
import json
import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from src.api.auth import require_api_key
from src.api.event_bus import OmnisEvent, get_event_bus

router = APIRouter()

_HEARTBEAT_INTERVAL = 30  # segundos
_EVENT_TYPE_MAP = {
    "mission_started": "mission:update",
    "mission_completed": "mission:update",
    "mission_failed": "mission:update",
    "cost_updated": "cost:update",
}


def _to_sse(event_type: str, data: dict, ts: float) -> str:
    payload = json.dumps({"type": event_type, "data": data, "ts": ts})
    return f"event: {event_type}\ndata: {payload}\n\n"


def _normalize_event(event: OmnisEvent) -> tuple[str, dict]:
    canonical = _EVENT_TYPE_MAP.get(event.event_type, event.event_type)
    data = dict(event.data or {})
    if event.event_type == "mission_started":
        data.setdefault("status", "running")
    elif event.event_type == "mission_completed":
        data.setdefault("status", "completed")
    elif event.event_type == "mission_failed":
        data.setdefault("status", "failed")
    return canonical, data


async def event_stream_generator(request: Request):
    """Generator SSE integrado ao EventBus com heartbeat."""
    bus = get_event_bus()

    # Enviar heartbeat inicial imediatamente (confirma conexão)
    yield f"data: {json.dumps({'type': 'connected', 'ts': time.time()})}\n\n"

    heartbeat_task: asyncio.Task | None = None

    async def heartbeat():
        """Envia heartbeat periódico enquanto subscriber está conectado."""
        while True:
            await asyncio.sleep(_HEARTBEAT_INTERVAL)
            await bus.publish("heartbeat", {"ts": time.time()})

    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        async for event in bus.subscribe():
            if await request.is_disconnected():
                break
            canonical_type, canonical_data = _normalize_event(event)
            yield _to_sse(canonical_type, canonical_data, event.ts)
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()


@router.get("", dependencies=[Depends(require_api_key)])
async def sse_events(request: Request):
    """SSE endpoint — KRATOS conecta aqui para receber eventos em tempo real.

    Eventos disponíveis:
    - connected: confirmação de conexão
    - heartbeat: keepalive a cada 30s
    - mission_started / mission_completed / mission_failed
    - cost_updated
    - agent_result
    """
    return StreamingResponse(
        event_stream_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Desativa buffering Nginx
        },
    )


@router.get("/stream", dependencies=[Depends(require_api_key)])
async def sse_events_stream(request: Request):
    """Alias explícito para contrato v1 (/events/stream e /live/stream via prefix)."""
    return await sse_events(request)


@router.get("/status", dependencies=[Depends(require_api_key)])
async def sse_status():
    """Status do EventBus — quantos subscribers SSE estão conectados."""
    bus = get_event_bus()
    return {
        "subscribers": bus.subscriber_count(),
        "status": "ok",
        "ts": time.time(),
    }
