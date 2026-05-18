"""Base Provider protocol — every OMNIS provider implements this."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProviderStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class ProviderHealth:
    status: ProviderStatus
    provider_name: str
    backend: str
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == ProviderStatus.OK


class Provider(ABC):
    """Base class for all OMNIS providers.

    OMNIS core depends only on this interface — never on concrete backends.
    Concrete providers inject the real framework (Langfuse, mem0, etc.) via adapters.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g. 'tracing', 'memory')."""

    @property
    @abstractmethod
    def backend(self) -> str:
        """Active backend name (e.g. 'langfuse', 'local_jsonl')."""

    @abstractmethod
    def health_check(self) -> ProviderHealth:
        """Return current health. Never raises — returns UNAVAILABLE on error."""

    def dispose(self) -> None:
        """Release resources. Safe to call multiple times."""
