"""Tests for P8 Publisher ARGOS Export models."""

from datetime import datetime

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


class TestPublishTarget:
    def test_defaults(self):
        t = PublishTarget()
        assert t.handle == ""
        assert t.channel == PublishChannel.INSTAGRAM_FEED
        assert t.followers == 0

    def test_custom(self):
        t = PublishTarget(
            handle="lucastigrereal",
            profile="@lucastigrereal",
            channel=PublishChannel.INSTAGRAM_REEL,
            followers=690_000,
            label="Lucas Reels",
        )
        assert t.handle == "lucastigrereal"
        assert t.followers == 690_000
        assert t.channel == PublishChannel.INSTAGRAM_REEL

    def test_to_dict(self):
        t = PublishTarget(handle="test", channel=PublishChannel.INSTAGRAM_STORY)
        d = t.to_dict()
        assert d["handle"] == "test"
        assert d["channel"] == "instagram_story"


class TestArgosExportItem:
    def test_defaults(self):
        item = ArgosExportItem()
        assert item.status == ExportStatus.DRAFT
        assert item.approval_required is True
        assert item.media_type == "IMAGE"
        assert item.id

    def test_mark_ready(self):
        item = ArgosExportItem()
        item.mark_ready()
        assert item.status == ExportStatus.READY

    def test_mark_queued(self):
        item = ArgosExportItem()
        item.mark_queued()
        assert item.status == ExportStatus.QUEUED

    def test_mark_exported(self):
        item = ArgosExportItem()
        item.mark_exported()
        assert item.status == ExportStatus.EXPORTED

    def test_mark_blocked(self):
        item = ArgosExportItem()
        item.mark_blocked("caption too short")
        assert item.status == ExportStatus.BLOCKED
        assert item.notes == "caption too short"

    def test_to_dict(self):
        item = ArgosExportItem(
            caption="Hello world test caption",
            tags=["travel", "family"],
            media_type="CAROUSEL",
        )
        d = item.to_dict()
        assert d["caption"] == "Hello world test caption"
        assert d["tags"] == ["travel", "family"]
        assert d["media_type"] == "CAROUSEL"
        assert d["status"] == "draft"
        assert d["approval_required"] is True


class TestPublishReadinessCheck:
    def test_pass(self):
        c = PublishReadinessCheck(
            item_id="i1",
            verdict=ReadinessVerdict.PASS,
            passed=5, failed=0, blocked=0,
        )
        assert c.is_ready is True
        assert c.requires_approval is False

    def test_fail(self):
        c = PublishReadinessCheck(
            item_id="i2",
            verdict=ReadinessVerdict.FAIL,
            passed=2, failed=3, blocked=0,
        )
        assert c.is_ready is False
        assert c.requires_approval is True

    def test_pending_approval(self):
        c = PublishReadinessCheck(
            item_id="i3",
            verdict=ReadinessVerdict.PENDING_APPROVAL,
            passed=4, failed=0, blocked=1,
        )
        assert c.is_ready is False
        assert c.requires_approval is True

    def test_to_dict(self):
        c = PublishReadinessCheck(
            item_id="i1",
            verdict=ReadinessVerdict.PASS,
            reason="All good",
        )
        d = c.to_dict()
        assert d["verdict"] == "pass"
        assert d["is_ready"] is True
        assert d["requires_approval"] is False


class TestPublishQueuePlan:
    def test_empty(self):
        qp = PublishQueuePlan()
        assert qp.pending == []
        assert qp.ready == []
        assert qp.queued == []
        assert qp.blocked == []
        assert qp.dry_run is True

    def test_add_and_filter(self):
        qp = PublishQueuePlan()
        item = ArgosExportItem(caption="Test post")
        qp.add(item)
        assert len(qp.items) == 1
        assert len(qp.pending) == 1

    def test_status_filters(self):
        qp = PublishQueuePlan()
        draft = ArgosExportItem(caption="Draft")
        ready = ArgosExportItem(caption="Ready")
        ready.mark_ready()
        queued = ArgosExportItem(caption="Queued")
        queued.mark_queued()
        blocked = ArgosExportItem(caption="Blocked")
        blocked.mark_blocked("test")
        qp.add(draft)
        qp.add(ready)
        qp.add(queued)
        qp.add(blocked)
        assert len(qp.pending) == 1
        assert len(qp.ready) == 1
        assert len(qp.queued) == 1
        assert len(qp.blocked) == 1

    def test_find_by_handle(self):
        qp = PublishQueuePlan()
        t1 = PublishTarget(handle="lucastigrereal")
        t2 = PublishTarget(handle="oinatalrn")
        qp.add(ArgosExportItem(target=t1, caption="A"))
        qp.add(ArgosExportItem(target=t2, caption="B"))
        assert len(qp.find_by_handle("lucastigrereal")) == 1
        assert len(qp.find_by_handle("unknown")) == 0

    def test_find_by_channel(self):
        qp = PublishQueuePlan()
        t1 = PublishTarget(handle="a", channel=PublishChannel.INSTAGRAM_REEL)
        t2 = PublishTarget(handle="b", channel=PublishChannel.INSTAGRAM_FEED)
        qp.add(ArgosExportItem(target=t1, caption="A"))
        qp.add(ArgosExportItem(target=t2, caption="B"))
        assert len(qp.find_by_channel(PublishChannel.INSTAGRAM_REEL)) == 1
        assert len(qp.find_by_channel(PublishChannel.INSTAGRAM_FEED)) == 1
        assert len(qp.find_by_channel(PublishChannel.INSTAGRAM_STORY)) == 0

    def test_to_dict(self):
        qp = PublishQueuePlan(label="Test Queue")
        qp.add(ArgosExportItem(caption="Hello"))
        d = qp.to_dict()
        assert d["label"] == "Test Queue"
        assert d["dry_run"] is True
        assert d["item_count"] == 1
        assert len(d["items"]) == 1


class TestArgosExportPackage:
    def test_defaults(self):
        pkg = ArgosExportPackage()
        assert pkg.dry_run is True
        assert pkg.approval_required is True
        assert pkg.all_ready is False
        assert pkg.item_count == 0

    def test_all_ready_true(self):
        qp = PublishQueuePlan(label="Ready queue")
        checks = [
            PublishReadinessCheck(item_id="i1", verdict=ReadinessVerdict.PASS, passed=5),
            PublishReadinessCheck(item_id="i2", verdict=ReadinessVerdict.PASS, passed=5),
        ]
        pkg = ArgosExportPackage(queue_plan=qp, readiness_checks=checks)
        assert pkg.all_ready is True

    def test_all_ready_mixed(self):
        qp = PublishQueuePlan()
        checks = [
            PublishReadinessCheck(item_id="i1", verdict=ReadinessVerdict.PASS, passed=5),
            PublishReadinessCheck(item_id="i2", verdict=ReadinessVerdict.FAIL, failed=2),
        ]
        pkg = ArgosExportPackage(queue_plan=qp, readiness_checks=checks)
        assert pkg.all_ready is False

    def test_to_dict(self):
        qp = PublishQueuePlan(label="Pkg Test")
        qp.add(ArgosExportItem(caption="Test caption here"))
        checks = [PublishReadinessCheck(item_id=qp.items[0].id, verdict=ReadinessVerdict.PASS, passed=5)]
        pkg = ArgosExportPackage(queue_plan=qp, readiness_checks=checks, label="My Package")
        d = pkg.to_dict()
        assert d["label"] == "My Package"
        assert d["dry_run"] is True
        assert d["item_count"] == 1
        assert d["all_ready"] is True
        assert len(d["readiness_checks"]) == 1


class TestPublisherHandoff:
    def test_defaults(self):
        h = PublisherHandoff()
        assert h.source_module == "publisher_argos"
        assert h.target_system == "ARGOS"
        assert h.dry_run is True
        assert h.approval_required is True
        assert h.approved_by is None

    def test_to_dict(self):
        h = PublisherHandoff(notes="Test handoff")
        d = h.to_dict()
        assert d["source_module"] == "publisher_argos"
        assert d["target_system"] == "ARGOS"
        assert d["dry_run"] is True
        assert d["notes"] == "Test handoff"
        assert "package" in d


class TestNeverPublishes:
    """All models default to dry-run and approval_required — never auto-publish."""

    def test_export_item_always_requires_approval(self):
        item = ArgosExportItem()
        assert item.approval_required is True

    def test_queue_plan_is_dry_run(self):
        qp = PublishQueuePlan()
        assert qp.dry_run is True

    def test_export_package_requires_approval(self):
        pkg = ArgosExportPackage()
        assert pkg.approval_required is True

    def test_handoff_requires_approval(self):
        h = PublisherHandoff()
        assert h.approval_required is True
        assert h.approved_by is None
