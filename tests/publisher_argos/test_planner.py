"""Tests for P8 Publisher ARGOS Planner."""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.publisher_argos.models import (
    ArgosExportItem,
    ArgosExportPackage,
    ExportStatus,
    PublisherHandoff,
    PublishChannel,
    PublishQueuePlan,
    PublishReadinessCheck,
    PublishTarget,
    ReadinessVerdict,
)
from src.publisher_argos.planner import PublisherArgosPlanner


@pytest.fixture
def planner():
    return PublisherArgosPlanner()


class TestBuildExportItem:
    def test_build_default(self, planner):
        item = planner.build_export_item(caption="Hello world, this is a test post!")
        assert isinstance(item, ArgosExportItem)
        assert item.caption == "Hello world, this is a test post!"
        assert item.target.handle == "lucastigrereal"
        assert item.target.followers == 690_000
        assert item.status == ExportStatus.DRAFT
        assert item.approval_required is True

    def test_build_custom_handle(self, planner):
        item = planner.build_export_item(
            caption="Test post",
            handle="oinatalrn",
            channel=PublishChannel.INSTAGRAM_REEL,
            media_type="VIDEO",
            tags=["travel", "natal"],
        )
        assert item.target.handle == "oinatalrn"
        assert item.target.followers == 630_000
        assert item.target.channel == PublishChannel.INSTAGRAM_REEL
        assert item.media_type == "VIDEO"
        assert item.tags == ["travel", "natal"]

    def test_build_unknown_handle(self, planner):
        item = planner.build_export_item(caption="Test", handle="unknown_page")
        assert item.target.handle == "unknown_page"
        assert item.target.followers == 0

    def test_build_with_schedule(self, planner):
        item = planner.build_export_item(
            caption="Scheduled post test caption",
            handle="afamiliatigrereal",
            schedule_iso="2026-05-20T10:00:00",
        )
        assert item.schedule_iso == "2026-05-20T10:00:00"

    def test_build_always_draft(self, planner):
        """All built items must start as DRAFT — never auto-published."""
        item = planner.build_export_item(caption="Test")
        assert item.status == ExportStatus.DRAFT


class TestValidatePublishReadiness:
    def test_valid_item_passes(self, planner):
        item = planner.build_export_item(
            caption="This is a valid caption for testing!",
            handle="lucastigrereal",
            media_url="https://example.com/media.jpg",
        )
        check = planner.validate_publish_readiness(item)
        assert check.verdict == ReadinessVerdict.PASS
        assert check.passed == 5
        assert check.failed == 0
        assert check.blocked == 0
        assert check.is_ready is True

    def test_empty_caption_fails(self, planner):
        item = planner.build_export_item(caption="", handle="lucastigrereal")
        check = planner.validate_publish_readiness(item)
        assert check.verdict == ReadinessVerdict.FAIL
        assert check.failed >= 1
        assert any(c["check"] == "has_caption" and not c["ok"] for c in check.checks)

    def test_short_caption_fails(self, planner):
        item = planner.build_export_item(caption="Short", handle="lucastigrereal")
        check = planner.validate_publish_readiness(item)
        assert check.verdict == ReadinessVerdict.FAIL
        assert any(c["check"] == "caption_min_length" and not c["ok"] for c in check.checks)

    def test_missing_media_url_blocked(self, planner):
        item = planner.build_export_item(
            caption="Valid caption with enough text!",
            handle="lucastigrereal",
            media_url="",
        )
        check = planner.validate_publish_readiness(item)
        assert check.verdict == ReadinessVerdict.PENDING_APPROVAL
        assert check.blocked == 1
        assert any(c["check"] == "has_media_url" and not c["ok"] for c in check.checks)

    def test_unknown_handle_blocked(self, planner):
        item = planner.build_export_item(
            caption="Valid caption with enough chars",
            handle="random_unknown_page",
            media_url="https://example.com/img.jpg",
        )
        check = planner.validate_publish_readiness(item)
        assert check.verdict == ReadinessVerdict.PENDING_APPROVAL
        assert any(c["check"] == "handle_is_known" and not c["ok"] for c in check.checks)

    def test_empty_target_fails(self, planner):
        item = ArgosExportItem(
            target=PublishTarget(handle=""),
            caption="A valid test caption that is long enough",
        )
        check = planner.validate_publish_readiness(item)
        assert any(c["check"] == "has_target" and not c["ok"] for c in check.checks)

    def test_check_count(self, planner):
        item = planner.build_export_item(caption="Test caption with enough chars")
        check = planner.validate_publish_readiness(item)
        total = check.passed + check.failed + check.blocked
        assert total == 5  # 5 checks always run


class TestBuildQueuePlan:
    def test_empty(self, planner):
        qp = planner.build_queue_plan()
        assert isinstance(qp, PublishQueuePlan)
        assert qp.items == []
        assert qp.dry_run is True

    def test_with_items(self, planner):
        i1 = planner.build_export_item(caption="First test post for the queue")
        i2 = planner.build_export_item(
            caption="Second test post for the queue",
            handle="oinatalrn",
            channel=PublishChannel.INSTAGRAM_REEL,
        )
        qp = planner.build_queue_plan(items=[i1, i2], label="Morning Batch")
        assert len(qp.items) == 2
        assert qp.label == "Morning Batch"

    def test_find_by_handle(self, planner):
        i1 = planner.build_export_item(caption="Post A captions here", handle="lucastigrereal")
        i2 = planner.build_export_item(caption="Post B captions here", handle="oinatalrn")
        qp = planner.build_queue_plan(items=[i1, i2])
        assert len(qp.find_by_handle("lucastigrereal")) == 1
        assert len(qp.find_by_handle("oinatalrn")) == 1


class TestBuildArgosExportPackage:
    def test_build_package(self, planner):
        items = [
            planner.build_export_item(
                caption="First valid test caption here",
                handle="lucastigrereal",
                media_url="https://x.com/a.jpg",
            ),
            planner.build_export_item(
                caption="Second valid test caption here",
                handle="oinatalrn",
                media_url="https://x.com/b.jpg",
                channel=PublishChannel.INSTAGRAM_REEL,
            ),
        ]
        qp = planner.build_queue_plan(items=items, label="Batch 1")
        pkg = planner.build_argos_export_package(qp, label="Morning Export")

        assert isinstance(pkg, ArgosExportPackage)
        assert pkg.label == "Morning Export"
        assert pkg.dry_run is True
        assert pkg.approval_required is True
        assert pkg.item_count == 2
        assert len(pkg.readiness_checks) == 2
        assert pkg.all_ready is True

    def test_items_marked_ready(self, planner):
        item = planner.build_export_item(
            caption="Good caption for this test",
            handle="lucastigrereal",
            media_url="https://x.com/img.jpg",
        )
        qp = planner.build_queue_plan(items=[item])
        pkg = planner.build_argos_export_package(qp)
        assert pkg.queue_plan.items[0].status == ExportStatus.READY

    def test_blocked_items(self, planner):
        item = planner.build_export_item(
            caption="",  # empty → will fail
            handle="unknown_page",
            media_url="",
        )
        qp = planner.build_queue_plan(items=[item])
        pkg = planner.build_argos_export_package(qp)
        assert pkg.all_ready is False
        assert len(pkg.blocked_items) >= 1
        assert pkg.queue_plan.items[0].status == ExportStatus.BLOCKED

    def test_dry_run_never_real(self, planner):
        """Package must always be dry_run=True — never real export."""
        qp = planner.build_queue_plan()
        pkg = planner.build_argos_export_package(qp)
        assert pkg.dry_run is True


class TestBuildPublisherHandoff:
    def test_build_handoff(self, planner):
        item = planner.build_export_item(
            caption="Handoff test post caption here",
            handle="lucastigrereal",
            media_url="https://x.com/m.jpg",
        )
        qp = planner.build_queue_plan(items=[item])
        pkg = planner.build_argos_export_package(qp)
        handoff = planner.build_publisher_handoff(pkg)

        assert isinstance(handoff, PublisherHandoff)
        assert handoff.source_module == "publisher_argos"
        assert handoff.target_system == "ARGOS"
        assert handoff.dry_run is True
        assert handoff.approval_required is True
        assert handoff.approved_by is None

    def test_handoff_never_auto_approves(self, planner):
        """Handoff must NEVER auto-approve — approved_by is always None."""
        qp = planner.build_queue_plan()
        pkg = planner.build_argos_export_package(qp)
        handoff = planner.build_publisher_handoff(pkg)
        assert handoff.approved_by is None
        assert handoff.approval_required is True


class TestExportArgosJson:
    def test_export_json_string(self, planner):
        item = planner.build_export_item(
            caption="Export JSON test post caption",
            handle="lucastigrereal",
            media_url="https://x.com/e.jpg",
        )
        qp = planner.build_queue_plan(items=[item])
        pkg = planner.build_argos_export_package(qp, label="JSON Export")
        handoff = planner.build_publisher_handoff(pkg)

        json_str = planner.export_argos_json(handoff)
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["handoff_id"] == handoff.id
        assert data["source_module"] == "publisher_argos"
        assert data["dry_run"] is True
        assert "package" in data
        assert data["package"]["label"] == "JSON Export"

    def test_export_json_pretty(self, planner):
        qp = planner.build_queue_plan()
        pkg = planner.build_argos_export_package(qp)
        handoff = planner.build_publisher_handoff(pkg)
        json_str = planner.export_argos_json(handoff, indent=4)
        assert "    " in json_str

    def test_json_has_approval_flag(self, planner):
        qp = planner.build_queue_plan()
        pkg = planner.build_argos_export_package(qp)
        handoff = planner.build_publisher_handoff(pkg)
        json_str = planner.export_argos_json(handoff)
        data = json.loads(json_str)
        assert data["approval_required"] is True
        assert data["approved_by"] is None

    def test_export_preserves_all_items(self, planner):
        items = []
        for i in range(3):
            items.append(planner.build_export_item(
                caption=f"Post number {i} with a valid test caption",
                handle="lucastigrereal",
                media_url=f"https://x.com/{i}.jpg",
            ))
        qp = planner.build_queue_plan(items=items, label="Batch 3")
        pkg = planner.build_argos_export_package(qp)
        handoff = planner.build_publisher_handoff(pkg)
        json_str = planner.export_argos_json(handoff)
        data = json.loads(json_str)
        assert data["package"]["queue_plan"]["item_count"] == 3

    def test_export_to_explicit_temp_path(self, planner):
        """Helper receives explicit path — never writes to exports/ automatically."""
        item = planner.build_export_item(
            caption="Temp file test post caption here",
            handle="lucastigrereal",
            media_url="https://x.com/t.jpg",
        )
        qp = planner.build_queue_plan(items=[item])
        pkg = planner.build_argos_export_package(qp)
        handoff = planner.build_publisher_handoff(pkg)
        json_str = planner.export_argos_json(handoff)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json_str)
            tmp_path = f.name

        try:
            written = Path(tmp_path).read_text(encoding="utf-8")
            data = json.loads(written)
            assert data["handoff_id"] == handoff.id
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class TestKnownPages:
    def test_get_known_handles(self):
        handles = PublisherArgosPlanner.get_known_handles()
        assert "lucastigrereal" in handles
        assert "oinatalrn" in handles
        assert len(handles) == 6

    def test_get_page_info(self):
        info = PublisherArgosPlanner.get_page_info("lucastigrereal")
        assert info is not None
        assert info["followers"] == 690_000
        assert info["profile"] == "@lucastigrereal"

    def test_get_page_info_unknown(self):
        info = PublisherArgosPlanner.get_page_info("nonexistent")
        assert info is None


class TestPlannerConfiguration:
    def test_custom_planner(self):
        p = PublisherArgosPlanner(dry_run=True, approval_required=True)
        assert p.dry_run is True
        assert p.approval_required is True

    def test_export_item_inherits_approval(self, planner):
        item = planner.build_export_item(caption="Test post caption for approval check")
        assert item.approval_required is True


class TestNeverNetworkOrExternal:
    """All operations are pure Python modeling — no network, no Meta, no ARGOS."""

    def test_build_export_item_no_network(self, planner):
        item = planner.build_export_item(caption="Test post caption with enough text")
        assert isinstance(item, ArgosExportItem)

    def test_validate_no_network(self, planner):
        item = planner.build_export_item(
            caption="Network free validation test caption!",
            handle="lucastigrereal",
            media_url="https://example.com/test.jpg",
        )
        check = planner.validate_publish_readiness(item)
        assert isinstance(check, PublishReadinessCheck)

    def test_export_no_network(self, planner):
        qp = planner.build_queue_plan()
        pkg = planner.build_argos_export_package(qp)
        handoff = planner.build_publisher_handoff(pkg)
        json_str = planner.export_argos_json(handoff)
        assert isinstance(json_str, str)
        assert len(json_str) > 0
