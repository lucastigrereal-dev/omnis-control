"""TracingProvider — observability abstraction for OMNIS.

Backends (in priority order):
1. LangfuseProvider  — cloud tracing with cost/latency/replay (optional dep)
2. OTelProvider      — OpenTelemetry standard (optional dep)
3. LocalJSONLProvider — built-in fallback, no external deps

OMNIS core only imports TracingProvider and SpanContext — never a backend directly.
"""
from __future__ import annotations

import json
import time
import uuid
from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator, Optional

from src.providers.base import Provider, ProviderHealth, ProviderStatus


@dataclass
class SpanContext:
    """A single trace span. Wraps framework-specific span transparently."""
    trace_id: str
    span_id: str
    name: str
    started_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    input: Any = None
    output: Any = None
    error: Optional[str] = None

    def set_output(self, value: Any) -> None:
        self.output = value

    def set_error(self, error: str) -> None:
        self.error = error

    def duration_ms(self) -> float:
        return (time.time() - self.started_at) * 1000


class TracingProvider(Provider):
    """Abstract tracing provider. Use registry.get('tracing') to get instance."""

    @property
    def name(self) -> str:
        return "tracing"

    @abstractmethod
    @contextmanager
    def span(
        self,
        name: str,
        *,
        trace_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        input: Any = None,
    ) -> Generator[SpanContext, None, None]:
        """Context manager that creates a span and finalizes it on exit."""

    @abstractmethod
    def trace(
        self,
        name: str,
        input: Any = None,
        output: Any = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Record a one-shot trace event. Returns trace_id."""

    @abstractmethod
    def flush(self) -> None:
        """Flush buffered spans to backend."""


# ── Built-in fallback: LocalJSONLProvider ──────────────────────────────────

_DEFAULT_TRACES_DIR = Path("data/traces")


class LocalJSONLProvider(TracingProvider):
    """Zero-dependency tracing — writes spans to JSONL on disk.

    Replaces the existing observability/tracer_local.py with a Provider interface.
    Compatible with existing data/traces/ directory.
    """

    def __init__(self, traces_dir: Optional[Path] = None) -> None:
        self._dir = Path(traces_dir or _DEFAULT_TRACES_DIR)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._buffer: list[dict[str, Any]] = []

    @property
    def backend(self) -> str:
        return "local_jsonl"

    def health_check(self) -> ProviderHealth:
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            return ProviderHealth(
                status=ProviderStatus.OK,
                provider_name=self.name,
                backend=self.backend,
                details={"traces_dir": str(self._dir)},
            )
        except Exception as e:
            return ProviderHealth(
                status=ProviderStatus.UNAVAILABLE,
                provider_name=self.name,
                backend=self.backend,
                details={"error": str(e)},
            )

    @contextmanager
    def span(
        self,
        name: str,
        *,
        trace_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        input: Any = None,
    ) -> Generator[SpanContext, None, None]:
        ctx = SpanContext(
            trace_id=trace_id or str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            name=name,
            metadata=metadata or {},
            input=input,
        )
        try:
            yield ctx
        except Exception as e:
            ctx.set_error(str(e))
            raise
        finally:
            self._write(ctx)

    def trace(
        self,
        name: str,
        input: Any = None,
        output: Any = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        ctx = SpanContext(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            name=name,
            input=input,
            output=output,
            metadata=metadata or {},
        )
        self._write(ctx)
        return ctx.trace_id

    def flush(self) -> None:
        for entry in self._buffer:
            self._append_to_file(entry)
        self._buffer.clear()

    def _write(self, ctx: SpanContext) -> None:
        entry = {
            "trace_id": ctx.trace_id,
            "span_id": ctx.span_id,
            "name": ctx.name,
            "started_at": ctx.started_at,
            "duration_ms": round(ctx.duration_ms(), 2),
            "metadata": ctx.metadata,
            "input": ctx.input,
            "output": ctx.output,
            "error": ctx.error,
        }
        self._append_to_file(entry)

    def _append_to_file(self, entry: dict[str, Any]) -> None:
        from datetime import datetime, timezone
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = self._dir / f"traces_{date_str}.jsonl"
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except OSError:
            pass  # non-critical: trace write failure never blocks execution


# ── Optional: LangfuseProvider ─────────────────────────────────────────────

class LangfuseProvider(TracingProvider):
    """Langfuse cloud tracing provider.

    Requires: pip install langfuse
    Env vars: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST (optional)

    Falls back gracefully if Langfuse is not installed or credentials missing.
    """

    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        fallback: Optional[TracingProvider] = None,
    ) -> None:
        import os
        self._pk = public_key or os.environ.get("LANGFUSE_PUBLIC_KEY", "")
        self._sk = secret_key or os.environ.get("LANGFUSE_SECRET_KEY", "")
        self._host = host or os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
        self._fallback = fallback or LocalJSONLProvider()
        self._client: Any = None
        self._available = False
        self._init()

    def _init(self) -> None:
        try:
            from langfuse import Langfuse  # type: ignore
            if self._pk and self._sk:
                self._client = Langfuse(
                    public_key=self._pk,
                    secret_key=self._sk,
                    host=self._host,
                )
                self._available = True
        except ImportError:
            pass

    @property
    def backend(self) -> str:
        return "langfuse" if self._available else f"local_jsonl(langfuse_unavailable)"

    def health_check(self) -> ProviderHealth:
        if not self._available:
            return ProviderHealth(
                status=ProviderStatus.DEGRADED,
                provider_name=self.name,
                backend=self.backend,
                details={"reason": "langfuse not installed or credentials missing", "fallback": "local_jsonl"},
            )
        try:
            self._client.auth_check()
            return ProviderHealth(
                status=ProviderStatus.OK,
                provider_name=self.name,
                backend=self.backend,
                details={"host": self._host},
            )
        except Exception as e:
            return ProviderHealth(
                status=ProviderStatus.DEGRADED,
                provider_name=self.name,
                backend=self.backend,
                details={"error": str(e), "fallback": "local_jsonl"},
            )

    @contextmanager
    def span(
        self,
        name: str,
        *,
        trace_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        input: Any = None,
    ) -> Generator[SpanContext, None, None]:
        if not self._available:
            with self._fallback.span(name, trace_id=trace_id, metadata=metadata, input=input) as ctx:
                yield ctx
            return

        lf_trace = self._client.trace(
            id=trace_id or str(uuid.uuid4()),
            name=name,
            input=input,
            metadata=metadata or {},
        )
        ctx = SpanContext(
            trace_id=lf_trace.id,
            span_id=str(uuid.uuid4()),
            name=name,
            metadata=metadata or {},
            input=input,
        )
        try:
            yield ctx
        except Exception as e:
            ctx.set_error(str(e))
            lf_trace.update(output={"error": str(e)}, metadata={**(metadata or {}), "error": str(e)})
            raise
        finally:
            lf_trace.update(
                output=ctx.output,
                metadata={**(metadata or {}), "duration_ms": ctx.duration_ms()},
            )

    def trace(
        self,
        name: str,
        input: Any = None,
        output: Any = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        if not self._available:
            return self._fallback.trace(name, input=input, output=output, metadata=metadata)
        lf_trace = self._client.trace(name=name, input=input, output=output, metadata=metadata or {})
        return lf_trace.id

    def flush(self) -> None:
        if self._available:
            self._client.flush()
        self._fallback.flush()

    def dispose(self) -> None:
        self.flush()
