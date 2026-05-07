"""Metrics Spine — P0.9. Camada local de metricas de execucao."""
from __future__ import annotations

from typing import Any, Dict

from src.metrics.recorder import MetricsRecorder
from src.metrics.errors import (
    MetricsError,
    StoreOperationError,
    InvalidMetricError,
    RunNotFoundError,
)

_default_recorder: MetricsRecorder | None = None


def get_recorder(base_dir: str | None = None) -> MetricsRecorder:
    """Retorna instancia de MetricsRecorder (cria sob demanda)."""
    global _default_recorder
    if _default_recorder is None or base_dir is not None:
        _default_recorder = MetricsRecorder(base_dir)
    return _default_recorder


def quick_record_metric(name: str, value: float = 1.0, **kwargs) -> Dict[str, Any]:
    """Conveniencia: grava metrica rapida sem segurar referencia ao recorder."""
    return get_recorder().record_metric(name, value, **kwargs).model_dump()


__all__ = [
    "MetricsRecorder",
    "get_recorder",
    "quick_record_metric",
    "MetricsError",
    "StoreOperationError",
    "InvalidMetricError",
    "RunNotFoundError",
]
