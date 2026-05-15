import tempfile

from src.akasha_runtime.models import (
    AkashaConnectionConfig,
    AkashaWritePolicy,
    AkashaEventMapping,
)
from src.akasha_runtime.runtime_service import AkashaRuntimeService


class TestAkashaRuntimeIntegrationSmoke:
    def store_dir(self):
        return tempfile.mkdtemp(prefix="akasha_int_")

    def test_full_lifecycle_remember_recall(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        svc.initialize(
            AkashaConnectionConfig(enabled=True),
            policy=AkashaWritePolicy(require_embedding=False, allowed_collections=["audit", "logs"]),
            event_mappings=[
                AkashaEventMapping(event_type="EXECUTION_COMPLETED", target_collection="logs"),
                AkashaEventMapping(event_type="DECISION_LOGGED", target_collection="audit"),
            ],
        )

        r1 = svc.remember("EXECUTION_COMPLETED", "Task X finished", metadata={"priority": 1})
        r2 = svc.remember("DECISION_LOGGED", "Approved deploy", metadata={"approved_by": "lucas"})

        assert r1["ok"] is True
        assert r1["collection"] == "logs"
        assert r2["ok"] is True
        assert r2["collection"] == "audit"

        recalled = svc.recall(r1["doc_id"], collection="logs")
        assert recalled["ok"] is True
        assert recalled["doc"]["content"] == "Task X finished"

    def test_unmapped_event_goes_to_default(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        svc.initialize(
            AkashaConnectionConfig(enabled=True),
            policy=AkashaWritePolicy(require_embedding=False),
        )
        result = svc.remember("UNKNOWN_EVENT", "something happened")
        assert result["ok"] is True
        assert result["collection"] == "default"

    def test_policy_rejects_wrong_collection(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        svc.initialize(
            AkashaConnectionConfig(enabled=True),
            policy=AkashaWritePolicy(require_embedding=False, allowed_collections=["events"]),
        )
        result = svc.remember("EVENT", "content", collection="forbidden")
        assert result["ok"] is False
        assert result["error"] == "policy validation failed"

    def test_duplicate_across_calls(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        svc.initialize(
            AkashaConnectionConfig(enabled=True),
            policy=AkashaWritePolicy(require_embedding=False),
        )

        svc.remember("EVENT", "unique A")
        svc.remember("EVENT", "unique B")

        dup = svc.remember("EVENT", "unique A")
        assert dup["ok"] is False
        assert dup["error"] == "duplicate content"

    def test_query_collection_returns_all(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        svc.initialize(
            AkashaConnectionConfig(enabled=True),
            policy=AkashaWritePolicy(require_embedding=False),
        )

        svc.remember("EVENT", "doc1", collection="events")
        svc.remember("EVENT", "doc2", collection="events")
        svc.remember("EVENT", "doc3", collection="events")

        result = svc.query_collection("events")
        assert result["count"] == 3
        assert result["ok"] is True

    def test_not_initialized_blocks_all_ops(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        assert svc.remember("E", "c") == {"ok": False, "error": "not initialized"}
        assert svc.recall("x") == {"ok": False, "error": "not found"}
        assert svc.health() == {"ok": False, "error": "not initialized"}

    def test_event_mapping_approval_flag(self):
        svc = AkashaRuntimeService(dry_run=True, store_dir=self.store_dir())
        svc.initialize(
            AkashaConnectionConfig(enabled=True),
            policy=AkashaWritePolicy(require_embedding=False),
            event_mappings=[
                AkashaEventMapping(
                    event_type="DEPLOY_REQUESTED", target_collection="security",
                    require_approval=True,
                ),
            ],
        )
        result = svc.remember("DEPLOY_REQUESTED", "deploy to production")
        assert result["ok"] is True
        assert result["requires_approval"] is True
