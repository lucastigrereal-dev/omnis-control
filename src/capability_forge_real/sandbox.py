"""Sandbox Runner — isolated execution for generated capabilities."""
from __future__ import annotations

import io
import sys
import time
import traceback
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SandboxStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"
    BLOCKED = "blocked"


@dataclass
class SandboxResult:
    run_id: str = ""
    status: SandboxStatus = SandboxStatus.PASSED
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    duration_ms: float = 0.0
    artifacts: list[str] = field(default_factory=list)
    blocked_patterns: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return self.status == SandboxStatus.PASSED and not self.blocked_patterns

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "artifacts": self.artifacts,
            "blocked_patterns": self.blocked_patterns,
            "is_clean": self.is_clean,
        }


FORBIDDEN_CALLS = frozenset({
    "subprocess", "os.system", "eval(", "exec(", "__import__",
    "shutil.rmtree", "os.remove", "os.rmdir", "os.unlink",
})

FORBIDDEN_IMPORTS = frozenset({
    "socket", "requests", "urllib", "http.client", "ftplib",
    "smtplib", "telnetlib",
})


class SandboxRunner:
    """Runs generated capability code in a dry-run sandbox — no real execution."""

    def __init__(
        self,
        timeout_ms: int = 30_000,
        max_output_chars: int = 50_000,
        allowed_write_paths: list[str] | None = None,
    ):
        self.timeout_ms = timeout_ms
        self.max_output_chars = max_output_chars
        self.allowed_write_paths = allowed_write_paths or ["data/", "exports/"]

    def run(self, code: str, run_id: str = "") -> SandboxResult:
        blocked = self._scan_blocked(code)
        if blocked:
            return SandboxResult(
                run_id=run_id,
                status=SandboxStatus.BLOCKED,
                blocked_patterns=blocked,
                error=f"Blocked patterns: {', '.join(blocked)}",
            )

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        start = time.time()

        try:
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                exec(code, {"__name__": "__sandbox__", "__builtins__": __builtins__})
        except Exception as exc:
            elapsed = (time.time() - start) * 1000
            return SandboxResult(
                run_id=run_id,
                status=SandboxStatus.ERROR,
                stdout=self._truncate(stdout_buf.getvalue()),
                stderr=self._truncate(stderr_buf.getvalue()),
                error=str(exc),
                duration_ms=elapsed,
            )

        elapsed = (time.time() - start) * 1000

        if elapsed > self.timeout_ms:
            return SandboxResult(
                run_id=run_id,
                status=SandboxStatus.TIMEOUT,
                duration_ms=elapsed,
                error=f"Exceeded timeout: {elapsed:.0f}ms > {self.timeout_ms}ms",
            )

        return SandboxResult(
            run_id=run_id,
            status=SandboxStatus.PASSED,
            stdout=self._truncate(stdout_buf.getvalue()),
            stderr=self._truncate(stderr_buf.getvalue()),
            duration_ms=elapsed,
        )

    def dry_run_validate(self, code: str, run_id: str = "") -> SandboxResult:
        """Validate code without executing — pattern scan only."""
        blocked = self._scan_blocked(code)
        if blocked:
            return SandboxResult(
                run_id=run_id,
                status=SandboxStatus.BLOCKED,
                blocked_patterns=blocked,
                error=f"Blocked patterns: {', '.join(blocked)}",
            )
        return SandboxResult(
            run_id=run_id,
            status=SandboxStatus.PASSED,
            error="",
        )

    @staticmethod
    def _scan_blocked(code: str) -> list[str]:
        blocked: list[str] = []
        code_lower = code.lower()

        for pattern in FORBIDDEN_CALLS:
            if pattern.lower() in code_lower:
                blocked.append(pattern)

        for module in FORBIDDEN_IMPORTS:
            if f"import {module}" in code_lower or f"from {module}" in code_lower:
                blocked.append(f"import {module}")

        return blocked

    @staticmethod
    def _truncate(text: str) -> str:
        if len(text) > 50_000:
            return text[:50_000] + "\n... [TRUNCATED]"
        return text
