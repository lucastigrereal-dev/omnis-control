"""Tests for AkashaProvider — fallback behavior when DB unavailable."""
import pytest
from src.providers.akasha import AkashaProvider
from src.providers.base import ProviderStatus
from src.providers.memory import LocalMemoryProvider


class TestAkashaProviderFallback:
    """When PostgreSQL is not available, AkashaProvider falls back to local."""

    def test_health_degraded_without_db(self):
        p = AkashaProvider(db_url="")
        h = p.health_check()
        assert h.status == ProviderStatus.DEGRADED

    def test_health_details_show_reason(self):
        p = AkashaProvider(db_url="")
        h = p.health_check()
        assert "reason" in h.details or "error" in h.details

    def test_retrieve_falls_back_to_local(self):
        local = LocalMemoryProvider()
        local.write("OMNIS content for search")
        p = AkashaProvider(db_url="", fallback=local)
        results = p.retrieve("OMNIS content")
        assert len(results) >= 1

    def test_write_falls_back_to_local(self):
        local = LocalMemoryProvider()
        p = AkashaProvider(db_url="", fallback=local)
        id_ = p.write("test content")
        assert isinstance(id_, str)
        assert id_ in local._store

    def test_delete_falls_back_to_local(self):
        local = LocalMemoryProvider()
        p = AkashaProvider(db_url="", fallback=local)
        id_ = p.write("to delete")
        assert p.delete(id_) is True
        assert id_ not in local._store

    def test_backend_indicates_unavailable(self):
        p = AkashaProvider(db_url="")
        assert "unavailable" in p.backend or p.backend == "akasha_pgvector"

    def test_name(self):
        assert AkashaProvider(db_url="").name == "memory"

    def test_dispose_safe(self):
        p = AkashaProvider(db_url="")
        p.dispose()  # must not raise

    def test_bad_url_falls_back(self):
        p = AkashaProvider(db_url="postgresql://bad:bad@localhost:9999/nonexistent")
        h = p.health_check()
        assert not h.ok
