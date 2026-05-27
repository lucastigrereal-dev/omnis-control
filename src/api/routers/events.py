"""Router SSE — Server-Sent Events para KRATOS."""
import asyncio
import json
import time

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()


async def event_generator(request: Request):
    while True:
        if await request.is_disconnected():
            break
        yield f"data: {json.dumps({'type': 'heartbeat', 'ts': time.time()})}\n\n"
        await asyncio.sleep(30)


@router.get("")
async def sse_events(request: Request):
    return StreamingResponse(event_generator(request), media_type="text/event-stream")
