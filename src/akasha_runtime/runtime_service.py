from src.akasha_runtime.models import (
    AkashaConnectionConfig,
    AkashaMemoryDocument,
    AkashaWritePolicy,
    AkashaHealthResult,
    AkashaEventMapping,
)
from src.akasha_runtime.health import AkashaHealthChecker
from src.akasha_runtime.write_policy import WritePolicyEnforcer
from src.akasha_runtime.event_mapper import AkashaEventMapper
from src.akasha_runtime.dedup import DedupRegistry
from src.akasha_runtime.file_adapter import FileBackedAkashaAdapter


class AkashaRuntimeService:
    def __init__(self, dry_run: bool = True, store_dir: str | None = None):
        self.dry_run = dry_run
        self.config: AkashaConnectionConfig | None = None
        self.policy: AkashaWritePolicy | None = None
        self.health_checker = AkashaHealthChecker(dry_run=dry_run)
        self.policy_enforcer = WritePolicyEnforcer(dry_run=dry_run)
        self.event_mapper = AkashaEventMapper(dry_run=dry_run)
        self.dedup_registry = DedupRegistry(dry_run=dry_run)
        self.adapter = FileBackedAkashaAdapter(dry_run=dry_run, store_dir=store_dir)

    def initialize(
        self,
        config: AkashaConnectionConfig,
        policy: AkashaWritePolicy | None = None,
        event_mappings: list[AkashaEventMapping] | None = None,
    ) -> AkashaHealthResult:
        self.config = config
        self.policy = policy or AkashaWritePolicy()
        if event_mappings:
            self.event_mapper.register_batch(event_mappings)

        self.adapter.connect(config)
        return self.health_checker.full_health_check(config)

    def remember(
        self,
        event_type: str,
        content: str,
        collection: str = "",
        metadata: dict | None = None,
    ) -> dict:
        if not self.config:
            return {"ok": False, "error": "not initialized"}

        target_collection = collection
        if not target_collection:
            mapped_collection, mapping = self.event_mapper.map_event(event_type)
            if mapped_collection:
                target_collection = mapped_collection
            else:
                target_collection = "default"

        doc = AkashaMemoryDocument(
            collection=target_collection,
            content=content,
            event_type=event_type,
            metadata=metadata or {},
        )

        if not self.policy_enforcer.validate(self.policy, doc):
            return {"ok": False, "error": "policy validation failed", "violations": self.policy_enforcer.violations}

        if self.dedup_registry.is_duplicate(doc):
            return {"ok": False, "error": "duplicate content"}

        require_approval = self.policy_enforcer.requires_approval(self.policy, doc)
        if require_approval and self.dry_run:
            pass

        self.dedup_registry.register(doc)
        written = self.adapter.write(doc, self.policy)
        return {
            "ok": written,
            "doc_id": doc.doc_id,
            "collection": target_collection,
            "requires_approval": require_approval,
        }

    def recall(self, doc_id: str, collection: str = "") -> dict:
        doc = self.adapter.read(doc_id, collection)
        if doc is None:
            return {"ok": False, "error": "not found"}
        return {"ok": True, "doc": doc.to_dict()}

    def query_collection(self, collection: str) -> dict:
        docs = self.adapter.list_collection(collection)
        return {"ok": True, "collection": collection, "count": len(docs), "docs": [d.to_dict() for d in docs]}

    def health(self) -> dict:
        if not self.config:
            return {"ok": False, "error": "not initialized"}
        result = self.health_checker.full_health_check(self.config)
        return {"ok": result.healthy, "healthy": result.healthy, "checks": result.checks, "errors": result.errors}

    @property
    def is_initialized(self) -> bool:
        return self.config is not None and self.adapter.is_connected
