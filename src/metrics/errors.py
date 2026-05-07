"""Metrics Spine errors — P0.9."""
from __future__ import annotations


class MetricsError(Exception):
    """Erro base da Metrics Spine."""


class StoreOperationError(MetricsError):
    """Falha de I/O no storage."""


class InvalidMetricError(MetricsError):
    """MetricEvent com dados invalidos."""


class RunNotFoundError(MetricsError):
    """Run ID nao encontrado."""
