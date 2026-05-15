"""Tests for W097 — Content Batch Export."""
from __future__ import annotations

import pytest

from src.content_factory.brief import ContentBrief
from src.content_factory.seogram import SEOgramCaption
from src.content_factory.carousel import CarouselPackage
from src.content_factory.reels import ReelScriptPackage
from src.content_factory.stories import StoriesPackage
from src.content_factory.batch_export import ExportBatch, BatchExporter, ExportFormat


class TestExportBatch:
    def test_create_batch(self):
        batch = ExportBatch(batch_id="eb1")
        assert batch.batch_id == "eb1"
        assert batch.item_count == 0
        assert batch.export_format == "jsonl"

    def test_add_items(self):
        batch = ExportBatch(batch_id="eb2")
        batch.items.append({"type": "test", "id": "1"})
        batch.items.append({"type": "test", "id": "2"})
        assert batch.item_count == 2

    def test_to_jsonl(self):
        batch = ExportBatch(batch_id="eb3")
        batch.items.append({"id": "1", "title": "Test 1"})
        batch.items.append({"id": "2", "title": "Test 2"})
        j = batch.to_jsonl()
        assert "Test 1" in j
        assert "Test 2" in j

    def test_to_csv(self):
        batch = ExportBatch(batch_id="eb4")
        batch.items.append({"id": "1", "title": "Test"})
        c = batch.to_csv()
        assert "id,title" in c
        assert "1,Test" in c

    def test_to_csv_empty(self):
        batch = ExportBatch(batch_id="eb5")
        assert batch.to_csv() == ""

    def test_export_jsonl(self):
        batch = ExportBatch(batch_id="eb6", export_format="jsonl")
        batch.items.append({"id": "1"})
        result = batch.export()
        assert result is not None
        assert "1" in result

    def test_export_csv(self):
        batch = ExportBatch(batch_id="eb7", export_format="csv")
        batch.items.append({"id": "1", "title": "T"})
        result = batch.export()
        assert "id,title" in result

    def test_export_markdown(self):
        batch = ExportBatch(batch_id="eb8", export_format="markdown")
        batch.items.append({"id": "1", "title": "T"})
        result = batch.export()
        assert result is not None
        assert "eb8" in result

    def test_export_empty_returns_none(self):
        batch = ExportBatch(batch_id="eb9")
        assert batch.export() is None

    def test_to_dict_roundtrip(self):
        batch = ExportBatch(batch_id="eb10", brand="Tigre", export_format="csv")
        batch.items.append({"id": "1"})
        d = batch.to_dict()
        restored = ExportBatch.from_dict(d)
        assert restored.batch_id == batch.batch_id
        assert restored.brand == "Tigre"
        assert restored.item_count == 1


class TestBatchExporter:
    def setup_method(self):
        self.exporter = BatchExporter()

    def _make_brief(self, brief_id="b1") -> ContentBrief:
        return ContentBrief(
            brief_id=brief_id,
            title="Test Brief",
            brand="Tigre Real",
            keywords=["test"],
            cta="Test CTA",
        )

    def _make_caption(self, caption_id="c1") -> SEOgramCaption:
        return SEOgramCaption(
            caption_id=caption_id,
            brief_id="b1",
            hook="Hook",
            paragraph_1="P1",
            paragraph_2="P2",
            cta="CTA",
            hashtags=["#test"],
            keywords_used=["test"],
        )

    def test_collect_from_briefs(self):
        briefs = [self._make_brief("b1"), self._make_brief("b2")]
        batch = self.exporter.collect_from_brief("batch1", briefs)
        assert batch.item_count == 2
        assert batch.brand == "Tigre Real"
        assert all(item["type"] == "content_brief" for item in batch.items)

    def test_collect_from_captions(self):
        captions = [self._make_caption("c1"), self._make_caption("c2")]
        batch = self.exporter.collect_from_captions("batch2", captions)
        assert batch.item_count == 2
        assert all(item["type"] == "seogram_caption" for item in batch.items)

    def test_collect_from_carousels(self):
        pkg = CarouselPackage(package_id="p1", brief_id="b1", title="Carrossel Test")
        batch = self.exporter.collect_from_carousels("batch3", [pkg])
        assert batch.item_count == 1
        assert batch.items[0]["type"] == "carousel_package"

    def test_collect_from_reels(self):
        pkg = ReelScriptPackage(package_id="r1", brief_id="b1", title="Reel Test", hook="Hook!")
        batch = self.exporter.collect_from_reels("batch4", [pkg])
        assert batch.item_count == 1
        assert batch.items[0]["type"] == "reel_script"

    def test_collect_from_stories(self):
        pkg = StoriesPackage(package_id="s1", brief_id="b1", title="Stories Test")
        batch = self.exporter.collect_from_stories("batch5", [pkg])
        assert batch.item_count == 1
        assert batch.items[0]["type"] == "stories_package"

    def test_collect_empty_lists(self):
        batch = self.exporter.collect_from_brief("batch6", [])
        assert batch.item_count == 0
        assert batch.brand == ""

    def test_export_jsonl_format(self):
        briefs = [self._make_brief("b1")]
        batch = self.exporter.collect_from_brief("batch7", briefs, export_format="jsonl")
        result = batch.export()
        assert result is not None

    def test_export_csv_format(self):
        briefs = [self._make_brief("b1")]
        batch = self.exporter.collect_from_brief("batch8", briefs, export_format="csv")
        result = batch.export()
        assert "id" in result
