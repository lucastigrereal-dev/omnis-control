"""Tests for Publer/Metricool export (W088)."""
from __future__ import annotations

from src.publisher.publer_export import (
    PublerExportBatch,
    PublerExportItem,
    PublerExporter,
    PublerPlatform,
)


class TestPublerExportItem:
    def test_defaults(self):
        i = PublerExportItem(item_id="i1", caption="Test", account_handle="@test")
        assert i.platform == PublerPlatform.INSTAGRAM
        assert i.hashtags == []

    def test_to_dict_roundtrip(self):
        i = PublerExportItem(
            item_id="i1", caption="Hello world", account_handle="@test",
            hashtags=["#omnis", "#test"], schedule_iso="2026-06-01T10:00:00",
        )
        restored = PublerExportItem.from_dict(i.to_dict())
        assert restored.item_id == "i1"
        assert restored.caption == "Hello world"
        assert restored.hashtags == ["#omnis", "#test"]
        assert restored.schedule_iso == "2026-06-01T10:00:00"


class TestPublerExportBatch:
    def test_empty_batch(self):
        b = PublerExportBatch(batch_id="b1")
        assert len(b.items) == 0
        assert b.dry_run is True

    def test_add_item(self):
        b = PublerExportBatch(batch_id="b1")
        b.add(PublerExportItem(item_id="i1", caption="Test", account_handle="@test"))
        assert len(b.items) == 1

    def test_to_csv_rows(self):
        b = PublerExportBatch(batch_id="b1")
        b.add(PublerExportItem(item_id="i1", caption="Test", account_handle="@test", hashtags=["#a", "#b"]))
        rows = b.to_csv_rows()
        assert len(rows) == 1
        assert rows[0]["item_id"] == "i1"

    def test_to_dict_roundtrip(self):
        b = PublerExportBatch(batch_id="b1", label="Test batch")
        b.add(PublerExportItem(item_id="i1", caption="Hello", account_handle="@test"))
        restored = PublerExportBatch.from_dict(b.to_dict())
        assert restored.batch_id == "b1"
        assert restored.label == "Test batch"
        assert len(restored.items) == 1


class TestPublerExporter:
    def test_create_batch(self):
        e = PublerExporter()
        batch = e.create_batch("Test batch")
        assert batch.label == "Test batch"
        assert batch.dry_run is True

    def test_build_item(self):
        e = PublerExporter()
        item = e.build_item("Caption text", "@lucastigrereal", hashtags=["#test"])
        assert item.caption == "Caption text"
        assert item.account_handle == "@lucastigrereal"
        assert item.hashtags == ["#test"]

    def test_export_batch_csv(self):
        e = PublerExporter()
        batch = e.create_batch("Test")
        item = e.build_item("Caption", "@test", hashtags=["#a", "#b"])
        batch.add(item)
        csv_out = e.export_batch(batch.batch_id)
        assert csv_out is not None
        assert "item_id" in csv_out
        assert "Caption" in csv_out
        assert "#a #b" in csv_out

    def test_export_batch_empty(self):
        e = PublerExporter()
        batch = e.create_batch("Empty")
        assert e.export_batch(batch.batch_id) is None

    def test_export_batch_unknown(self):
        e = PublerExporter()
        assert e.export_batch("nonexistent") is None

    def test_to_dict(self):
        e = PublerExporter()
        e.create_batch("Batch 1")
        d = e.to_dict()
        assert d["dry_run"] is True
        assert len(d["batches"]) == 1
