"""Tests for approval center models."""
from src.approval_center.models import (
    ApprovalRequest,
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_REJECTED,
)


def test_new_generates_request_id():
    req = ApprovalRequest.new("publish reels @lucastigrereal")
    assert req.request_id.startswith("req_")
    assert req.status == APPROVAL_STATUS_PENDING
    assert req.resolved_at is None


def test_to_dict_round_trip():
    req = ApprovalRequest.new("campanha hotel boutique", capability_id="campaign_package", risk_level="high")
    d = req.to_dict()
    req2 = ApprovalRequest.from_dict(d)
    assert req2.request_id == req.request_id
    assert req2.capability_id == "campaign_package"
    assert req2.risk_level == "high"


def test_status_constants_are_strings():
    assert APPROVAL_STATUS_PENDING == "pending"
    assert APPROVAL_STATUS_APPROVED == "approved"
    assert APPROVAL_STATUS_REJECTED == "rejected"


def test_new_with_description():
    req = ApprovalRequest.new("test", description="detailed description", risk_level="medium")
    assert req.description == "detailed description"
    assert req.risk_level == "medium"
