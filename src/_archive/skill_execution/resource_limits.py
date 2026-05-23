"""Skill Resource Limits — timeout, memory, and CPU constraints for skill execution."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LimitViolation(str, Enum):
    TIMEOUT = "timeout"
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    NETWORK = "network"


@dataclass
class ResourceLimits:
    timeout_ms: int = 300_000
    max_memory_mb: int = 512
    max_cpu_percent: int = 80
    max_disk_mb: int = 100
    max_network_calls: int = 0
    kill_on_violation: bool = True
    violations: list[LimitViolation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeout_ms": self.timeout_ms,
            "max_memory_mb": self.max_memory_mb,
            "max_cpu_percent": self.max_cpu_percent,
            "max_disk_mb": self.max_disk_mb,
            "max_network_calls": self.max_network_calls,
            "kill_on_violation": self.kill_on_violation,
            "violations": [v.value for v in self.violations],
        }

    @classmethod
    def safe_defaults(cls) -> "ResourceLimits":
        """Conservative limits for untrusted skills — no network, tight timeout."""
        return cls(
            timeout_ms=60_000,
            max_memory_mb=256,
            max_cpu_percent=50,
            max_disk_mb=50,
            max_network_calls=0,
            kill_on_violation=True,
        )

    @classmethod
    def generous_defaults(cls) -> "ResourceLimits":
        """Relaxed limits for trusted internal skills."""
        return cls(
            timeout_ms=600_000,
            max_memory_mb=2048,
            max_cpu_percent=90,
            max_disk_mb=500,
            max_network_calls=10,
            kill_on_violation=False,
        )


class ResourceLimitEnforcer:
    """Enforces resource limits on skill execution — deterministic planning only."""

    @staticmethod
    def check_limits(
        limits: ResourceLimits,
        elapsed_ms: int = 0,
        memory_used_mb: int = 0,
        cpu_percent: int = 0,
        disk_used_mb: int = 0,
        network_calls: int = 0,
    ) -> list[LimitViolation]:
        violations: list[LimitViolation] = []

        if elapsed_ms > limits.timeout_ms:
            violations.append(LimitViolation.TIMEOUT)
        if memory_used_mb > limits.max_memory_mb:
            violations.append(LimitViolation.MEMORY)
        if cpu_percent > limits.max_cpu_percent:
            violations.append(LimitViolation.CPU)
        if disk_used_mb > limits.max_disk_mb:
            violations.append(LimitViolation.DISK)
        if network_calls > limits.max_network_calls:
            violations.append(LimitViolation.NETWORK)

        return violations

    @staticmethod
    def is_within_limits(limits: ResourceLimits, **usage) -> bool:
        return len(ResourceLimitEnforcer.check_limits(limits, **usage)) == 0

    @staticmethod
    def should_kill(limits: ResourceLimits, violations: list[LimitViolation]) -> bool:
        return limits.kill_on_violation and len(violations) > 0
