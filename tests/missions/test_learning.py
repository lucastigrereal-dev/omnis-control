"""Tests for LearningEntry + LearningJournal."""
from __future__ import annotations

import pytest

from src.missions.learning import LearningEntry, LearningJournal, Confidence


class TestLearningEntry:
    def test_creation(self):
        e = LearningEntry(insight="Dry-run reveals gap in artifact tracking")
        assert len(e.id) == 12
        assert e.insight == "Dry-run reveals gap in artifact tracking"
        assert e.confidence == Confidence.MEDIUM
        assert e.tags == []

    def test_to_from_jsonl_roundtrip(self):
        e = LearningEntry(
            insight="Step 3 produced unexpected output format",
            source="step_completed",
            confidence=Confidence.HIGH,
            tags=["format", "unexpected"],
            mission_id="abc123",
            step_id="step-3",
        )
        line = e.to_jsonl()
        restored = LearningEntry.from_jsonl(line)
        assert restored.insight == e.insight
        assert restored.id == e.id
        assert restored.confidence == e.confidence
        assert restored.tags == e.tags

    def test_frozen(self):
        e = LearningEntry(insight="test")
        with pytest.raises(Exception):
            e.insight = "changed"


class TestLearningJournal:
    def test_record_and_read(self, tmp_path):
        journal = LearningJournal(str(tmp_path))
        journal.record(insight="Test insight", source="test", tags=["test"])

        entries = journal.read_all()
        assert len(entries) == 1
        assert entries[0].insight == "Test insight"
        assert entries[0].source == "test"

    def test_multiple_entries_preserve_order(self, tmp_path):
        journal = LearningJournal(str(tmp_path))
        for i in range(5):
            journal.record(insight=f"Insight {i}")

        entries = journal.read_all()
        assert len(entries) == 5
        assert [e.insight for e in entries] == [f"Insight {i}" for i in range(5)]

    def test_empty_journal(self, tmp_path):
        journal = LearningJournal(str(tmp_path))
        assert journal.read_all() == []

    def test_filter_by_tag(self, tmp_path):
        journal = LearningJournal(str(tmp_path))
        journal.record(insight="A", tags=["bug", "critical"])
        journal.record(insight="B", tags=["feature"])
        journal.record(insight="C", tags=["bug", "minor"])

        bugs = journal.filter_by_tag("bug")
        assert len(bugs) == 2
        assert {b.insight for b in bugs} == {"A", "C"}

    def test_filter_by_confidence(self, tmp_path):
        journal = LearningJournal(str(tmp_path))
        journal.record(insight="A", confidence=Confidence.HIGH)
        journal.record(insight="B", confidence=Confidence.LOW)
        journal.record(insight="C", confidence=Confidence.HIGH)

        high = journal.filter_by_confidence(Confidence.HIGH)
        assert len(high) == 2

    def test_search_keyword(self, tmp_path):
        journal = LearningJournal(str(tmp_path))
        journal.record(insight="Artifact registry missing hash")
        journal.record(insight="Budget cap exceeded")
        journal.record(insight="Registry needs dedup keys")

        results = journal.search("registry")
        assert len(results) == 2

    def test_count(self, tmp_path):
        journal = LearningJournal(str(tmp_path))
        assert journal.count() == 0
        journal.record(insight="a")
        journal.record(insight="b")
        assert journal.count() == 2

    def test_summary(self, tmp_path):
        journal = LearningJournal(str(tmp_path))
        journal.record(insight="A", confidence=Confidence.HIGH, tags=["critical"])
        journal.record(insight="B", confidence=Confidence.MEDIUM, tags=["minor"])

        s = journal.summary()
        assert s["total"] == 2
        assert s["by_confidence"]["high"] == 1
        assert s["by_confidence"]["medium"] == 1
        assert s["by_confidence"]["low"] == 0
        assert set(s["all_tags"]) == {"critical", "minor"}
