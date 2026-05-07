"""Dry-run wrapper — atalho para executar pipeline local com logging.

Uso:
    from src.pipeline_local.dry_run import dry_run_pipeline
    result = dry_run_pipeline("queue-id-123")
"""
import logging
from typing import Optional

from .service import PipelineLocalService
from .models import PipelineRunResult

logger = logging.getLogger("omnis.pipeline_local.dry_run")


def dry_run_pipeline(queue_item_id: str) -> PipelineRunResult:
    """Executa pipeline dry-run completo para um queue item.

    Args:
        queue_item_id: ID do item na Content Queue.

    Returns:
        PipelineRunResult com status e evidências.
    """
    service = PipelineLocalService()
    logger.info("Pipeline dry-run iniciado para queue item %s", queue_item_id)
    result = service.run_local_content_pipeline(queue_item_id)
    logger.info(
        "Pipeline dry-run concluído: status=%s warnings=%d",
        result.status, len(result.warnings),
    )
    return result
