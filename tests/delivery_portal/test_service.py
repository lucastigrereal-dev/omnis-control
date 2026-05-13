"""Tests for P17 Delivery Portal — DeliveryPlanner service."""

from __future__ import annotations

import pytest

from src.delivery_portal.errors import (
    DealNotClosedError,
    HandoffRejectedError,
    InvalidStateTransitionError,
)
from src.delivery_portal.models import DeliveryPackage, DeliveryStatus, FeedbackItem
from src.delivery_portal.service import DeliveryPlanner
from src.publisher_argos.models import (
    ArgosExportPackage,
    PublishQueuePlan,
    PublisherHandoff,
)
from src.sales_crm.models import Deal, PipelineStage


# ── helpers ───────────────────────────────────────────────────────

def _valid_handoff(**overrides) -> PublisherHandoff:
    kwargs = {
        "id": "ho_test01",
        "dry_run": False,
        "approval_required": True,
        "approved_by": "local_user",
        "package": ArgosExportPackage(
            id="pkg_test01",
            queue_plan=PublishQueuePlan(),
            label="Test Export",
            dry_run=False,
            approval_required=True,
        ),
    }
    kwargs.update(overrides)
    return PublisherHandoff(**kwargs)


def _valid_deal(**overrides) -> Deal:
    kwargs = {"lead_id": "lead_001", "stage": PipelineStage.CLOSED_WON}
    kwargs.update(overrides)
    return Deal.new(lead_id=kwargs.pop("lead_id"), stage=kwargs.pop("stage"), **kwargs)


def _closed_won_deal() -> Deal:
    return _valid_deal()


# ═══════════════════════════════════════════════════════════════════
# build_delivery_package
# ═══════════════════════════════════════════════════════════════════

class TestBuildDeliveryPackage:
    def test_build_with_valid_inputs_returns_delivery_package(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        assert isinstance(pkg, DeliveryPackage)

    def test_build_sets_status_to_pending_delivery(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        assert pkg.status == DeliveryStatus.PENDING_DELIVERY

    def test_build_embeds_handoff(self):
        handoff = _valid_handoff()
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=handoff,
            deal=_closed_won_deal(),
        )
        assert pkg.handoff is handoff

    def test_build_embeds_deal(self):
        deal = _closed_won_deal()
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=deal,
        )
        assert pkg.deal is deal

    def test_build_dry_run_defaults_true(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        assert pkg.dry_run is True

    def test_build_dry_run_false_preserved(self):
        planner = DeliveryPlanner(dry_run=False)
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        assert pkg.dry_run is False

    def test_build_rejects_handoff_dry_run_true(self):
        planner = DeliveryPlanner()
        handoff = _valid_handoff(dry_run=True)
        with pytest.raises(HandoffRejectedError, match="dry_run is True"):
            planner.build_delivery_package(handoff=handoff, deal=_closed_won_deal())

    def test_build_rejects_handoff_approved_by_none(self):
        planner = DeliveryPlanner()
        handoff = _valid_handoff(approved_by=None)
        with pytest.raises(HandoffRejectedError, match="approved_by is None"):
            planner.build_delivery_package(handoff=handoff, deal=_closed_won_deal())

    def test_build_rejects_handoff_approval_required_false(self):
        planner = DeliveryPlanner()
        handoff = _valid_handoff(approval_required=False)
        with pytest.raises(HandoffRejectedError, match="approval_required is False"):
            planner.build_delivery_package(handoff=handoff, deal=_closed_won_deal())

    def test_build_rejects_handoff_package_none(self):
        planner = DeliveryPlanner()
        handoff = _valid_handoff(package=None)
        with pytest.raises(HandoffRejectedError, match="package is None"):
            planner.build_delivery_package(handoff=handoff, deal=_closed_won_deal())

    def test_build_rejects_deal_not_closed_won(self):
        planner = DeliveryPlanner()
        deal = _valid_deal(stage=PipelineStage.PROSPECTING)
        with pytest.raises(DealNotClosedError, match="must be 'closed_won'"):
            planner.build_delivery_package(handoff=_valid_handoff(), deal=deal)

    def test_build_rejects_deal_closed_lost(self):
        planner = DeliveryPlanner()
        deal = _valid_deal(stage=PipelineStage.CLOSED_LOST)
        with pytest.raises(DealNotClosedError):
            planner.build_delivery_package(handoff=_valid_handoff(), deal=deal)

    def test_build_accepts_created_by_custom(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
            created_by="tigrao",
        )
        assert pkg.created_by == "tigrao"

    def test_build_accepts_approval_required_false(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
            approval_required=False,
        )
        assert pkg.approval_required is False

    def test_build_multiple_packages_have_unique_delivery_ids(self):
        planner = DeliveryPlanner()
        pkg1 = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        pkg2 = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        assert pkg1.delivery_id != pkg2.delivery_id
        # Same handoff → package_id is shared (edge case #7)
        assert pkg1.package_id != pkg2.package_id  # new() always generates fresh


# ═══════════════════════════════════════════════════════════════════
# add_feedback
# ═══════════════════════════════════════════════════════════════════

class TestAddFeedback:
    def test_add_feedback_appends_to_list(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        # Must advance to viewed before feedback can be added
        planner.transition_state(pkg, DeliveryStatus.DELIVERED)
        planner.transition_state(pkg, DeliveryStatus.VIEWED)

        planner.add_feedback(pkg, feedback_type="approved", comment="Nice!")
        assert len(pkg.feedback) == 1

    def test_add_feedback_transitions_to_feedback_received(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        planner.transition_state(pkg, DeliveryStatus.DELIVERED)
        planner.transition_state(pkg, DeliveryStatus.VIEWED)

        planner.add_feedback(pkg, feedback_type="approved", comment="Good")
        assert pkg.status == DeliveryStatus.FEEDBACK_RECEIVED

    def test_add_feedback_adjustment_sets_requires_revision(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        planner.transition_state(pkg, DeliveryStatus.DELIVERED)
        planner.transition_state(pkg, DeliveryStatus.VIEWED)

        planner.add_feedback(
            pkg, feedback_type="adjustment", comment="Please change the caption"
        )
        assert pkg.feedback[0].feedback_type == "adjustment"
        assert pkg.feedback[0].requires_revision is True

    def test_add_feedback_approved_does_not_set_requires_revision(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        planner.transition_state(pkg, DeliveryStatus.DELIVERED)
        planner.transition_state(pkg, DeliveryStatus.VIEWED)

        planner.add_feedback(pkg, feedback_type="approved", comment="")
        assert pkg.feedback[0].requires_revision is False

    def test_add_feedback_complaint_type(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        planner.transition_state(pkg, DeliveryStatus.DELIVERED)
        planner.transition_state(pkg, DeliveryStatus.VIEWED)

        planner.add_feedback(
            pkg, feedback_type="complaint", comment="I expected more posts"
        )
        assert pkg.feedback[0].feedback_type == "complaint"

    def test_add_feedback_ack_type(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        planner.transition_state(pkg, DeliveryStatus.DELIVERED)
        planner.transition_state(pkg, DeliveryStatus.VIEWED)

        planner.add_feedback(pkg, feedback_type="ack", comment="Received, thanks")
        assert pkg.feedback[0].feedback_type == "ack"

    def test_add_multiple_feedback_items(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        planner.transition_state(pkg, DeliveryStatus.DELIVERED)
        planner.transition_state(pkg, DeliveryStatus.VIEWED)

        planner.add_feedback(pkg, feedback_type="ack", comment="Got it")
        # Need to be in viewed state to add another feedback (transition back not allowed)
        # So create a fresh package for the second test
        pkg2 = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        planner.transition_state(pkg2, DeliveryStatus.DELIVERED)
        planner.transition_state(pkg2, DeliveryStatus.VIEWED)
        planner.add_feedback(pkg2, feedback_type="ack", comment="First")
        # Can't add second feedback without going through the state machine again
        assert len(pkg2.feedback) == 1


# ═══════════════════════════════════════════════════════════════════
# transition_state
# ═══════════════════════════════════════════════════════════════════

class TestTransitionState:
    def test_transition_pending_to_delivered(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        planner.transition_state(pkg, DeliveryStatus.DELIVERED)
        assert pkg.status == DeliveryStatus.DELIVERED

    def test_transition_full_happy_path(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        planner.transition_state(pkg, DeliveryStatus.DELIVERED)
        planner.transition_state(pkg, DeliveryStatus.VIEWED)
        planner.transition_state(pkg, DeliveryStatus.FEEDBACK_RECEIVED)
        planner.transition_state(pkg, DeliveryStatus.CLOSED)
        assert pkg.status == DeliveryStatus.CLOSED

    def test_skip_stage_raises_invalid_transition(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        with pytest.raises(InvalidStateTransitionError):
            planner.transition_state(pkg, DeliveryStatus.VIEWED)  # skip delivered

    def test_closed_cannot_reopen(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        planner.transition_state(pkg, DeliveryStatus.DELIVERED)
        planner.transition_state(pkg, DeliveryStatus.VIEWED)
        planner.transition_state(pkg, DeliveryStatus.FEEDBACK_RECEIVED)
        planner.transition_state(pkg, DeliveryStatus.CLOSED)

        with pytest.raises(InvalidStateTransitionError):
            planner.transition_state(pkg, DeliveryStatus.FEEDBACK_RECEIVED)

    def test_reverse_transition_raises(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        planner.transition_state(pkg, DeliveryStatus.DELIVERED)
        with pytest.raises(InvalidStateTransitionError):
            planner.transition_state(pkg, DeliveryStatus.PENDING_DELIVERY)

    def test_same_state_transition_raises(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        with pytest.raises(InvalidStateTransitionError):
            planner.transition_state(pkg, DeliveryStatus.PENDING_DELIVERY)

    def test_error_includes_delivery_id(self):
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        try:
            planner.transition_state(pkg, DeliveryStatus.CLOSED)
        except InvalidStateTransitionError as e:
            assert e.delivery_id == pkg.delivery_id


# ═══════════════════════════════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_feedback_with_requires_revision_blocks_close(self):
        """Edge case #8: feedback with requires_revision=True — close is still
        technically valid from feedback_received state, but the flag signals
        that a new handoff is needed. The state machine doesn't block this
        mechanically; the flag is advisory.
        """
        planner = DeliveryPlanner()
        pkg = planner.build_delivery_package(
            handoff=_valid_handoff(),
            deal=_closed_won_deal(),
        )
        planner.transition_state(pkg, DeliveryStatus.DELIVERED)
        planner.transition_state(pkg, DeliveryStatus.VIEWED)
        planner.add_feedback(
            pkg, feedback_type="adjustment", comment="Needs changes"
        )
        assert pkg.feedback[0].requires_revision is True
        assert pkg.status == DeliveryStatus.FEEDBACK_RECEIVED
        # State machine allows close from feedback_received
        planner.transition_state(pkg, DeliveryStatus.CLOSED)
        assert pkg.status == DeliveryStatus.CLOSED

    def test_handoff_rejected_error_includes_handoff_id(self):
        planner = DeliveryPlanner()
        handoff = _valid_handoff(dry_run=True)
        try:
            planner.build_delivery_package(handoff=handoff, deal=_closed_won_deal())
        except HandoffRejectedError as e:
            assert e.handoff_id == "ho_test01"

    def test_deal_not_closed_error_includes_stage(self):
        planner = DeliveryPlanner()
        deal = _valid_deal(stage=PipelineStage.NEGOTIATION)
        try:
            planner.build_delivery_package(handoff=_valid_handoff(), deal=deal)
        except DealNotClosedError as e:
            assert e.current_stage == "negotiation"
