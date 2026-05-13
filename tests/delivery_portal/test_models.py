"""Tests for P17 Delivery Portal — models, enums, helpers, and errors."""

from __future__ import annotations

import pytest

from src.delivery_portal.errors import (
    DealNotClosedError,
    DeliveryError,
    HandoffRejectedError,
    InvalidStateTransitionError,
)
from src.delivery_portal.models import (
    VALID_FEEDBACK_TYPES,
    DeliveryPackage,
    DeliveryStatus,
    FeedbackItem,
    _now_iso,
    _short_id,
    is_valid_transition,
)
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
            label="Test Export Package",
            dry_run=False,
            approval_required=True,
        ),
    }
    kwargs.update(overrides)
    return PublisherHandoff(**kwargs)


def _valid_deal(**overrides) -> Deal:
    kwargs = {
        "lead_id": "lead_001",
        "stage": PipelineStage.CLOSED_WON,
    }
    kwargs.update(overrides)
    return Deal.new(lead_id=kwargs.pop("lead_id"), stage=kwargs.pop("stage"), **kwargs)


# ═══════════════════════════════════════════════════════════════════
# DeliveryStatus enum
# ═══════════════════════════════════════════════════════════════════

class TestDeliveryStatusEnum:
    def test_exactly_five_states(self):
        states = list(DeliveryStatus)
        assert len(states) == 5

    def test_is_string_enum(self):
        assert isinstance(DeliveryStatus.PENDING_DELIVERY, str)

    def test_can_construct_from_value(self):
        assert DeliveryStatus("pending_delivery") == DeliveryStatus.PENDING_DELIVERY
        assert DeliveryStatus("delivered") == DeliveryStatus.DELIVERED
        assert DeliveryStatus("viewed") == DeliveryStatus.VIEWED
        assert DeliveryStatus("feedback_received") == DeliveryStatus.FEEDBACK_RECEIVED
        assert DeliveryStatus("closed") == DeliveryStatus.CLOSED

    def test_values_are_lowercase_snake(self):
        for state in DeliveryStatus:
            assert state.value == state.value.lower()
            assert " " not in state.value


# ═══════════════════════════════════════════════════════════════════
# _now_iso / _short_id helpers
# ═══════════════════════════════════════════════════════════════════

class TestHelpers:
    def test_now_iso_returns_string(self):
        result = _now_iso()
        assert isinstance(result, str)

    def test_now_iso_has_z_suffix(self):
        result = _now_iso()
        assert result.endswith("Z")

    def test_now_iso_contains_t_separator(self):
        result = _now_iso()
        assert "T" in result

    def test_short_id_has_prefix(self):
        result = _short_id("pkg_")
        assert result.startswith("pkg_")

    def test_short_id_total_length(self):
        result = _short_id("dlv_")
        assert len(result) == len("dlv_") + 8  # prefix + 8 hex chars

    def test_short_ids_are_unique(self):
        ids = {_short_id("pkg_") for _ in range(100)}
        assert len(ids) == 100


# ═══════════════════════════════════════════════════════════════════
# FeedbackItem
# ═══════════════════════════════════════════════════════════════════

class TestFeedbackItem:
    def test_new_creates_with_defaults(self):
        fb = FeedbackItem.new(delivery_id="dlv_test")
        assert fb.feedback_type == "ack"
        assert fb.comment == ""
        assert fb.requires_revision is False
        assert fb.recorded_by == "local_user"
        assert fb.delivery_id == "dlv_test"

    def test_new_uses_custom_values(self):
        fb = FeedbackItem.new(
            delivery_id="dlv_test",
            feedback_type="approved",
            comment="Looks great!",
            recorded_by="lucas",
        )
        assert fb.feedback_type == "approved"
        assert fb.comment == "Looks great!"
        assert fb.recorded_by == "lucas"

    def test_feedback_id_has_fbk_prefix(self):
        fb = FeedbackItem.new(delivery_id="dlv_test")
        assert fb.feedback_id.startswith("fbk_")

    def test_invalid_feedback_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid feedback_type"):
            FeedbackItem(feedback_type="invalid_type")

    def test_all_valid_feedback_types_accepted(self):
        for ft in VALID_FEEDBACK_TYPES:
            fb = FeedbackItem(feedback_type=ft)
            assert fb.feedback_type == ft

    def test_to_dict_returns_expected_keys(self):
        fb = FeedbackItem.new(delivery_id="dlv_test", feedback_type="approved")
        d = fb.to_dict()
        expected_keys = {
            "feedback_id", "delivery_id", "feedback_type",
            "comment", "requires_revision", "recorded_at", "recorded_by",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_serializes_values(self):
        fb = FeedbackItem.new(
            delivery_id="dlv_test",
            feedback_type="complaint",
            comment="Not what I expected.",
        )
        d = fb.to_dict()
        assert d["feedback_type"] == "complaint"
        assert d["comment"] == "Not what I expected."
        assert d["requires_revision"] is False

    def test_from_dict_roundtrip(self):
        fb = FeedbackItem.new(
            delivery_id="dlv_test",
            feedback_type="approved",
            comment="Great!",
            requires_revision=False,
        )
        restored = FeedbackItem.from_dict(fb.to_dict())
        assert restored.feedback_id == fb.feedback_id
        assert restored.delivery_id == fb.delivery_id
        assert restored.feedback_type == fb.feedback_type
        assert restored.comment == fb.comment
        assert restored.requires_revision == fb.requires_revision
        assert restored.recorded_at == fb.recorded_at
        assert restored.recorded_by == fb.recorded_by

    def test_from_dict_empty_uses_defaults(self):
        fb = FeedbackItem.from_dict({})
        assert fb.feedback_type == "ack"
        assert fb.comment == ""
        assert fb.requires_revision is False

    def test_direct_construction_sets_fields(self):
        fb = FeedbackItem(
            feedback_id="fbk_001",
            delivery_id="dlv_001",
            feedback_type="approved",
            comment="ok",
            requires_revision=False,
        )
        assert fb.feedback_id == "fbk_001"
        assert fb.delivery_id == "dlv_001"


# ═══════════════════════════════════════════════════════════════════
# DeliveryPackage
# ═══════════════════════════════════════════════════════════════════

class TestDeliveryPackage:
    def test_new_creates_with_correct_prefixes(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        assert pkg.package_id.startswith("pkg_")
        assert pkg.delivery_id.startswith("dlv_")

    def test_new_defaults_to_pending_delivery(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        assert pkg.status == DeliveryStatus.PENDING_DELIVERY

    def test_new_defaults_dry_run_true(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        assert pkg.dry_run is True

    def test_new_dry_run_false(self):
        pkg = DeliveryPackage.new(
            handoff=_valid_handoff(),
            deal=_valid_deal(),
            dry_run=False,
        )
        assert pkg.dry_run is False

    def test_new_defaults_approval_required_true(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        assert pkg.approval_required is True

    def test_new_stores_handoff(self):
        handoff = _valid_handoff()
        pkg = DeliveryPackage.new(handoff=handoff, deal=_valid_deal())
        assert pkg.handoff is handoff

    def test_new_stores_deal(self):
        deal = _valid_deal()
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=deal)
        assert pkg.deal is deal

    def test_feedback_starts_empty(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        assert pkg.feedback == []

    def test_created_by_custom(self):
        pkg = DeliveryPackage.new(
            handoff=_valid_handoff(),
            deal=_valid_deal(),
            created_by="lucas",
        )
        assert pkg.created_by == "lucas"

    def test_created_at_is_iso_string(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        assert isinstance(pkg.created_at, str)
        assert "T" in pkg.created_at

    def test_to_dict_includes_all_keys(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        d = pkg.to_dict()
        expected_keys = {
            "package_id", "delivery_id", "status", "handoff", "deal",
            "feedback", "created_at", "created_by", "dry_run", "approval_required",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_status_is_string_value(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        d = pkg.to_dict()
        assert d["status"] == "pending_delivery"

    def test_to_dict_handoff_is_dict(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        d = pkg.to_dict()
        assert isinstance(d["handoff"], dict)
        assert "handoff_id" in d["handoff"]

    def test_to_dict_deal_is_dict(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        d = pkg.to_dict()
        assert isinstance(d["deal"], dict)
        assert "id" in d["deal"]

    def test_from_dict_roundtrip(self):
        pkg = DeliveryPackage.new(
            handoff=_valid_handoff(),
            deal=_valid_deal(),
            created_by="lucas",
            dry_run=False,
        )
        restored = DeliveryPackage.from_dict(pkg.to_dict())
        assert restored.package_id == pkg.package_id
        assert restored.delivery_id == pkg.delivery_id
        assert restored.status == pkg.status
        assert restored.created_by == pkg.created_by
        assert restored.dry_run == pkg.dry_run
        assert restored.approval_required == pkg.approval_required

    def test_from_dict_restores_feedback_list(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        fb = FeedbackItem.new(delivery_id=pkg.delivery_id)
        pkg.feedback.append(fb)
        restored = DeliveryPackage.from_dict(pkg.to_dict())
        assert len(restored.feedback) == 1
        assert restored.feedback[0].feedback_id == fb.feedback_id

    def test_from_dict_empty_feedback(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        restored = DeliveryPackage.from_dict(pkg.to_dict())
        assert restored.feedback == []

    def test_from_dict_defaults_on_empty(self):
        pkg = DeliveryPackage.from_dict({
            "deal": {"id": "deal_x", "lead_id": "lead_x"},
        })
        assert pkg.status == DeliveryStatus.PENDING_DELIVERY
        assert pkg.package_id == ""

    def test_package_id_and_delivery_id_are_different(self):
        pkg = DeliveryPackage.new(handoff=_valid_handoff(), deal=_valid_deal())
        assert pkg.package_id != pkg.delivery_id


# ═══════════════════════════════════════════════════════════════════
# is_valid_transition
# ═══════════════════════════════════════════════════════════════════

class TestStateTransitions:
    def test_valid_pending_to_delivered(self):
        assert is_valid_transition(
            DeliveryStatus.PENDING_DELIVERY, DeliveryStatus.DELIVERED
        ) is True

    def test_valid_delivered_to_viewed(self):
        assert is_valid_transition(
            DeliveryStatus.DELIVERED, DeliveryStatus.VIEWED
        ) is True

    def test_valid_viewed_to_feedback_received(self):
        assert is_valid_transition(
            DeliveryStatus.VIEWED, DeliveryStatus.FEEDBACK_RECEIVED
        ) is True

    def test_valid_feedback_received_to_closed(self):
        assert is_valid_transition(
            DeliveryStatus.FEEDBACK_RECEIVED, DeliveryStatus.CLOSED
        ) is True

    def test_closed_has_no_valid_transitions(self):
        for state in DeliveryStatus:
            assert is_valid_transition(DeliveryStatus.CLOSED, state) is False

    def test_invalid_skip_stage(self):
        assert is_valid_transition(
            DeliveryStatus.PENDING_DELIVERY, DeliveryStatus.VIEWED
        ) is False

    def test_invalid_reverse(self):
        assert is_valid_transition(
            DeliveryStatus.DELIVERED, DeliveryStatus.PENDING_DELIVERY
        ) is False

    def test_invalid_same_state(self):
        assert is_valid_transition(
            DeliveryStatus.PENDING_DELIVERY, DeliveryStatus.PENDING_DELIVERY
        ) is False


# ═══════════════════════════════════════════════════════════════════
# Errors
# ═══════════════════════════════════════════════════════════════════

class TestErrors:
    def test_delivery_error_is_exception(self):
        err = DeliveryError("test")
        assert isinstance(err, Exception)

    def test_delivery_error_stores_message(self):
        err = DeliveryError("something went wrong")
        assert "something went wrong" in str(err)

    def test_delivery_error_stores_delivery_id(self):
        err = DeliveryError("err", delivery_id="dlv_001")
        assert err.delivery_id == "dlv_001"

    def test_invalid_state_transition_has_current_and_target(self):
        err = InvalidStateTransitionError(
            current="pending_delivery",
            target="closed",
            delivery_id="dlv_001",
        )
        assert err.current == "pending_delivery"
        assert err.target == "closed"
        assert "pending_delivery" in str(err)
        assert "closed" in str(err)

    def test_invalid_state_transition_is_delivery_error(self):
        err = InvalidStateTransitionError("a", "b")
        assert isinstance(err, DeliveryError)

    def test_handoff_rejected_error_stores_handoff_id(self):
        err = HandoffRejectedError(
            "dry_run is True",
            handoff_id="ho_abc",
        )
        assert err.handoff_id == "ho_abc"
        assert err.reason == "dry_run is True"
        assert "dry_run is True" in str(err)

    def test_handoff_rejected_error_is_delivery_error(self):
        err = HandoffRejectedError("reason")
        assert isinstance(err, DeliveryError)

    def test_deal_not_closed_error_stores_deal_id(self):
        err = DealNotClosedError(
            deal_id="deal_001",
            current_stage="prospecting",
        )
        assert err.deal_id == "deal_001"
        assert err.current_stage == "prospecting"
        assert "deal_001" in str(err)
        assert "prospecting" in str(err)

    def test_deal_not_closed_error_is_delivery_error(self):
        err = DealNotClosedError("deal_x", "prospecting")
        assert isinstance(err, DeliveryError)

    def test_all_errors_can_be_raised_and_caught(self):
        for err_cls in [
            DeliveryError,
            InvalidStateTransitionError,
            HandoffRejectedError,
            DealNotClosedError,
        ]:
            try:
                if err_cls is InvalidStateTransitionError:
                    raise err_cls("a", "b")
                elif err_cls is DealNotClosedError:
                    raise err_cls("did", "prospecting")
                elif err_cls is HandoffRejectedError:
                    raise err_cls("reason")
                else:
                    raise err_cls("base")
            except DeliveryError:
                pass  # caught by base class
