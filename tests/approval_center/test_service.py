"""Tests for approval center service."""
import pytest
from src.approval_center import service as svc_mod
from src.approval_center import store as store_mod
from src.approval_center.models import APPROVAL_STATUS_APPROVED, APPROVAL_STATUS_REJECTED
from src.approval_center.errors import ApprovalNotFoundError, ApprovalAlreadyResolvedError


def test_request_approval_creates_pending(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "approvals.jsonl")
    req = svc_mod.request_approval("publish reels", capability_id="campaign_package")
    assert req.request_id.startswith("req_")
    assert req.status == "pending"


def test_approve_changes_status(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "approvals.jsonl")
    req = svc_mod.request_approval("test approve", approvals_log=tmp_path / "approvals.jsonl")
    approved = svc_mod.approve(req.request_id, note="cleared", approvals_log=tmp_path / "approvals.jsonl")
    assert approved.status == APPROVAL_STATUS_APPROVED
    assert approved.resolution_note == "cleared"


def test_reject_changes_status(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "approvals.jsonl")
    req = svc_mod.request_approval("test reject", approvals_log=tmp_path / "approvals.jsonl")
    rejected = svc_mod.reject(req.request_id, note="too risky", approvals_log=tmp_path / "approvals.jsonl")
    assert rejected.status == APPROVAL_STATUS_REJECTED
    assert rejected.resolution_note == "too risky"


def test_approve_not_found_raises(tmp_path):
    with pytest.raises(ApprovalNotFoundError):
        svc_mod.approve("req_ghost", approvals_log=tmp_path / "approvals.jsonl")


def test_reject_not_found_raises(tmp_path):
    with pytest.raises(ApprovalNotFoundError):
        svc_mod.reject("req_ghost", approvals_log=tmp_path / "approvals.jsonl")


def test_double_approve_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "approvals.jsonl")
    req = svc_mod.request_approval("double", approvals_log=tmp_path / "approvals.jsonl")
    svc_mod.approve(req.request_id, approvals_log=tmp_path / "approvals.jsonl")
    with pytest.raises(ApprovalAlreadyResolvedError):
        svc_mod.approve(req.request_id, approvals_log=tmp_path / "approvals.jsonl")


def test_reject_already_approved_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "approvals.jsonl")
    req = svc_mod.request_approval("approve then reject", approvals_log=tmp_path / "approvals.jsonl")
    svc_mod.approve(req.request_id, approvals_log=tmp_path / "approvals.jsonl")
    with pytest.raises(ApprovalAlreadyResolvedError):
        svc_mod.reject(req.request_id, approvals_log=tmp_path / "approvals.jsonl")
