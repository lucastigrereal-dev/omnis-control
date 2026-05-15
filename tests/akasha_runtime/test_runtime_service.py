import tempfile

from src.akasha_runtime.models import (
    AkashaConnectionConfig,
    AkashaWritePolicy,
    AkashaEventMapping,
)
from src.akasha_runtime.runtime_service import AkashaRuntimeService


class TestAkashaRuntimeService:
    def store_dir(self):
        return tempfile.mkdtemp(prefix="akasha_rt_")

    def test_initialize(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        result = svc.initialize(AkashaConnectionConfig(enabled=True))
        assert result.healthy is True
        assert svc.is_initialized is True

    def test_remember_with_event_mapping(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        svc.initialize(
            AkashaConnectionConfig(enabled=True),
            policy=AkashaWritePolicy(require_embedding=False, allowed_collections=["execution_logs"]),
            event_mappings=[
                AkashaEventMapping(event_type="EXECUTION_COMPLETED", target_collection="execution_logs"),
            ],
        )
        result = svc.remember("EXECUTION_COMPLETED", "Task completed successfully")
        assert result["ok"] is True
        assert result["collection"] == "execution_logs"
        assert result["requires_approval"] is False

    def test_remember_duplicate_rejected(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        svc.initialize(
            AkashaConnectionConfig(enabled=True),
            policy=AkashaWritePolicy(require_embedding=False),
        )
        svc.remember("EVENT_X", "same content")
        result = svc.remember("EVENT_X", "same content")
        assert result["ok"] is False
        assert result["error"] == "duplicate content"

    def test_remember_not_initialized(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        result = svc.remember("EVENT", "content")
        assert result["ok"] is False
        assert result["error"] == "not initialized"

    def test_recall_found(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        svc.initialize(
            AkashaConnectionConfig(enabled=True),
            policy=AkashaWritePolicy(require_embedding=False),
        )
        r = svc.remember("EVENT", "hello", collection="events")
        doc = svc.recall(r["doc_id"], collection="events")
        assert doc["ok"] is True
        assert doc["doc"]["content"] == "hello"

    def test_recall_not_found(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        svc.initialize(AkashaConnectionConfig(enabled=True))
        result = svc.recall("nonexistent")
        assert result["ok"] is False

    def test_query_collection(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        svc.initialize(
            AkashaConnectionConfig(enabled=True),
            policy=AkashaWritePolicy(require_embedding=False),
        )
        svc.remember("EVENT", "a", collection="events")
        svc.remember("EVENT", "b", collection="events")
        result = svc.query_collection("events")
        assert result["ok"] is True
        assert result["count"] == 2

    def test_health_not_initialized(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        result = svc.health()
        assert result["ok"] is False
        assert result["error"] == "not initialized"

    def test_health_initialized(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        svc.initialize(AkashaConnectionConfig(enabled=True))
        result = svc.health()
        assert result["ok"] is True
