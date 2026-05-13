"""P17 Delivery Portal — exception hierarchy."""

from __future__ import annotations


class DeliveryError(Exception):
    """Base exception for all delivery portal errors."""

    def __init__(self, message: str = "", *, delivery_id: str = ""):
        self.delivery_id = delivery_id
        super().__init__(message)


class InvalidStateTransitionError(DeliveryError):
    """Raised when a state transition is not allowed by the state machine."""

    def __init__(
        self,
        current: str,
        target: str,
        *,
        delivery_id: str = "",
    ):
        self.current = current
        self.target = target
        super().__init__(
            f"Cannot transition from '{current}' to '{target}' — invalid state transition.",
            delivery_id=delivery_id,
        )


class HandoffRejectedError(DeliveryError):
    """Raised when a PublisherHandoff fails validation."""

    def __init__(self, reason: str, *, handoff_id: str = "", delivery_id: str = ""):
        self.handoff_id = handoff_id
        self.reason = reason
        super().__init__(
            f"Handoff rejected: {reason}",
            delivery_id=delivery_id,
        )


class DealNotClosedError(DeliveryError):
    """Raised when a Deal is not in closed_won stage."""

    def __init__(self, deal_id: str, current_stage: str, *, delivery_id: str = ""):
        self.deal_id = deal_id
        self.current_stage = current_stage
        super().__init__(
            f"Deal '{deal_id}' is in stage '{current_stage}' — must be 'closed_won' to generate delivery.",
            delivery_id=delivery_id,
        )
