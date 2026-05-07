"""Logging estruturado JSON com redacao de dados sensiveis."""
from __future__ import annotations
import logging
import json
import sys
import re
from datetime import datetime, timezone
from typing import Any, Dict

SENSITIVE_PATTERNS = [
    (re.compile(r"(token|key|secret|password|bearer)[=: ]+[\w\-\.]+", re.IGNORECASE), r"\1=***REDACTED***"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "***EMAIL***"),
]


class StructuredFormatter(logging.Formatter):
    """Formata logs como JSON estruturado."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": self._redact(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "thread", "threadName", "exc_info", "exc_text",
                "message", "taskName",
            ):
                log_entry[key] = self._redact(str(value)) if isinstance(value, str) else value
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False, default=str)

    def _redact(self, text: str) -> str:
        for pattern, replacement in SENSITIVE_PATTERNS:
            text = pattern.sub(replacement, text)
        return text


def setup_logging(level: str = "INFO", json_output: bool = True) -> None:
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        StructuredFormatter() if json_output else logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )
    )
    root.handlers.clear()
    root.addHandler(handler)
    for noisy in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
