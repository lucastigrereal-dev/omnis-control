"""RetryPolicy — política de retry configurável por nó."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NodeRetryConfig:
    max_retries: int = 3
    # Extensível: backoff_s, jitter, retry_on_exceptions (para fases futuras)


@dataclass
class RetryPolicy:
    """Política de retry por nó. Nós sem config usam default."""
    default: NodeRetryConfig = field(default_factory=NodeRetryConfig)
    nodes: dict[str, NodeRetryConfig] = field(default_factory=dict)

    def max_retries_for(self, node: str) -> int:
        return self.nodes.get(node, self.default).max_retries

    def should_retry(self, node: str, attempts: int) -> bool:
        return attempts < self.max_retries_for(node)

    @classmethod
    def default_policy(cls) -> "RetryPolicy":
        return cls()

    @classmethod
    def strict(cls) -> "RetryPolicy":
        """0 retries em todos os nós."""
        return cls(default=NodeRetryConfig(max_retries=0))
