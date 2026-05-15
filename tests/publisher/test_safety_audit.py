"""Publisher Safety Audit (W090) — security validation of publisher pipeline."""
from __future__ import annotations

import pytest

from src.publisher.statemachine import ContentContext, ContentStatus, ALLOWED_TRANSITIONS
from src.publisher.approval_gate import ApprovalGate
from src.publisher_argos.planner import PublisherArgosPlanner
from src.publisher_argos.models import ArgosExportItem, PublisherHandoff
from src.publisher.publer_export import PublerExporter


class TestPublisherSafetyAudit:
    """Publisher safety audit — guardrail verification."""

    def test_dry_run_default_on_all_planners(self):
        """Every planner and exporter defaults to dry_run=True."""
        planner = PublisherArgosPlanner()
        assert planner.dry_run is True
        assert planner.approval_required is True

        exporter = PublerExporter()
        assert exporter.dry_run is True

    def test_approval_never_auto_approved(self):
        """Approval is never auto-approved — requires explicit human action."""
        gate = ApprovalGate()
        gate.submit("c1", "Test caption")
        # Without explicit approve(), can_proceed must be False
        assert gate.can_proceed("c1") is False
        # Only after explicit approval
        gate.approve("c1", "lucas")
        assert gate.can_proceed("c1") is True

    def test_handoff_never_auto_approved(self):
        """PublisherHandoff never sets approved_by automatically."""
        planner = PublisherArgosPlanner()
        item = planner.build_export_item("Test caption", media_url="http://example.com/img.jpg")
        queue = planner.build_queue_plan([item])
        package = planner.build_argos_export_package(queue)
        handoff = planner.build_publisher_handoff(package)
        assert handoff.approved_by is None
        assert handoff.dry_run is True

    def test_no_real_publish_in_export_items(self):
        """ArgosExportItem never contains real publish triggers."""
        item = ArgosExportItem(
            caption="Test caption",
            media_url="http://example.com/img.jpg",
        )
        d = item.to_dict()
        # No publish-related flags
        assert "publish" not in d.get("status", "")

    def test_no_secrets_in_output_dicts(self):
        """All to_dict() outputs are free of sensitive keys."""
        planner = PublisherArgosPlanner()
        item = planner.build_export_item("Test caption", media_url="http://example.com/img.jpg")
        queue = planner.build_queue_plan([item])
        package = planner.build_argos_export_package(queue)
        handoff = planner.build_publisher_handoff(package)

        for obj, name in [(item.to_dict(), "item"), (queue.to_dict(), "queue"),
                          (package.to_dict(), "package"), (handoff.to_dict(), "handoff")]:
            for key in obj:
                assert "secret" not in key.lower(), f"{name} has secret key: {key}"
                assert "token" not in key.lower(), f"{name} has token key: {key}"
                assert "password" not in key.lower(), f"{name} has password key: {key}"
                assert "api_key" not in key.lower(), f"{name} has api_key key: {key}"

    def test_state_machine_no_destructive_jump_to_published(self):
        """Cannot jump directly from IDEA to PUBLISHED (bypasses approval)."""
        ctx = ContentContext(content_id="c1", title="Test")
        valid = ContentStatus.PUBLISHED in ALLOWED_TRANSITIONS.get(ContentStatus.IDEA, [])
        assert valid is False

    def test_known_pages_are_read_only(self):
        """Known pages cannot be mutated during export."""
        planner = PublisherArgosPlanner()
        handles_before = set(planner.get_known_handles())
        assert len(handles_before) == 6
        # Build export items — should not change known handles
        for _ in range(3):
            planner.build_export_item("Test")
        handles_after = set(planner.get_known_handles())
        assert handles_before == handles_after

    def test_forbidden_patterns_absent(self):
        """Scan source modules for forbidden patterns (no eval, no subprocess)."""
        import inspect
        from src.publisher import pipeline, statemachine, worker, approval_gate, creative_bridge, metrics, publer_export

        modules = [pipeline, statemachine, worker, approval_gate, creative_bridge, metrics, publer_export]
        forbidden = ["eval(", "exec(", "__import__(", "subprocess", "os.system", "shutil.rmtree"]

        for mod in modules:
            source = inspect.getsource(mod)
            for pattern in forbidden:
                assert pattern not in source, f"Forbidden pattern '{pattern}' found in {mod.__name__}"

    def test_no_network_calls_in_source(self):
        """No socket/requests/urllib imports in publisher modules."""
        import inspect
        from src.publisher import pipeline, statemachine, worker, approval_gate, creative_bridge, metrics, publer_export

        modules = [pipeline, statemachine, worker, approval_gate, creative_bridge, metrics, publer_export]
        forbidden_imports = ["import socket", "import requests", "import urllib", "import http.client",
                             "from socket", "from requests", "from urllib"]

        for mod in modules:
            source = inspect.getsource(mod)
            for imp in forbidden_imports:
                assert imp not in source, f"Forbidden import '{imp}' in {mod.__name__}"

    def test_idempotency_key_present(self):
        """ContentContext always has an idempotency key for safe retry."""
        ctx = ContentContext(content_id="c1", title="Test")
        assert ctx.idempotency_key != ""
        assert len(ctx.idempotency_key) > 0
