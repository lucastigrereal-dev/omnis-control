"""Mem0Provider — mem0 cloud memory backend for OMNIS.

Requires: pip install mem0ai
Env vars: MEM0_API_KEY

Falls back to LocalMemoryProvider when not available.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from src.providers.base import ProviderHealth, ProviderStatus
from src.providers.memory import MemoryProvider, MemoryResult, LocalMemoryProvider


class Mem0Provider(MemoryProvider):
    """MemoryProvider backed by mem0 cloud.

    Handles multi-user episodic memory, semantic retrieval, and writeback.
    Falls back to LocalMemoryProvider when mem0 is not installed or key missing.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: str = "omnis",
        fallback: Optional[MemoryProvider] = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("MEM0_API_KEY", "")
        self._user_id = user_id
        self._fallback = fallback or LocalMemoryProvider()
        self._client: Any = None
        self._available = False
        self._init()

    def _init(self) -> None:
        if not self._api_key:
            return
        try:
            from mem0 import MemoryClient  # type: ignore
            self._client = MemoryClient(api_key=self._api_key)
            self._available = True
        except ImportError:
            self._available = False

    @property
    def backend(self) -> str:
        return f"mem0(user={self._user_id})" if self._available else "local_memory(mem0_unavailable)"

    def health_check(self) -> ProviderHealth:
        if not self._available:
            return ProviderHealth(
                status=ProviderStatus.DEGRADED,
                provider_name=self.name,
                backend=self.backend,
                details={
                    "reason": "mem0 not installed or MEM0_API_KEY not set",
                    "fallback": "local_memory",
                    "api_key_set": bool(self._api_key),
                },
            )
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider_name=self.name,
            backend=self.backend,
            details={"user_id": self._user_id},
        )

    def retrieve(self, query: str, *, k: int = 5, filter: Optional[dict] = None) -> list[MemoryResult]:
        if not self._available:
            return self._fallback.retrieve(query, k=k, filter=filter)
        try:
            results = self._client.search(query, user_id=self._user_id, limit=k)
            return [
                MemoryResult(
                    id=r.get("id", ""),
                    content=r.get("memory", ""),
                    score=r.get("score", 1.0),
                    source=self.backend,
                    metadata=r.get("metadata", {}),
                )
                for r in (results or [])
            ]
        except Exception:
            return self._fallback.retrieve(query, k=k, filter=filter)

    def write(self, content: str, *, id: Optional[str] = None, metadata: Optional[dict] = None) -> str:
        if not self._available:
            return self._fallback.write(content, id=id, metadata=metadata)
        try:
            result = self._client.add(
                [{"role": "user", "content": content}],
                user_id=self._user_id,
                metadata=metadata or {},
            )
            # mem0 returns list of results; use first id
            if result and isinstance(result, list):
                return result[0].get("id", id or "")
            return id or ""
        except Exception:
            return self._fallback.write(content, id=id, metadata=metadata)

    def delete(self, id: str) -> bool:
        if not self._available:
            return self._fallback.delete(id)
        try:
            self._client.delete(id)
            return True
        except Exception:
            return False
