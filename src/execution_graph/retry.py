"""Retry policy for execution graph steps."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BackoffStrategy(str, Enum):
    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"


RETRYABLE_STATUSES = frozenset({"failed", "timeout", "error"})


@dataclass
class RetryConfig:
    max_retries: int = 3
    backoff: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    retryable_statuses: frozenset[str] = field(default=RETRYABLE_STATUSES)

    def delay_for_attempt(self, attempt: int) -> float:
        if self.backoff == BackoffStrategy.FIXED:
            return self.base_delay_seconds
        if self.backoff == BackoffStrategy.LINEAR:
            return min(self.base_delay_seconds * attempt, self.max_delay_seconds)
        return min(self.base_delay_seconds * (2 ** (attempt - 1)), self.max_delay_seconds)

    def to_dict(self) -> dict:
        return {
            "max_retries": self.max_retries,
            "backoff": self.backoff.value,
            "base_delay_seconds": self.base_delay_seconds,
            "max_delay_seconds": self.max_delay_seconds,
            "retryable_statuses": sorted(self.retryable_statuses),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RetryConfig":
        return cls(
            max_retries=d.get("max_retries", 3),
            backoff=BackoffStrategy(d.get("backoff", "exponential")),
            base_delay_seconds=d.get("base_delay_seconds", 1.0),
            max_delay_seconds=d.get("max_delay_seconds", 60.0),
            retryable_statuses=frozenset(d.get("retryable_statuses", RETRYABLE_STATUSES)),
        )


@dataclass
class RetryPolicy:
    config: RetryConfig
    per_step: dict[str, RetryConfig] = field(default_factory=dict)

    def get_config(self, step_id: str) -> RetryConfig:
        return self.per_step.get(step_id, self.config)

    def is_retryable(self, status: str) -> bool:
        return status in self.config.retryable_statuses

    def to_dict(self) -> dict:
        return {
            "config": self.config.to_dict(),
            "per_step": {k: v.to_dict() for k, v in self.per_step.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RetryPolicy":
        config = RetryConfig.from_dict(d.get("config", {}))
        per_step = {
            k: RetryConfig.from_dict(v) for k, v in d.get("per_step", {}).items()
        }
        return cls(config=config, per_step=per_step)
