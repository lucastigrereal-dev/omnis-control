"""Tracer local — substitui Langfuse/OTel por JSONL em disco.

Sem dependencias externas. Registra spans, metricas e traces
em data/traces/ e data/metrics/.
"""
from __future__ import annotations
import json
import logging
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Optional

logger = logging.getLogger("omnis.observability.tracer_local")

TRACES_DIR = Path(__file__).parent.parent.parent / "data" / "traces"
METRICS_DIR = Path(__file__).parent.parent.parent / "data" / "metrics"


class _NoopSpan:
    """Span no-op para uso quando tracer esta em modo silencioso."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def record_exception(self, exc: Exception) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class LocalTracer:
    """Tracer que persiste spans em JSONL."""

    def __init__(self, name: str = "omnis", traces_dir: Optional[Path] = None):
        self.name = name
        self.dir = traces_dir or TRACES_DIR
        self.dir.mkdir(parents=True, exist_ok=True)
        self._enabled = True

    @contextmanager
    def start_as_current_span(self, span_name: str, **kwargs) -> Generator:
        span_id = uuid.uuid4().hex[:12]
        start = time.time()
        attrs: Dict[str, Any] = {}
        try:
            span = _LocalSpan(span_id, span_name, attrs)
            yield span
        except Exception as exc:
            self._write_span(span_id, span_name, attrs, start, error=str(exc))
            raise
        else:
            self._write_span(span_id, span_name, attrs, start)
        finally:
            pass

    def _write_span(
        self, span_id: str, name: str,
        attributes: Dict, start: float, error: Optional[str] = None,
    ) -> None:
        elapsed = time.time() - start
        entry = {
            "span_id": span_id,
            "trace_name": self.name,
            "span_name": name,
            "attributes": attributes,
            "duration_ms": round(elapsed * 1000, 2),
            "error": error,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        log_path = self.dir / f"{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled


class _LocalSpan:
    """Span que coleta atributos e persiste no tracer."""

    def __init__(self, span_id: str, name: str, attributes: Dict):
        self._span_id = span_id
        self._name = name
        self._attributes = attributes

    def set_attribute(self, key: str, value: Any) -> None:
        self._attributes[key] = value

    def record_exception(self, exc: Exception) -> None:
        self._attributes["exception"] = str(exc)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


# --- Singleton para uso global ---
_default_tracer: Optional[LocalTracer] = None


def get_tracer(name: str = "omnis") -> LocalTracer:
    """Retorna o tracer singleton."""
    global _default_tracer
    if _default_tracer is None:
        _default_tracer = LocalTracer(name)
    return _default_tracer


def record_metric(name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """Registra metrica em JSONL."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "metric": name,
        "value": value,
        "labels": labels or {},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    log_path = METRICS_DIR / f"{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.debug("metric recorded", extra={"metric": name, "value": value})


def skill_traced(skill_name: str, model: str = "unknown"):
    """Decorator para tracing de skills."""
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await fn(*args, **kwargs)
                return result
            except Exception as e:
                raise
            finally:
                elapsed = time.time() - start
                record_metric("skill.execution_time", elapsed, {"skill": skill_name, "model": model})
        return wrapper
    return decorator
