from src.akasha_runtime.models import AkashaWritePolicy, AkashaMemoryDocument
from src.akasha_runtime.write_policy import WritePolicyEnforcer


class TestWritePolicyEnforcer:
    def test_empty_policy_allows(self):
        enforcer = WritePolicyEnforcer()
        policy = AkashaWritePolicy(allowed_collections=[])
        doc = AkashaMemoryDocument(collection="any")
        assert enforcer.validate(policy, doc) is True

    def test_collection_allowed(self):
        enforcer = WritePolicyEnforcer()
        policy = AkashaWritePolicy(require_embedding=False, allowed_collections=["events", "decisions"])
        doc = AkashaMemoryDocument(collection="events")
        assert enforcer.validate(policy, doc) is True

    def test_collection_not_allowed(self):
        enforcer = WritePolicyEnforcer()
        policy = AkashaWritePolicy(allowed_collections=["events"])
        doc = AkashaMemoryDocument(collection="secrets")
        assert enforcer.validate(policy, doc) is False
        assert any(v["reason"] == "collection_not_allowed" for v in enforcer.violations)

    def test_embedding_required_missing(self):
        enforcer = WritePolicyEnforcer()
        policy = AkashaWritePolicy(require_embedding=True, allowed_collections=["events"])
        doc = AkashaMemoryDocument(collection="events", embedding=[])
        assert enforcer.validate(policy, doc) is False
        assert any(v["reason"] == "embedding_required" for v in enforcer.violations)

    def test_embedding_not_required(self):
        enforcer = WritePolicyEnforcer()
        policy = AkashaWritePolicy(require_embedding=False, allowed_collections=["events"])
        doc = AkashaMemoryDocument(collection="events", embedding=[])
        assert enforcer.validate(policy, doc) is True

    def test_validate_batch_within_limit(self):
        enforcer = WritePolicyEnforcer()
        policy = AkashaWritePolicy(max_batch_size=5, dedup_enabled=False)
        docs = [AkashaMemoryDocument(collection="e", content=str(i)) for i in range(3)]
        allowed, rejected = enforcer.validate_batch(policy, docs)
        assert len(allowed) == 3
        assert len(rejected) == 0

    def test_validate_batch_exceeds_limit(self):
        enforcer = WritePolicyEnforcer()
        policy = AkashaWritePolicy(max_batch_size=2)
        docs = [AkashaMemoryDocument() for _ in range(5)]
        allowed, rejected = enforcer.validate_batch(policy, docs)
        assert len(allowed) == 0
        assert len(rejected) == 1
        assert rejected[0]["reason"] == "batch_too_large"

    def test_validate_batch_dedup_by_content_hash(self):
        enforcer = WritePolicyEnforcer()
        policy = AkashaWritePolicy(max_batch_size=10, dedup_enabled=True)
        docs = [
            AkashaMemoryDocument(content_hash="abc", collection="e"),
            AkashaMemoryDocument(content_hash="abc", collection="e"),
            AkashaMemoryDocument(content_hash="def", collection="e"),
        ]
        allowed, rejected = enforcer.validate_batch(policy, docs)
        assert len(allowed) == 2
        assert len(rejected) == 1

    def test_validate_batch_dedup_by_content_fallback(self):
        enforcer = WritePolicyEnforcer()
        policy = AkashaWritePolicy(max_batch_size=10, dedup_enabled=True)
        docs = [
            AkashaMemoryDocument(content="same", collection="e"),
            AkashaMemoryDocument(content="same", collection="e"),
        ]
        allowed, rejected = enforcer.validate_batch(policy, docs)
        assert len(allowed) == 1
        assert len(rejected) == 1

    def test_validate_batch_rejects_disallowed_collection(self):
        enforcer = WritePolicyEnforcer()
        policy = AkashaWritePolicy(require_embedding=False, allowed_collections=["events"])
        docs = [
            AkashaMemoryDocument(collection="events"),
            AkashaMemoryDocument(collection="secrets"),
        ]
        allowed, rejected = enforcer.validate_batch(policy, docs)
        assert len(allowed) == 1
        assert len(rejected) == 1

    def test_requires_approval_when_policy_set(self):
        enforcer = WritePolicyEnforcer()
        policy = AkashaWritePolicy(require_approval=True)
        doc = AkashaMemoryDocument()
        assert enforcer.requires_approval(policy, doc) is True

    def test_requires_approval_when_not_set(self):
        enforcer = WritePolicyEnforcer()
        policy = AkashaWritePolicy(require_approval=False)
        doc = AkashaMemoryDocument()
        assert enforcer.requires_approval(policy, doc) is False
