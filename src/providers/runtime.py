"""RuntimeProvider — skill/tool execution abstraction for OMNIS.

Backends:
1. SubprocessRuntimeProvider — built-in, executes skills via subprocess (current behavior)
2. FastMCPRuntimeProvider    — MCP tool execution via FastMCP (optional)
3. MockRuntimeProvider       — for tests and dry-run

Wraps and replaces the direct subprocess calls in runners/skill_runner.py.
"""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from src.providers.base import Provider, ProviderHealth, ProviderStatus


@dataclass
class RuntimeResult:
    """Result of executing a skill/tool via RuntimeProvider."""
    skill_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "dry_run": self.dry_run,
        }


class RuntimeProvider(Provider):
    """Abstract runtime provider. Use registry.get('runtime') to get instance."""

    @property
    def name(self) -> str:
        return "runtime"

    @abstractmethod
    def run(
        self,
        skill_id: str,
        args: dict[str, Any],
        *,
        dry_run: bool = True,
        timeout: float = 30.0,
    ) -> RuntimeResult:
        """Execute a skill. dry_run=True simulates without real subprocess."""

    @abstractmethod
    def available(self, skill_id: str) -> bool:
        """Check if a skill is available for execution."""


# ── Built-in: MockRuntimeProvider ──────────────────────────────────────────

class MockRuntimeProvider(RuntimeProvider):
    """Test and dry-run runtime. Never executes real processes."""

    def __init__(self, outcomes: Optional[dict[str, Any]] = None) -> None:
        self._outcomes = outcomes or {}

    @property
    def backend(self) -> str:
        return "mock"

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider_name=self.name,
            backend=self.backend,
        )

    def run(
        self,
        skill_id: str,
        args: dict[str, Any],
        *,
        dry_run: bool = True,
        timeout: float = 30.0,
    ) -> RuntimeResult:
        if skill_id in self._outcomes:
            outcome = self._outcomes[skill_id]
            if isinstance(outcome, Exception):
                return RuntimeResult(skill_id=skill_id, success=False, error=str(outcome), dry_run=True)
            return RuntimeResult(skill_id=skill_id, success=True, output=outcome, dry_run=True)
        return RuntimeResult(
            skill_id=skill_id,
            success=True,
            output={"mock": True, "skill_id": skill_id, "args": args},
            dry_run=True,
        )

    def available(self, skill_id: str) -> bool:
        return True


# ── Built-in: SubprocessRuntimeProvider ────────────────────────────────────

class SubprocessRuntimeProvider(RuntimeProvider):
    """Executes skills via subprocess — wraps existing skill_runner behavior."""

    def __init__(self, skills_path: Optional[str] = None) -> None:
        import os
        self._skills_path = skills_path or os.environ.get("SKILLS_PATH", "")

    @property
    def backend(self) -> str:
        return "subprocess"

    def health_check(self) -> ProviderHealth:
        import shutil
        python_ok = shutil.which("python") is not None
        return ProviderHealth(
            status=ProviderStatus.OK if python_ok else ProviderStatus.DEGRADED,
            provider_name=self.name,
            backend=self.backend,
            details={"python_available": python_ok, "skills_path": self._skills_path},
        )

    def run(
        self,
        skill_id: str,
        args: dict[str, Any],
        *,
        dry_run: bool = True,
        timeout: float = 30.0,
    ) -> RuntimeResult:
        import time
        if dry_run:
            return RuntimeResult(
                skill_id=skill_id,
                success=True,
                output={"dry_run": True, "skill_id": skill_id},
                dry_run=True,
            )
        try:
            from src.runners.skill_runner import run_skill  # type: ignore
            t0 = time.time()
            output = run_skill(skill_id, args, timeout=timeout)
            return RuntimeResult(
                skill_id=skill_id,
                success=True,
                output=output,
                duration_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            return RuntimeResult(skill_id=skill_id, success=False, error=str(e))

    def available(self, skill_id: str) -> bool:
        try:
            from src.runners.skill_runner import skill_exists  # type: ignore
            return skill_exists(skill_id)
        except Exception:
            return False
