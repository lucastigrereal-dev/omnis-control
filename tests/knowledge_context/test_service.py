"""Tests for knowledge_context service."""
import pytest
from pathlib import Path

from src.knowledge_context.service import (
    create_pack, add_entry, list_packs, get_pack,
    set_context, set_context_fact, get_context, list_contexts,
    PackNotFoundError, ContextNotFoundError, ValidationError,
)


@pytest.fixture
def tmp_packs(tmp_path):
    return tmp_path / "knowledge_packs.jsonl"


@pytest.fixture
def tmp_contexts(tmp_path):
    return tmp_path / "context_packs.jsonl"


class TestKnowledgePacks:
    def test_create_pack(self, tmp_packs):
        pack = create_pack("Gastronomia Natal", description="Sabores de Natal", log_path=tmp_packs)
        assert pack.pack_id.startswith("kp_")
        assert pack.name == "Gastronomia Natal"

    def test_empty_name_raises(self, tmp_packs):
        with pytest.raises(ValidationError):
            create_pack("", log_path=tmp_packs)

    def test_tags_stored(self, tmp_packs):
        pack = create_pack("Pack", tags=["viagem", "natal"], log_path=tmp_packs)
        assert "viagem" in pack.tags

    def test_add_entry(self, tmp_packs):
        pack = create_pack("Pack", log_path=tmp_packs)
        updated = add_entry(pack.pack_id, title="Dica 1", content="Conteudo.", log_path=tmp_packs)
        assert updated.entry_count() == 1
        assert updated.entries[0].title == "Dica 1"

    def test_add_entry_prefix_match(self, tmp_packs):
        pack = create_pack("Pack", log_path=tmp_packs)
        updated = add_entry(pack.pack_id[:8], title="T", content="C", log_path=tmp_packs)
        assert updated.entry_count() == 1

    def test_add_entry_pack_not_found(self, tmp_packs):
        with pytest.raises(PackNotFoundError):
            add_entry("bad_id", title="T", content="C", log_path=tmp_packs)

    def test_list_packs(self, tmp_packs):
        create_pack("P1", log_path=tmp_packs)
        create_pack("P2", log_path=tmp_packs)
        packs = list_packs(log_path=tmp_packs)
        assert len(packs) == 2

    def test_list_packs_filter_by_tag(self, tmp_packs):
        create_pack("P1", tags=["viagem"], log_path=tmp_packs)
        create_pack("P2", tags=["gastronomia"], log_path=tmp_packs)
        packs = list_packs(tag="viagem", log_path=tmp_packs)
        assert len(packs) == 1

    def test_get_pack_by_prefix(self, tmp_packs):
        pack = create_pack("Pack A", log_path=tmp_packs)
        found = get_pack(pack.pack_id[:10], log_path=tmp_packs)
        assert found.pack_id == pack.pack_id

    def test_get_pack_not_found(self, tmp_packs):
        with pytest.raises(PackNotFoundError):
            get_pack("nonexistent", log_path=tmp_packs)

    def test_entries_persist_after_roundtrip(self, tmp_packs):
        pack = create_pack("Pack", log_path=tmp_packs)
        add_entry(pack.pack_id, title="T1", content="C1", log_path=tmp_packs)
        add_entry(pack.pack_id, title="T2", content="C2", log_path=tmp_packs)
        loaded = get_pack(pack.pack_id, log_path=tmp_packs)
        assert loaded.entry_count() == 2

    def test_no_network_calls(self, tmp_packs):
        from unittest.mock import patch
        with patch("requests.post") as mock:
            create_pack("P", log_path=tmp_packs)
            mock.assert_not_called()


class TestContextPacks:
    def test_set_context(self, tmp_contexts):
        ctx = set_context("afamiliatigrereal", "Familia Tigre", log_path=tmp_contexts)
        assert ctx.context_id.startswith("ctx_")
        assert ctx.account_handle == "afamiliatigrereal"

    def test_strips_at_from_handle(self, tmp_contexts):
        ctx = set_context("@lucastigrereal", "Lucas", log_path=tmp_contexts)
        assert "@" not in ctx.account_handle

    def test_set_upserts_existing(self, tmp_contexts):
        set_context("acc1", "Old Name", log_path=tmp_contexts)
        set_context("acc1", "New Name", log_path=tmp_contexts)
        contexts = list_contexts(log_path=tmp_contexts)
        assert len(contexts) == 1
        assert contexts[0].display_name == "New Name"

    def test_set_context_fact(self, tmp_contexts):
        set_context("acc1", "Test", log_path=tmp_contexts)
        ctx = set_context_fact("acc1", key="cidade", value="Natal", log_path=tmp_contexts)
        assert ctx.get_fact("cidade") == "Natal"

    def test_set_fact_upserts(self, tmp_contexts):
        set_context("acc1", "Test", log_path=tmp_contexts)
        set_context_fact("acc1", key="cidade", value="Natal", log_path=tmp_contexts)
        set_context_fact("acc1", key="cidade", value="Fortaleza", log_path=tmp_contexts)
        ctx = get_context("acc1", log_path=tmp_contexts)
        assert ctx.get_fact("cidade") == "Fortaleza"
        assert len(ctx.facts) == 1

    def test_fact_on_nonexistent_context_raises(self, tmp_contexts):
        with pytest.raises(ContextNotFoundError):
            set_context_fact("nonexistent", key="k", value="v", log_path=tmp_contexts)

    def test_get_context(self, tmp_contexts):
        set_context("oinatalrn", "Natal RN", log_path=tmp_contexts)
        ctx = get_context("oinatalrn", log_path=tmp_contexts)
        assert ctx.account_handle == "oinatalrn"

    def test_get_context_not_found(self, tmp_contexts):
        with pytest.raises(ContextNotFoundError):
            get_context("nonexistent", log_path=tmp_contexts)

    def test_list_contexts(self, tmp_contexts):
        set_context("acc1", "A1", log_path=tmp_contexts)
        set_context("acc2", "A2", log_path=tmp_contexts)
        contexts = list_contexts(log_path=tmp_contexts)
        assert len(contexts) == 2

    def test_topics_stored(self, tmp_contexts):
        ctx = set_context("acc1", "A", topics=["viagem", "familia"], log_path=tmp_contexts)
        assert "viagem" in ctx.topics

    def test_context_roundtrip(self, tmp_contexts):
        from src.knowledge_context.models import ContextPack
        set_context("acc1", "A", log_path=tmp_contexts)
        set_context_fact("acc1", "k1", "v1", log_path=tmp_contexts)
        ctx = get_context("acc1", log_path=tmp_contexts)
        d = ctx.to_dict()
        restored = ContextPack.from_dict(d)
        assert restored.account_handle == "acc1"
        assert restored.get_fact("k1") == "v1"
