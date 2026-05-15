import hashlib
from src.akasha_runtime.models import AkashaMemoryDocument


class DedupKeyGenerator:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._keys_generated: int = 0

    def generate(self, doc: AkashaMemoryDocument, keys: list[str] | None = None) -> str:
        keys = keys or ["content_hash"]
        parts = []

        for key in sorted(keys):
            if key == "content_hash" and doc.content_hash:
                parts.append(f"ch:{doc.content_hash}")
            elif key == "content_raw":
                parts.append(f"cr:{self._hash(doc.content)}")
            elif key == "collection_content":
                parts.append(f"cc:{doc.collection}:{self._hash(doc.content)}")
            elif key == "event_type_collection":
                parts.append(f"etc:{doc.event_type}:{doc.collection}")
            elif key == "timestamp":
                parts.append(f"ts:{doc.created_at}")

        combined = "|".join(parts) if parts else self._hash(doc.content)
        result = self._hash(combined)
        self._keys_generated += 1
        return result

    def check_duplicate(
        self, doc: AkashaMemoryDocument, existing_keys: set[str], keys: list[str] | None = None
    ) -> bool:
        doc_key = self.generate(doc, keys)
        return doc_key in existing_keys

    def _hash(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

    @property
    def keys_generated(self) -> int:
        return self._keys_generated


class DedupRegistry:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._generator = DedupKeyGenerator(dry_run=dry_run)
        self._keys: set[str] = set()
        self._deduped_count: int = 0

    def register(self, doc: AkashaMemoryDocument, keys: list[str] | None = None) -> str:
        doc_key = self._generator.generate(doc, keys)
        self._keys.add(doc_key)
        return doc_key

    def is_duplicate(self, doc: AkashaMemoryDocument, keys: list[str] | None = None) -> bool:
        return self._generator.check_duplicate(doc, self._keys, keys)

    def filter_duplicates(
        self, docs: list[AkashaMemoryDocument], keys: list[str] | None = None
    ) -> tuple[list[AkashaMemoryDocument], list[AkashaMemoryDocument]]:
        unique = []
        duplicates = []
        for doc in docs:
            if self.is_duplicate(doc, keys):
                duplicates.append(doc)
                self._deduped_count += 1
            else:
                self.register(doc, keys)
                unique.append(doc)
        return unique, duplicates

    @property
    def key_count(self) -> int:
        return len(self._keys)

    @property
    def deduped_count(self) -> int:
        return self._deduped_count
