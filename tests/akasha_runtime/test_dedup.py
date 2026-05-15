from src.akasha_runtime.models import AkashaMemoryDocument
from src.akasha_runtime.dedup import DedupKeyGenerator, DedupRegistry


class TestDedupKeyGenerator:
    def test_generate_content_hash(self):
        gen = DedupKeyGenerator()
        doc = AkashaMemoryDocument(content_hash="abc123")
        key = gen.generate(doc, keys=["content_hash"])
        assert len(key) == 16

    def test_generate_same_content_produces_same_key(self):
        gen = DedupKeyGenerator()
        d1 = AkashaMemoryDocument(content_hash="abc")
        d2 = AkashaMemoryDocument(content_hash="abc")
        assert gen.generate(d1, keys=["content_hash"]) == gen.generate(d2, keys=["content_hash"])

    def test_generate_different_content_produces_different_key(self):
        gen = DedupKeyGenerator()
        d1 = AkashaMemoryDocument(content_hash="abc")
        d2 = AkashaMemoryDocument(content_hash="def")
        assert gen.generate(d1) != gen.generate(d2)

    def test_generate_content_raw_key(self):
        gen = DedupKeyGenerator()
        doc = AkashaMemoryDocument(content="hello world")
        key = gen.generate(doc, keys=["content_raw"])
        assert len(key) == 16

    def test_generate_combined_keys(self):
        gen = DedupKeyGenerator()
        doc = AkashaMemoryDocument(content_hash="abc", content="hello", collection="events")
        key = gen.generate(doc, keys=["content_hash", "collection_content"])
        assert len(key) == 16

    def test_keys_generated_counter(self):
        gen = DedupKeyGenerator()
        gen.generate(AkashaMemoryDocument(content_hash="a"))
        gen.generate(AkashaMemoryDocument(content_hash="b"))
        assert gen.keys_generated == 2


class TestDedupRegistry:
    def test_register_and_check(self):
        reg = DedupRegistry()
        doc = AkashaMemoryDocument(content_hash="abc", content="test")
        reg.register(doc)
        assert reg.is_duplicate(AkashaMemoryDocument(content_hash="abc", content="test")) is True

    def test_unique_not_duplicate(self):
        reg = DedupRegistry()
        reg.register(AkashaMemoryDocument(content_hash="abc"))
        assert reg.is_duplicate(AkashaMemoryDocument(content_hash="def")) is False

    def test_filter_duplicates(self):
        reg = DedupRegistry()
        docs = [
            AkashaMemoryDocument(content="a"),
            AkashaMemoryDocument(content="a"),
            AkashaMemoryDocument(content="b"),
        ]
        unique, duplicates = reg.filter_duplicates(docs, keys=["content_raw"])
        assert len(unique) == 2
        assert len(duplicates) == 1

    def test_filter_all_unique(self):
        reg = DedupRegistry()
        docs = [AkashaMemoryDocument(content=str(i)) for i in range(5)]
        unique, duplicates = reg.filter_duplicates(docs, keys=["content_raw"])
        assert len(unique) == 5
        assert len(duplicates) == 0

    def test_key_count(self):
        reg = DedupRegistry()
        reg.register(AkashaMemoryDocument(content_hash="a"))
        reg.register(AkashaMemoryDocument(content_hash="b"))
        assert reg.key_count == 2

    def test_deduped_count(self):
        reg = DedupRegistry()
        docs = [
            AkashaMemoryDocument(content="same"),
            AkashaMemoryDocument(content="same"),
            AkashaMemoryDocument(content="same"),
        ]
        _, duplicates = reg.filter_duplicates(docs, keys=["content_raw"])
        assert reg.deduped_count == 2
        assert len(duplicates) == 2
