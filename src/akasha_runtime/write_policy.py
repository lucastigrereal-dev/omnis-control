from src.akasha_runtime.models import AkashaWritePolicy, AkashaMemoryDocument


class WritePolicyEnforcer:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._violations: list[dict] = []

    def validate(self, policy: AkashaWritePolicy, doc: AkashaMemoryDocument) -> bool:
        self._violations = []

        if not policy.allowed_collections:
            return True

        if doc.collection not in policy.allowed_collections:
            self._violations.append({
                "reason": "collection_not_allowed",
                "collection": doc.collection,
                "allowed": policy.allowed_collections,
            })
            return False

        if policy.require_embedding and not doc.embedding:
            self._violations.append({"reason": "embedding_required"})
            return False

        return True

    def validate_batch(
        self, policy: AkashaWritePolicy, docs: list[AkashaMemoryDocument]
    ) -> tuple[list[AkashaMemoryDocument], list[dict]]:
        allowed = []
        rejected = []

        if len(docs) > policy.max_batch_size:
            return [], [{"reason": "batch_too_large", "size": len(docs), "max": policy.max_batch_size}]

        seen_hashes: set[str] = set()
        for doc in docs:
            if not self.validate(policy, doc):
                rejected.append({"doc_id": doc.doc_id, "violations": list(self._violations)})
                continue

            if policy.dedup_enabled:
                content_hash = doc.content_hash or doc.content
                if content_hash in seen_hashes:
                    rejected.append({"doc_id": doc.doc_id, "reason": "duplicate"})
                    continue
            seen_hashes.add(doc.content_hash or doc.content)

            allowed.append(doc)

        return allowed, rejected

    def requires_approval(self, policy: AkashaWritePolicy, doc: AkashaMemoryDocument) -> bool:
        if policy.require_approval:
            return True
        return False

    @property
    def violations(self) -> list[dict]:
        return list(self._violations)
