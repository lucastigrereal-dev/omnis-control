"""OMNIS API — Structured JSON Logging (W19).

Provides:
- JsonFormatter: formats LogRecord as JSON with standard fields
- setup_logging(): configures root logger + optional file handler
- StructuredLoggingMiddleware: FastAPI middleware that logs each request
  as a JSON line to logs/api_access.jsonl

Graceful degradation: if the log directory is not writable, the API
continues to run — logging failures are silently swallowed.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from logging import LogRecord
from pathlib import Path
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_ROOT = Path(os.getenv("OMNIS_ROOT", Path(__file__).resolve().parents[2]))
_DEFAULT_ACCESS_LOG = _ROOT / "logs" / "api_access.jsonl"


# ---------------------------------------------------------------------------
# JsonFormatter
# ---------------------------------------------------------------------------


class JsonFormatter(logging.Formatter):
    """Format a LogRecord as a single JSON line.

    Output fields: ts, level, logger, message, module, line.
    Any extra fields added to the LogRecord are included as-is.
    """

    def format(self, record: LogRecord) -> str:  # type: ignore[override]
        payload: dict = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        # Include any extra fields attached to the record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno",
                "pathname", "filename", "module", "exc_info",
                "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "message",
            } and not key.startswith("_"):
                payload[key] = value
        try:
            return json.dumps(payload, ensure_ascii=False, default=str)
        except Exception:  # noqa: BLE001
            return json.dumps({"ts": payload["ts"], "level": "ERROR",
                                "message": "log serialization failed"})


# ---------------------------------------------------------------------------
# setup_logging
# ---------------------------------------------------------------------------


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Configure root logger with JSON formatter and optional file handler.

    Args:
        log_level: Logging level string (default "INFO").
        log_file: Optional path to a log file. If None, only StreamHandler
                  (stdout) is used.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    formatter = JsonFormatter()

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid adding duplicate handlers on repeated calls
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except Exception:  # noqa: BLE001
            # Graceful: if the file cannot be opened, continue without it
            pass


# ---------------------------------------------------------------------------
# StructuredLoggingMiddleware
# ---------------------------------------------------------------------------


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Log each HTTP request as a JSON line to logs/api_access.jsonl.

    Logged fields: ts, method, path, status_code, duration_ms, client_ip.

    Graceful degradation: if the log directory is not writable or any
    error occurs while writing the log entry, the exception is silently
    swallowed and the API response is returned normally.
    """

    def __init__(self, app, access_log: Optional[Path] = None) -> None:
        super().__init__(app)
        self._access_log = Path(access_log) if access_log else _DEFAULT_ACCESS_LOG

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.monotonic()
        response: Response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        try:
            self._write_entry(
                ts=datetime.now(tz=timezone.utc).isoformat(),
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_ip=self._get_client_ip(request),
            )
        except Exception:  # noqa: BLE001
            # Graceful degradation — never crash the API because of logging
            pass
        return response

    # ------------------------------------------------------------------

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return ""

    def _write_entry(self, **fields) -> None:
        try:
            self._access_log.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(fields, ensure_ascii=False) + "\n"
            with self._access_log.open("a", encoding="utf-8") as fh:
                fh.write(line)
        except Exception:  # noqa: BLE001
            # Graceful degradation — never crash the API because of logging
            pass
