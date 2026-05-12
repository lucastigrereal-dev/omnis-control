"""Tests for P5 Marketing Supreme exporters."""

from __future__ import annotations

import json
import csv
import io

from src.marketing.models import (
    CampaignPackage,
    CampaignBrief,
    ContentPlan,
    ContentItem,
    CONTENT_FORMAT_CAROUSEL,
    CONTENT_FORMAT_REEL,
    PLATFORM_INSTAGRAM,
    CTA_BOOK,
    CTA_LINK_BIO,
)
from src.marketing.exporters import (
    export_campaign_package_markdown,
    export_content_calendar_csv,
    export_content_calendar_json,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_items() -> list[ContentItem]:
    return [
        ContentItem(date="2026-06-01", pillar_id="pil_a", topic="Hotel Dicas", content_format=CONTENT_FORMAT_CAROUSEL, platform=PLATFORM_INSTAGRAM, cta=CTA_LINK_BIO),
        ContentItem(date="2026-06-02", pillar_id="pil_b", topic="Resort Promo", content_format=CONTENT_FORMAT_REEL, platform=PLATFORM_INSTAGRAM, cta=CTA_BOOK, hook="Best deal"),
    ]


# ---------------------------------------------------------------------------
# Markdown exporter
# ---------------------------------------------------------------------------


class TestExportCampaignPackageMarkdown:
    def test_exports_basic_markdown(self):
        brief = CampaignBrief.new("Test Campaign", "mktobj_abc", "aud_123", pillar_ids=["pil_a"])
        plan = ContentPlan.new("cmp_test", items=_make_items(), schedule_start="2026-06-01", schedule_end="2026-06-02")
        pkg = CampaignPackage.new("Summer Package", brief=brief, plan=plan)

        md = export_campaign_package_markdown(pkg)

        assert "# Campaign: Summer Package" in md
        assert "## Brief" in md
        assert "## Content Plan" in md
        assert "Test Campaign" in md
        assert "Hotel Dicas" in md
        assert "Resort Promo" in md

    def test_exports_with_validation_issues(self):
        pkg = CampaignPackage.new("Broken", validation_issues=["no objective", "bad budget"])
        md = export_campaign_package_markdown(pkg)
        assert "no objective" in md
        assert "bad budget" in md

    def test_exports_warnings_section(self):
        pkg = CampaignPackage.new("Warn", validation_warnings=["low pillar count"])
        md = export_campaign_package_markdown(pkg)
        assert "## Warnings" in md
        assert "low pillar count" in md

    def test_empty_package(self):
        pkg = CampaignPackage.new("Empty")
        md = export_campaign_package_markdown(pkg)
        assert "# Campaign: Empty" in md
        assert "## Brief" not in md
        assert "## Content Plan" not in md


# ---------------------------------------------------------------------------
# CSV exporter
# ---------------------------------------------------------------------------


class TestExportContentCalendarCsv:
    def test_exports_csv_with_header(self):
        items = _make_items()
        csv_str = export_content_calendar_csv(items)

        lines = csv_str.strip().split("\r\n") if "\r\n" in csv_str else csv_str.strip().split("\n")
        assert len(lines) == 3  # header + 2 items

        reader = csv.reader(io.StringIO(csv_str))
        rows = list(reader)
        assert rows[0] == ["date", "pillar_id", "topic", "content_format", "platform", "hook", "cta", "notes"]
        assert rows[1][0] == "2026-06-01"
        assert rows[1][2] == "Hotel Dicas"
        assert rows[2][0] == "2026-06-02"

    def test_exports_empty_csv(self):
        csv_str = export_content_calendar_csv([])
        lines = csv_str.strip().split("\n")
        assert len(lines) == 1  # header only


# ---------------------------------------------------------------------------
# JSON exporter
# ---------------------------------------------------------------------------


class TestExportContentCalendarJson:
    def test_exports_json(self):
        items = _make_items()
        json_str = export_content_calendar_json(items)
        data = json.loads(json_str)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["date"] == "2026-06-01"
        assert data[0]["topic"] == "Hotel Dicas"
        assert data[1]["topic"] == "Resort Promo"

    def test_exports_empty_json(self):
        json_str = export_content_calendar_json([])
        data = json.loads(json_str)
        assert data == []
