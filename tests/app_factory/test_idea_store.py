"""Tests for IdeaStore - file-backed JSONL storage."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.app_factory.errors import InvalidAppIdeaError
from src.app_factory.idea_store import IdeaStore
from src.app_factory.models import AppIdea
from src.omnis_os.event_bus import EventBus


@pytest.fixture
def temp_dir(app_factory_tmp_dir: Path):
    return app_factory_tmp_dir


@pytest.fixture
def bus():
    return EventBus(dry_run=False)


@pytest.fixture
def sample_idea():
    return AppIdea.new(
        title="Test App",
        description="An app for testing",
        domain="testing",
        features=["login", "dashboard"],
    )


class TestIdeaStore:
    def test_save_creates_jsonl_entry(self, temp_dir, sample_idea):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        store.save(sample_idea)
        assert store._file_path.exists()
        lines = store._file_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["title"] == "Test App"

    def test_save_rejects_invalid_idea(self, temp_dir):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        bad = AppIdea.new(title="", description="")
        with pytest.raises(InvalidAppIdeaError):
            store.save(bad)

    def test_save_does_not_write_when_dry_run_true(self, temp_dir, sample_idea):
        store = IdeaStore(data_dir=temp_dir, dry_run=True)
        store.save(sample_idea)
        assert not store._file_path.exists()

    def test_get_returns_idea_by_id(self, temp_dir, sample_idea):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        store.save(sample_idea)
        found = store.get(sample_idea.idea_id)
        assert found is not None
        assert found.title == "Test App"

    def test_get_returns_none_for_missing_id(self, temp_dir):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        assert store.get("nonexistent") is None

    def test_list_all_returns_all_ideas(self, temp_dir, sample_idea):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        store.save(sample_idea)
        idea2 = AppIdea.new(title="Second", description="Another app")
        store.save(idea2)
        all_ideas = store.list_all()
        assert len(all_ideas) == 2

    def test_list_by_status_filters_correctly(self, temp_dir, sample_idea):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        store.save(sample_idea)
        idea2 = AppIdea.new(title="Generated", description="Already planned")
        store.save(idea2)
        drafts = store.list_by_status("draft")
        assert len(drafts) == 2

    def test_exists_returns_true_false(self, temp_dir, sample_idea):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        store.save(sample_idea)
        assert store.exists(sample_idea.idea_id) is True
        assert store.exists("nonexistent") is False

    def test_round_trip_save_get(self, temp_dir, sample_idea):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        store.save(sample_idea)
        found = store.get(sample_idea.idea_id)
        assert found is not None
        assert found.title == sample_idea.title
        assert found.description == sample_idea.description
        assert found.domain == sample_idea.domain
        assert found.features == sample_idea.features

    def test_events_emitted_on_non_dry_run_save(self, temp_dir, bus, sample_idea):
        store = IdeaStore(data_dir=temp_dir, dry_run=False, event_bus=bus)
        store.save(sample_idea)
        validated = bus.history("idea_validated")
        stored = bus.history("idea_stored")
        assert len(validated) == 1
        assert len(stored) == 1

    def test_events_not_emitted_on_dry_run_save(self, temp_dir, bus, sample_idea):
        store = IdeaStore(data_dir=temp_dir, dry_run=True, event_bus=bus)
        store.save(sample_idea)
        stored = bus.history("idea_stored")
        assert len(stored) == 0

    def test_empty_data_dir_handled(self, temp_dir, sample_idea):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        store.save(sample_idea)
        assert store._file_path.exists()

    def test_list_all_handles_corrupt_lines(self, temp_dir, sample_idea):
        store = IdeaStore(data_dir=temp_dir, dry_run=False)
        store.save(sample_idea)
        store.data_dir.mkdir(parents=True, exist_ok=True)
        with open(store._file_path, "a", encoding="utf-8") as fh:
            fh.write("not valid json\n")
            fh.write('{"idea_id": "missing_fields"}\n')
        ideas = store.list_all()
        assert len(ideas) == 1
        assert ideas[0].title == "Test App"
