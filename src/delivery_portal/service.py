"""P17 Delivery Portal — DeliveryPlanner service (build, feedback, state machine)."""

from __future__ import annotations

from src.delivery_portal.errors import (
    DealNotClosedError,
    HandoffRejectedError,
    InvalidStateTransitionError,
)
from src.delivery_portal.models import (
    DeliveryPackage,
    DeliveryStatus,
    FeedbackItem,
    _now_iso,
    is_valid_transition,
)
from src.publisher_argos.models import PublisherHandoff
from src.sales_crm.models import Deal, PipelineStage


class DeliveryPlanner:
    """Plans and manages delivery packages from publisher handoffs + closed deals."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def build_delivery_package(
        self,
        handoff: PublisherHandoff,
        deal: Deal,
        *,
        created_by: str = "local_user",
        approval_required: bool = True,
    ) -> DeliveryPackage:
        """Validate handoff + deal against the delivery contract, build a package.

        Raises:
            HandoffRejectedError: if handoff fails validation.
            DealNotClosedError: if deal is not closed_won.
        """
        self._validate_handoff(handoff)
        self._validate_deal(deal)

        return DeliveryPackage.new(
            handoff=handoff,
            deal=deal,
            created_by=created_by,
            dry_run=self.dry_run,
            approval_required=approval_required,
        )

    def add_feedback(
        self,
        pkg: DeliveryPackage,
        feedback_type: str,
        comment: str,
        *,
        recorded_by: str = "local_user",
    ) -> DeliveryPackage:
        """Add a FeedbackItem to the package and transition to feedback_received.

        If the package is not in a state that can receive feedback (viewed or beyond),
        the state transition will fail via transition_state().
        """
        feedback = FeedbackItem.new(
            delivery_id=pkg.delivery_id,
            feedback_type=feedback_type,
            comment=comment,
            recorded_by=recorded_by,
            requires_revision=(feedback_type == "adjustment"),
        )

        pkg.feedback.append(feedback)
        self.transition_state(pkg, DeliveryStatus.FEEDBACK_RECEIVED)
        return pkg

    def transition_state(
        self,
        pkg: DeliveryPackage,
        target: DeliveryStatus,
    ) -> DeliveryPackage:
        """Transition the package to a new state if valid.

        Raises:
            InvalidStateTransitionError: if the transition is not allowed.
        """
        current = pkg.status
        if not is_valid_transition(current, target):
            raise InvalidStateTransitionError(
                current=current.value,
                target=target.value,
                delivery_id=pkg.delivery_id,
            )
        pkg.status = target
        return pkg

    # ── private validators ────────────────────────────────────────

    @staticmethod
    def _validate_handoff(handoff: PublisherHandoff) -> None:
        if handoff.dry_run:
            raise HandoffRejectedError(
                "handoff.dry_run is True — only real handoffs can become deliveries.",
                handoff_id=handoff.id,
            )
        if not handoff.approval_required:
            raise HandoffRejectedError(
                "handoff.approval_required is False — delivery requires approval gate.",
                handoff_id=handoff.id,
            )
        if handoff.approved_by is None:
            raise HandoffRejectedError(
                "handoff.approved_by is None — handoff must be approved before delivery.",
                handoff_id=handoff.id,
            )
        if handoff.package is None:
            raise HandoffRejectedError(
                "handoff.package is None — handoff must contain an export package.",
                handoff_id=handoff.id,
            )

    @staticmethod
    def _validate_deal(deal: Deal) -> None:
        if deal.stage != PipelineStage.CLOSED_WON:
            raise DealNotClosedError(
                deal_id=deal.id,
                current_stage=deal.stage.value,
            )
