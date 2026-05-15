from src.akasha_runtime.models import (
    AkashaConnectionConfig,
    AkashaConnectionStatus,
    AkashaHealthResult,
    AkashaWritePolicy,
    AkashaMemoryDocument,
    AkashaEventMapping,
)


class TestAkashaConnectionConfig:
    def test_defaults(self):
        c = AkashaConnectionConfig()
        assert c.dry_run is True
        assert c.enabled is False
        assert c.port == 5432
        assert c.db_name == "akasha"

    def test_roundtrip(self):
        c = AkashaConnectionConfig(host="pg.local", port=5433, pool_size=10)
        d = c.to_dict()
        c2 = AkashaConnectionConfig.from_dict(d)
        assert c2.host == "pg.local"
        assert c2.port == 5433
        assert c2.pool_size == 10

    def test_enabled_flag(self):
        c = AkashaConnectionConfig(enabled=True)
        assert c.enabled is True


class TestAkashaConnectionStatus:
    def test_default_disconnected(self):
        s = AkashaConnectionStatus()
        assert s.connected is False
        assert s.latency_ms == 0.0
        assert s.pool_available == 0

    def test_healthy_status(self):
        s = AkashaConnectionStatus(connected=True, latency_ms=1.5, pool_available=3, pool_total=5)
        assert s.connected is True
        assert s.latency_ms == 1.5
        assert s.pool_available == 3

    def test_error_status(self):
        s = AkashaConnectionStatus(error_message="connection refused")
        assert s.connected is False
        assert s.error_message == "connection refused"

    def test_roundtrip(self):
        s = AkashaConnectionStatus(connected=True, latency_ms=2.0, pool_available=4, pool_total=5)
        d = s.to_dict()
        s2 = AkashaConnectionStatus.from_dict(d)
        assert s2.connected is True
        assert s2.latency_ms == 2.0


class TestAkashaHealthResult:
    def test_default_unhealthy(self):
        r = AkashaHealthResult()
        assert r.healthy is False
        assert r.checks == {}

    def test_healthy_with_checks(self):
        r = AkashaHealthResult(healthy=True, checks={"connectivity": True, "auth": True})
        assert r.healthy is True
        assert r.checks["connectivity"] is True

    def test_roundtrip_with_connection_status(self):
        cs = AkashaConnectionStatus(connected=True, latency_ms=1.0)
        r = AkashaHealthResult(healthy=True, connection_status=cs, checks={"pg": True})
        d = r.to_dict()
        r2 = AkashaHealthResult.from_dict(d)
        assert r2.healthy is True
        assert r2.connection_status is not None
        assert r2.connection_status.latency_ms == 1.0

    def test_roundtrip_without_connection_status(self):
        r = AkashaHealthResult(healthy=False, errors=["timeout"])
        d = r.to_dict()
        r2 = AkashaHealthResult.from_dict(d)
        assert r2.healthy is False
        assert r2.connection_status is None
        assert "timeout" in r2.errors


class TestAkashaWritePolicy:
    def test_defaults(self):
        p = AkashaWritePolicy()
        assert p.dry_run is True
        assert p.max_batch_size == 100
        assert p.dedup_enabled is True
        assert "content_hash" in p.dedup_keys

    def test_custom_collections(self):
        p = AkashaWritePolicy(allowed_collections=["events", "decisions"])
        assert len(p.allowed_collections) == 2

    def test_approval_required(self):
        p = AkashaWritePolicy(require_approval=True, require_embedding=False)
        assert p.require_approval is True
        assert p.require_embedding is False

    def test_roundtrip(self):
        p = AkashaWritePolicy(name="strict", max_batch_size=50, dedup_keys=["hash", "timestamp"])
        d = p.to_dict()
        p2 = AkashaWritePolicy.from_dict(d)
        assert p2.name == "strict"
        assert p2.max_batch_size == 50
        assert p2.dedup_keys == ["hash", "timestamp"]


class TestAkashaMemoryDocument:
    def test_default_document(self):
        d = AkashaMemoryDocument()
        assert d.doc_id.startswith("akd_")
        assert d.source_system == "omnis"

    def test_content_document(self):
        d = AkashaMemoryDocument(collection="events", content="test content")
        assert d.collection == "events"
        assert d.content == "test content"

    def test_with_embedding(self):
        d = AkashaMemoryDocument(embedding=[0.1, 0.2, 0.3], content_hash="abc123")
        assert len(d.embedding) == 3
        assert d.content_hash == "abc123"

    def test_roundtrip(self):
        d = AkashaMemoryDocument(
            collection="decisions", content="approved: deploy",
            event_type="DECISION_LOGGED", content_hash="def456",
        )
        data = d.to_dict()
        d2 = AkashaMemoryDocument.from_dict(data)
        assert d2.collection == "decisions"
        assert d2.content == "approved: deploy"
        assert d2.event_type == "DECISION_LOGGED"


class TestAkashaEventMapping:
    def test_default_mapping(self):
        m = AkashaEventMapping()
        assert m.mapping_id.startswith("akm_")
        assert m.priority == 0

    def test_event_to_collection(self):
        m = AkashaEventMapping(
            event_type="EXECUTION_COMPLETED",
            target_collection="execution_logs",
            priority=5,
        )
        assert m.event_type == "EXECUTION_COMPLETED"
        assert m.target_collection == "execution_logs"

    def test_roundtrip(self):
        m = AkashaEventMapping(event_type="REQUEST_RECEIVED", target_collection="audit", priority=3)
        d = m.to_dict()
        m2 = AkashaEventMapping.from_dict(d)
        assert m2.event_type == "REQUEST_RECEIVED"
        assert m2.target_collection == "audit"
        assert m2.priority == 3
