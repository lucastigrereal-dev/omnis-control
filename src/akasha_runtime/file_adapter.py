import json
import os
from pathlib import Path
from src.akasha_runtime.models import (
    AkashaConnectionConfig,
    AkashaMemoryDocument,
    AkashaWritePolicy,
    AkashaConnectionStatus,
    AkashaHealthResult,
)


class FileBackedAkashaAdapter:
    STORE_DIR = "data/akasha_store"

    def __init__(self, dry_run: bool = True, store_dir: str | None = None):
        self.dry_run = dry_run
        self._store_path = Path(store_dir or self.STORE_DIR)
        self._connected = False
        self._docs_written: int = 0

    def connect(self, config: AkashaConnectionConfig) -> AkashaConnectionStatus:
        if not config.enabled:
            return AkashaConnectionStatus(
                config_id=config.config_id,
                connected=False,
                error_message="akasha not enabled",
            )

        if self.dry_run or not config.host:
            self._store_path.mkdir(parents=True, exist_ok=True)
            self._connected = True
            return AkashaConnectionStatus(
                config_id=config.config_id,
                connected=True,
                latency_ms=0.3,
                pool_available=1,
                pool_total=1,
            )

        return AkashaConnectionStatus(
            config_id=config.config_id,
            connected=False,
            error_message="real pgvector connection not implemented",
        )

    def disconnect(self) -> None:
        self._connected = False

    def health(self, config: AkashaConnectionConfig) -> AkashaHealthResult:
        status = self.connect(config)
        return AkashaHealthResult(
            config_id=config.config_id,
            healthy=status.connected,
            connection_status=status,
            checks={"connectivity": status.connected, "file_backed": True},
        )

    def write(self, doc: AkashaMemoryDocument, policy: AkashaWritePolicy) -> bool:
        if not self._connected:
            return False
        if not self.dry_run:
            return False

        collection_dir = self._store_path / doc.collection
        collection_dir.mkdir(parents=True, exist_ok=True)
        file_path = collection_dir / f"{doc.doc_id}.json"
        file_path.write_text(json.dumps(doc.to_dict(), indent=2), encoding="utf-8")
        self._docs_written += 1
        return True

    def write_batch(
        self, docs: list[AkashaMemoryDocument], policy: AkashaWritePolicy
    ) -> tuple[int, int]:
        written = 0
        failed = 0
        for doc in docs:
            if self.write(doc, policy):
                written += 1
            else:
                failed += 1
        return written, failed

    def read(self, doc_id: str, collection: str = "") -> AkashaMemoryDocument | None:
        if not collection:
            return self._find_by_id(doc_id)
        file_path = self._store_path / collection / f"{doc_id}.json"
        return self._load_doc(file_path)

    def _find_by_id(self, doc_id: str) -> AkashaMemoryDocument | None:
        for collection_dir in self._store_path.iterdir():
            if collection_dir.is_dir():
                file_path = collection_dir / f"{doc_id}.json"
                if file_path.exists():
                    return self._load_doc(file_path)
        return None

    def _load_doc(self, path: Path) -> AkashaMemoryDocument | None:
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return AkashaMemoryDocument.from_dict(data)

    def list_collection(self, collection: str) -> list[AkashaMemoryDocument]:
        collection_dir = self._store_path / collection
        if not collection_dir.exists():
            return []
        docs = []
        for f in sorted(collection_dir.glob("*.json")):
            doc = self._load_doc(f)
            if doc:
                docs.append(doc)
        return docs

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def docs_written(self) -> int:
        return self._docs_written
