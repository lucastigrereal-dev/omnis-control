"""Worker de fila — consome publish_queue com SKIP LOCKED."""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from .pipeline import PublishPipeline, JsonLStore

logger = logging.getLogger("omnis.publisher.worker")


class PublishWorker:
    """Worker que consome publish_queue e executa stage_publish."""

    def __init__(
        self,
        pipeline: PublishPipeline,
        db: JsonLStore,
        worker_id: str = "worker-1",
        poll_interval: int = 30,
    ):
        self.pipeline = pipeline
        self.db = db
        self.worker_id = worker_id
        self.poll_interval = poll_interval
        self._running = False

    async def start(self) -> None:
        self._running = True
        logger.info("Worker iniciado", extra={"worker_id": self.worker_id})
        while self._running:
            try:
                processed = await self._process_next()
                if not processed:
                    await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error("Erro no worker", extra={"error": str(e), "worker_id": self.worker_id})
                await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        self._running = False
        logger.info("Worker parado", extra={"worker_id": self.worker_id})

    async def _process_next(self) -> bool:
        item = await self.db.execute_raw(
            "UPDATE publish_queue SET locked_by = $1, locked_at = NOW() WHERE id = (SELECT id FROM publish_queue WHERE locked_at IS NULL AND next_attempt_at <= NOW() AND attempts < max_attempts ORDER BY priority DESC, next_attempt_at ASC LIMIT 1 FOR UPDATE SKIP LOCKED) RETURNING content_item_id",
            [self.worker_id],
        )
        if not item:
            return False

        content_id = item[0]["content_item_id"] if isinstance(item, list) and item else None
        if not content_id:
            return False

        start_time = datetime.now(timezone.utc)
        try:
            ctx = await self.pipeline.stage_publish(
                self.pipeline._load(content_id)
            )
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info("job_completed", extra={"content_id": content_id, "elapsed": elapsed, "status": ctx.status.value})
            return True
        except Exception as e:
            logger.error("Falha no processamento", extra={"content_id": content_id, "error": str(e)})
            return True
