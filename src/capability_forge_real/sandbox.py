"""Sandbox Runner — isolated subprocess execution for generated capabilities.

Security model: user code is NEVER exec()'d in the parent process.
Code runs in a fresh Python subprocess via tempfile → subprocess.run().
Even if the subprocess executes arbitrary OS calls, the parent (OMNIS)
process memory and state cannot be compromised.

Static scanner (FORBIDDEN_CALLS / FORBIDDEN_IMPORTS) remains as a
first-layer defence to catch common patterns before subprocess starts.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
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
    """Runs generated capability code in an isolated subprocess.

    Execution model:
      1. Static scan — known forbidden patterns are blocked immediately.
      2. Subprocess execution — code is written to a tempfile and executed
         via a fresh Python interpreter. The parent process cannot be
         compromised regardless of what runs inside the subprocess.
    """

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
        return self._exec_subprocess(code, run_id)

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
        return SandboxResult(run_id=run_id, status=SandboxStatus.PASSED, error="")

    def _exec_subprocess(self, code: str, run_id: str) -> SandboxResult:
        """Write code to tempfile and run in isolated subprocess."""
        start = time.time()
        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                tmp_path = f.name

            proc = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout_ms / 1000,
            )
            elapsed = (time.time() - start) * 1000

            if proc.returncode != 0:
                return SandboxResult(
                    run_id=run_id,
                    status=SandboxStatus.ERROR,
                    stdout=self._truncate(proc.stdout),
                    stderr=self._truncate(proc.stderr),
                    error=(proc.stderr.strip() or f"exit code {proc.returncode}")[:500],
                    duration_ms=elapsed,
                )

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
                stdout=self._truncate(proc.stdout),
                stderr=self._truncate(proc.stderr),
                duration_ms=elapsed,
            )

        except subprocess.TimeoutExpired:
            elapsed = (time.time() - start) * 1000
            return SandboxResult(
                run_id=run_id,
                status=SandboxStatus.TIMEOUT,
                duration_ms=elapsed,
                error=f"Exceeded timeout: {elapsed:.0f}ms > {self.timeout_ms}ms",
            )
        except Exception as exc:
            elapsed = (time.time() - start) * 1000
            return SandboxResult(
                run_id=run_id,
                status=SandboxStatus.ERROR,
                duration_ms=elapsed,
                error=f"sandbox_internal:{exc}",
            )
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

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
