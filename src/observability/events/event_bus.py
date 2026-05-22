"""Unified Event Bus — Redis Streams backbone of OMNIS observability.

All events flow through this bus. Append-only. Replay-safe. Audit-safe.

Architecture:
    Publishers → Redis Streams → Consumer Groups → Handlers
                                   └→ Dead Letter Queue

Each stream is a named channel (e.g. omnis:events:missions).
Consumer groups enable fan-out to multiple subscribers.
The dead letter queue captures events that fail processing.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable

from ..schemas.event_schema import ALL_EVENT_TYPES, EventEnvelope, EventType

logger = logging.getLogger(__name__)


class EventBus:
    """Redis Streams-backed event bus.

    Usage:
        bus = EventBus(redis_url="redis://localhost:6379")
        await bus.connect()

        # Publish
        event = EventEnvelope(event_type=EventType.MISSION_STARTED, ...)
        await bus.publish("omnis:events:missions", event)

        # Subscribe
        async def handle(event): ...
        await bus.subscribe("omnis:events:missions", "my_group", "consumer_1", handle)
    """

    STREAM_PREFIX = "omnis:events"
    STREAMS = {
        "missions": f"{STREAM_PREFIX}:missions",
        "tasks": f"{STREAM_PREFIX}:tasks",
        "waves": f"{STREAM_PREFIX}:waves",
        "providers": f"{STREAM_PREFIX}:providers",
        "memory": f"{STREAM_PREFIX}:memory",
        "telemetry": f"{STREAM_PREFIX}:telemetry",
        "health": f"{STREAM_PREFIX}:health",
        "anomalies": f"{STREAM_PREFIX}:anomalies",
        "audit": f"{STREAM_PREFIX}:audit",
        "dead_letter": f"{STREAM_PREFIX}:dead_letter",
    }

    MAX_STREAM_LEN = 100_000
    DEAD_LETTER_MAX_LEN = 10_000

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self._redis_url = redis_url
        self._redis: Any = None
        self._handlers: dict[str, list[Callable]] = {}
        self._connected = False

    async def connect(self) -> None:
        import redis.asyncio as redis

        self._redis = redis.from_url(self._redis_url, decode_responses=True)
        await self._redis.ping()
        self._connected = True
        logger.info("EventBus connected to %s", self._redis_url)

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.close()
            self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def publish(self, stream: str, event: EventEnvelope) -> str:
        """Publish an event to a stream. Returns the stream entry ID."""
        if not self._connected:
            raise RuntimeError("EventBus not connected")

        data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "source": event.source,
            "sequence": str(event.sequence),
            "mission_id": event.mission_id or "",
            "task_id": event.task_id or "",
            "wave_id": event.wave_id or "",
            "trace_id": event.trace_id or "",
            "span_id": event.span_id or "",
            "parent_span_id": event.parent_span_id or "",
            "payload": json.dumps(event.payload),
            "payload_schema_version": event.payload_schema_version,
            "idempotency_key": event.idempotency_key,
            "delta_tokens": str(event.delta_tokens) if event.delta_tokens else "",
            "delta_cost_usd": str(event.delta_cost_usd) if event.delta_cost_usd else "",
            "latency_ms": str(event.latency_ms) if event.latency_ms else "",
            "tags": json.dumps(event.tags),
            "severity": event.severity,
        }

        entry_id = await self._redis.xadd(stream, data, maxlen=self.MAX_STREAM_LEN)
        logger.debug("Published %s to %s (id=%s)", event.event_type.value, stream, entry_id)
        return entry_id

    async def subscribe(
        self,
        stream: str,
        group: str,
        consumer: str,
        handler: Callable[[EventEnvelope], Any],
        start_from: str = "$",
    ) -> None:
        """Subscribe to a stream with a consumer group.

        Args:
            stream: Stream name (use EventBus.STREAMS keys)
            group: Consumer group name
            consumer: Consumer name within group
            handler: Async callback receiving EventEnvelope
            start_from: "$" for new only, "0" for replay from beginning
        """
        if not self._connected:
            raise RuntimeError("EventBus not connected")

        try:
            await self._redis.xgroup_create(stream, group, id="0", mkstream=True)
        except Exception:
            pass  # group already exists

        self._handlers.setdefault(stream, []).append(handler)

        logger.info("Subscribed %s/%s to %s (from=%s)", group, consumer, stream, start_from)

        while True:
            try:
                entries = await self._redis.xreadgroup(
                    group, consumer, {stream: ">"}, count=10, block=5000
                )
                for stream_name, messages in entries:
                    for msg_id, data in messages:
                        await self._dispatch(stream_name, msg_id, data)
                        await self._redis.xack(stream_name, group, msg_id)
            except Exception as e:
                logger.error("EventBus consumer error: %s", e)

    async def _dispatch(self, stream: str, msg_id: str, data: dict) -> None:
        event = self._deserialize(data)
        if event is None:
            await self._move_to_dead_letter(stream, msg_id, data, "deserialization_failed")
            return

        handlers = self._handlers.get(stream, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                logger.exception("Handler failed for %s on %s", event.event_type, stream)

    async def _move_to_dead_letter(
        self, source_stream: str, msg_id: str, data: dict, reason: str
    ) -> None:
        data["_dead_reason"] = reason
        data["_source_stream"] = source_stream
        data["_dead_at"] = datetime.now(timezone.utc).isoformat()
        await self._redis.xadd(
            self.STREAMS["dead_letter"], data, maxlen=self.DEAD_LETTER_MAX_LEN
        )

    def _deserialize(self, data: dict) -> EventEnvelope | None:
        try:
            return EventEnvelope(
                event_id=data["event_id"],
                event_type=EventType(data["event_type"]),
                timestamp=datetime.fromisoformat(data["timestamp"]),
                source=data["source"],
                sequence=int(data["sequence"]),
                mission_id=data.get("mission_id") or None,
                task_id=data.get("task_id") or None,
                wave_id=data.get("wave_id") or None,
                trace_id=data.get("trace_id") or None,
                span_id=data.get("span_id") or None,
                parent_span_id=data.get("parent_span_id") or None,
                payload=json.loads(data.get("payload", "{}")),
                payload_schema_version=data.get("payload_schema_version", "1.0.0"),
                idempotency_key=data.get("idempotency_key", ""),
                delta_tokens=int(data["delta_tokens"]) if data.get("delta_tokens") else None,
                delta_cost_usd=float(data["delta_cost_usd"]) if data.get("delta_cost_usd") else None,
                latency_ms=float(data["latency_ms"]) if data.get("latency_ms") else None,
                tags=json.loads(data.get("tags", "{}")),
                severity=data.get("severity", "info"),
            )
        except Exception:
            logger.exception("Failed to deserialize event from stream")
            return None

    async def replay_stream(
        self,
        stream: str,
        handler: Callable[[EventEnvelope], Any],
        start: str = "0",
        end: str = "+",
        batch_size: int = 100,
    ) -> int:
        """Replay events from a stream for recovery or audit.

        Returns the number of events replayed.
        """
        if not self._connected:
            raise RuntimeError("EventBus not connected")

        count = 0
        cursor = start
        while True:
            results = await self._redis.xrange(stream, cursor, end, count=batch_size)
            if not results:
                break
            for msg_id, data in results:
                event = self._deserialize(data)
                if event:
                    await handler(event)
                    count += 1
                cursor = msg_id
            if len(results) < batch_size:
                break
        logger.info("Replayed %d events from %s", count, stream)
        return count

    async def get_dead_letter_events(self, limit: int = 100) -> list[dict]:
        """Retrieve events from the dead letter queue for inspection."""
        results = await self._redis.xrange(
            self.STREAMS["dead_letter"], "-", "+", count=limit
        )
        return [{"msg_id": msg_id, **data} for msg_id, data in results]

    async def health_check(self) -> dict:
        """Check if the event bus is healthy."""
        try:
            await self._redis.ping()
            info = await self._redis.info("server")
            return {
                "status": "healthy",
                "redis_version": info.get("redis_version"),
                "uptime_days": info.get("uptime_in_days"),
                "connected_clients": info.get("connected_clients"),
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Singleton
_event_bus: EventBus | None = None


def get_event_bus(redis_url: str = "redis://localhost:6379") -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus(redis_url=redis_url)
    return _event_bus
