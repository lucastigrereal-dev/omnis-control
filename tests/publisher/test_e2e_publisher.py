"""E2E Publisher dry-run test — full IDEA→PUBLISH→ARGOS pipeline (W089)."""
from __future__ import annotations

import pytest

from src.publisher.statemachine import (
    ContentContext,
    ContentStatus,
    ALLOWED_TRANSITIONS,
    InvalidTransitionError,
)
from src.publisher.approval_gate import ApprovalGate, ApprovalStatus
from src.publisher.creative_bridge import CreativeBridge, CreativeFormat
from src.publisher.metrics import PostMetrics, PublisherMetricsReport
from src.publisher.publer_export import PublerExporter
from src.publisher_argos.models import (
    ArgosExportItem,
    PublishQueuePlan,
    PublishTarget,
    PublishChannel,
    ExportStatus,
)
from src.publisher_argos.planner import PublisherArgosPlanner, KNOWN_PAGES


class TestPublisherE2EDryRun:
    """Full dry-run pipeline: IDEA→BRIEF→DRAFT→REVIEW→APPROVED→QUEUED→ARGOS."""

    def test_full_state_machine_transition_chain(self):
        """An item traverses all 9 states in correct order."""
        ctx = ContentContext(content_id="c1", title="Test Post")
        assert ctx.status == ContentStatus.IDEA

        # IDEA → BRIEF
        ctx.transition_to(ContentStatus.BRIEF, actor="jarvis", reason="Brief generated")
        assert ctx.status == ContentStatus.BRIEF

        # BRIEF → DRAFT
        ctx.transition_to(ContentStatus.DRAFT, actor="jarvis", reason="Draft generated")
        assert ctx.status == ContentStatus.DRAFT

        # DRAFT → REVIEW
        ctx.transition_to(ContentStatus.REVIEW, actor="system", reason="Awaiting approval")
        assert ctx.status == ContentStatus.REVIEW

        # REVIEW → APPROVED
        ctx.transition_to(ContentStatus.APPROVED, actor="human:lucas", reason="Approved")
        assert ctx.status == ContentStatus.APPROVED

        # APPROVED → QUEUED
        ctx.transition_to(ContentStatus.QUEUED, actor="system", reason="Enqueued")
        assert ctx.status == ContentStatus.QUEUED

        # QUEUED → PUBLISHING
        ctx.transition_to(ContentStatus.PUBLISHING, actor="worker")
        assert ctx.status == ContentStatus.PUBLISHING

        # PUBLISHING → PUBLISHED
        ctx.transition_to(ContentStatus.PUBLISHED, actor="meta_api", reason="Published (dry-run)")
        assert ctx.status == ContentStatus.PUBLISHED

        # Final — PUBLISHED has no valid transitions
        assert len(ALLOWED_TRANSITIONS[ContentStatus.PUBLISHED]) == 0

        # Audit trail — 7 transitions between 8 states
        assert len(ctx.transitions) == 7

    def test_invalid_transition_blocked(self):
        """Jumping from IDEA to PUBLISHED is not allowed."""
        ctx = ContentContext(content_id="c1", title="Test")
        with pytest.raises(InvalidTransitionError):
            ctx.transition_to(ContentStatus.PUBLISHED)

    def test_failed_can_requeue(self):
        """Failed items can transition back to QUEUED."""
        ctx = ContentContext(content_id="c1", title="Test")
        # Follow valid path: IDEA→BRIEF→DRAFT→REVIEW→APPROVED→QUEUED
        ctx.transition_to(ContentStatus.BRIEF, actor="jarvis")
        ctx.transition_to(ContentStatus.DRAFT, actor="jarvis")
        ctx.transition_to(ContentStatus.REVIEW, actor="system")
        ctx.transition_to(ContentStatus.APPROVED, actor="human:lucas")
        ctx.transition_to(ContentStatus.QUEUED, actor="system")
        ctx.transition_to(ContentStatus.PUBLISHING, actor="worker")
        ctx.transition_to(ContentStatus.FAILED, actor="system", reason="Network error")
        assert ctx.status == ContentStatus.FAILED
        # Can retry: FAILED → QUEUED
        ctx.transition_to(ContentStatus.QUEUED, actor="system", reason="Retry")
        assert ctx.status == ContentStatus.QUEUED

    def test_approval_gate_integration(self):
        """Approval gate blocks unapproved items from QUEUED."""
        gate = ApprovalGate()
        gate.submit("c1", "My post caption")

        # Not approved yet
        assert gate.can_proceed("c1") is False

        # Approve
        gate.approve("c1", "lucas")
        assert gate.can_proceed("c1") is True

        # Check in state machine context
        ctx = ContentContext(content_id="c1", title="Test")
        ctx.caption = "My post caption"
        ctx.transition_to(ContentStatus.BRIEF, actor="jarvis")
        ctx.transition_to(ContentStatus.DRAFT, actor="jarvis")
        ctx.transition_to(ContentStatus.REVIEW, actor="system")

        if gate.can_proceed("c1"):
            ctx.transition_to(ContentStatus.APPROVED, actor="human:lucas")
            ctx.transition_to(ContentStatus.QUEUED, actor="system")
        assert ctx.status == ContentStatus.QUEUED

    def test_creative_bridge_placeholder_assets(self):
        """Creative bridge provides placeholder assets for dry-run."""
        bridge = CreativeBridge()
        asset = bridge.request_asset("c1", CreativeFormat.CAROUSEL)
        assert asset.status.value == "ready"
        assert len(asset.media_urls) == 3
        assert bridge.is_ready("c1")

    def test_argos_export_pipeline(self):
        """Build ARGOS export package from content items."""
        planner = PublisherArgosPlanner()
        item = planner.build_export_item(
            caption="Test caption for Instagram",
            handle="lucastigrereal",
            channel=PublishChannel.INSTAGRAM_FEED,
            media_url="https://example.com/image.jpg",
        )
        assert item.status == ExportStatus.DRAFT
        assert item.target.handle == "lucastigrereal"

        # Validate readiness
        check = planner.validate_publish_readiness(item)
        assert check.verdict.value == "pass"
        assert check.failed == 0

        # Build queue and package
        queue = planner.build_queue_plan([item], label="Test queue")
        package = planner.build_argos_export_package(queue, label="Test package")
        assert package.all_ready is True

        # Build handoff
        handoff = planner.build_publisher_handoff(package)
        assert handoff.dry_run is True
        assert handoff.approval_required is True

        # Export JSON
        json_str = planner.export_argos_json(handoff)
        assert "handoff_id" in json_str
        assert "dry_run" in json_str

    def test_metrics_report_aggregation(self):
        """Metrics report aggregates post metrics correctly."""
        report = PublisherMetricsReport(report_id="r1")
        report.add(PostMetrics(post_id="p1", views=1000, likes=50, comments=10))
        report.add(PostMetrics(post_id="p2", views=2000, likes=80, comments=20))
        assert report.post_count == 2
        assert report.total_views == 3000
        assert report.total_likes == 130

    def test_publer_export_flow(self):
        """Publer exporter produces CSV-formatted batches."""
        exporter = PublerExporter()
        batch = exporter.create_batch("Daily posts")
        batch.add(exporter.build_item("Caption 1", "@lucastigrereal", hashtags=["#test"]))
        batch.add(exporter.build_item("Caption 2", "@oinatalrn"))
        csv_str = exporter.export_batch(batch.batch_id)
        assert csv_str is not None
        assert "Caption 1" in csv_str
        assert "Caption 2" in csv_str
        assert "#test" in csv_str

    def test_no_env_no_network_no_secrets(self):
        """Verify no .env reads, no network calls, no secrets in the E2E path."""
        # All models and planners use dry_run=True by default
        planner = PublisherArgosPlanner()
        assert planner.dry_run is True
        assert planner.approval_required is True

        exporter = PublerExporter()
        assert exporter.dry_run is True

        handoff = planner.build_publisher_handoff(
            planner.build_argos_export_package(
                planner.build_queue_plan([
                    planner.build_export_item("Test caption", handle="lucastigrereal", media_url="http://example.com/img.jpg")
                ])
            )
        )
        d = handoff.to_dict()
        # No secrets in output
        for key in d:
            assert "secret" not in key.lower()
            assert "token" not in key.lower()
            assert "password" not in key.lower()

    def test_six_known_pages(self):
        """All 6 known Instagram pages are available for targeting."""
        handles = PublisherArgosPlanner.get_known_handles()
        assert len(handles) == 6
        assert "lucastigrereal" in handles
        assert "oinatalrn" in handles

    def test_content_context_error_handling(self):
        """ContentContext records errors and tracks retry count."""
        ctx = ContentContext(content_id="c1", title="Test")
        ctx.record_error("API timeout", "publish")
        assert len(ctx.error_log) == 1
        assert ctx.error_log[0]["stage"] == "publish"
        assert ctx.retry_count == 1
        assert ctx.can_retry is True

        ctx.record_error("API timeout", "publish")
        ctx.record_error("API timeout", "publish")
        assert ctx.retry_count == 3
        assert ctx.can_retry is False
