import json
import tempfile
from pathlib import Path

from src.akasha_runtime.models import (
    AkashaConnectionConfig,
    AkashaMemoryDocument,
    AkashaWritePolicy,
)
from src.akasha_runtime.file_adapter import FileBackedAkashaAdapter


class TestFileBackedAkashaAdapter:
    def store_dir(self):
        return tempfile.mkdtemp(prefix="akasha_test_")

    def test_connect_dry_run(self):
        store = self.store_dir()
        adapter = FileBackedAkashaAdapter(dry_run=True, store_dir=store)
        config = AkashaConnectionConfig(enabled=True)
        status = adapter.connect(config)
        assert status.connected is True
        assert adapter.is_connected is True

    def test_connect_not_enabled(self):
        store = self.store_dir()
        adapter = FileBackedAkashaAdapter(dry_run=True, store_dir=store)
        config = AkashaConnectionConfig(enabled=False)
        status = adapter.connect(config)
        assert status.connected is False

    def test_connect_real_not_implemented(self):
        store = self.store_dir()
        adapter = FileBackedAkashaAdapter(dry_run=False, store_dir=store)
        config = AkashaConnectionConfig(enabled=True, host="pg.local")
        status = adapter.connect(config)
        assert status.connected is False

    def test_disconnect(self):
        store = self.store_dir()
        adapter = FileBackedAkashaAdapter(dry_run=True, store_dir=store)
        config = AkashaConnectionConfig(enabled=True)
        adapter.connect(config)
        adapter.disconnect()
        assert adapter.is_connected is False

    def test_write_document(self):
        store = self.store_dir()
        adapter = FileBackedAkashaAdapter(dry_run=True, store_dir=store)
        adapter.connect(AkashaConnectionConfig(enabled=True))
        doc = AkashaMemoryDocument(collection="events", content="test")
        policy = AkashaWritePolicy()
        assert adapter.write(doc, policy) is True
        assert adapter.docs_written == 1

    def test_write_not_connected(self):
        store = self.store_dir()
        adapter = FileBackedAkashaAdapter(dry_run=True, store_dir=store)
        doc = AkashaMemoryDocument(collection="events", content="test")
        assert adapter.write(doc, AkashaWritePolicy()) is False

    def test_write_read_roundtrip(self):
        store = self.store_dir()
        adapter = FileBackedAkashaAdapter(dry_run=True, store_dir=store)
        adapter.connect(AkashaConnectionConfig(enabled=True))
        doc = AkashaMemoryDocument(
            collection="events", content="hello world",
            event_type="REQUEST_RECEIVED", source_system="omnis",
        )
        adapter.write(doc, AkashaWritePolicy())
        loaded = adapter.read(doc.doc_id, collection="events")
        assert loaded is not None
        assert loaded.content == "hello world"
        assert loaded.collection == "events"
        assert loaded.event_type == "REQUEST_RECEIVED"

    def test_read_by_id_only(self):
        store = self.store_dir()
        adapter = FileBackedAkashaAdapter(dry_run=True, store_dir=store)
        adapter.connect(AkashaConnectionConfig(enabled=True))
        doc = AkashaMemoryDocument(collection="decisions", content="approve")
        adapter.write(doc, AkashaWritePolicy())
        loaded = adapter.read(doc.doc_id)
        assert loaded is not None
        assert loaded.content == "approve"

    def test_read_nonexistent(self):
        store = self.store_dir()
        adapter = FileBackedAkashaAdapter(dry_run=True, store_dir=store)
        adapter.connect(AkashaConnectionConfig(enabled=True))
        assert adapter.read("nonexistent") is None

    def test_write_batch(self):
        store = self.store_dir()
        adapter = FileBackedAkashaAdapter(dry_run=True, store_dir=store)
        adapter.connect(AkashaConnectionConfig(enabled=True))
        docs = [
            AkashaMemoryDocument(collection="events", content=str(i))
            for i in range(5)
        ]
        written, failed = adapter.write_batch(docs, AkashaWritePolicy())
        assert written == 5
        assert failed == 0
        assert adapter.docs_written == 5

    def test_list_collection(self):
        store = self.store_dir()
        adapter = FileBackedAkashaAdapter(dry_run=True, store_dir=store)
        adapter.connect(AkashaConnectionConfig(enabled=True))
        adapter.write(AkashaMemoryDocument(collection="events", content="a"), AkashaWritePolicy())
        adapter.write(AkashaMemoryDocument(collection="events", content="b"), AkashaWritePolicy())
        adapter.write(AkashaMemoryDocument(collection="other", content="c"), AkashaWritePolicy())
        events = adapter.list_collection("events")
        assert len(events) == 2
        assert len(adapter.list_collection("nonexistent")) == 0

    def test_health_check(self):
        store = self.store_dir()
        adapter = FileBackedAkashaAdapter(dry_run=True, store_dir=store)
        config = AkashaConnectionConfig(enabled=True)
        result = adapter.health(config)
        assert result.healthy is True
        assert result.checks["file_backed"] is True
