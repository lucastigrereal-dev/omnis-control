"""P45: ApprovalRuntime integration — store + tokens + policy for HIGH/MEDIUM orders."""

import tempfile
from pathlib import Path
import pytest

from src.approval_runtime.models import (
    ApprovalRequest,
    ApprovalStatus,
    RiskLevel,
)
from src.approval_runtime.policy import ApprovalPolicy
from src.approval_runtime.store import ApprovalStore
from src.approval_runtime.tokens import TokenVerifier
from src.approval_runtime.errors import AlreadyDecidedError, InvalidTokenError


class TestApprovalRequired:
    def test_full_approval_lifecycle(self):
        """Request → evaluate → store → approve → verify decision."""
        policy = ApprovalPolicy(dry_run=True)
        store = ApprovalStore(dry_run=True)

        req = ApprovalRequest(
            risk=RiskLevel.HIGH,
            is_destructive=False,
            source_system="test_integration",
            reason="Deploy to staging",
        )
        store.save_request(req)

        decision = policy.evaluate(req)
        assert decision.status == ApprovalStatus.PENDING
        assert decision.requires_human is True

        approved = store.approve(req.request_id, approved_by="operator")
        assert approved.status == ApprovalStatus.APPROVED
        assert approved.decided_by == "operator"

    def test_reject_flow(self):
        """Request can be rejected with reason."""
        store = ApprovalStore(dry_run=True)

        req = ApprovalRequest(
            risk=RiskLevel.MEDIUM,
            is_destructive=True,
            reason="Database migration",
        )
        store.save_request(req)

        rejected = store.reject(req.request_id, "Too risky", rejected_by="operator")
        assert rejected.status == ApprovalStatus.REJECTED
        assert rejected.message == "Too risky"

    def test_cannot_approve_twice(self):
        """AlreadyDecidedError raised on duplicate approve/reject."""
        store = ApprovalStore(dry_run=True)
        req = ApprovalRequest(risk=RiskLevel.LOW, is_destructive=True)
        store.save_request(req)
        store.approve(req.request_id)

        with pytest.raises(AlreadyDecidedError):
            store.approve(req.request_id)

    def test_token_generation_and_verification(self):
        """TokenVerifier generates, verifies, and invalidates single-use tokens."""
        verifier = TokenVerifier()
        token = verifier.generate_token("req_1")
        assert token.startswith("omnis_approval_")

        assert verifier.verify("req_1", token) is True

        with pytest.raises(InvalidTokenError):
            verifier.verify("req_1", token)

    def test_token_revocation(self):
        """Revoked token cannot be verified."""
        verifier = TokenVerifier()
        token = verifier.generate_token("req_2")
        verifier.revoke("req_2")

        with pytest.raises(InvalidTokenError):
            verifier.verify("req_2", token)

    def test_token_wrong_request_id(self):
        """Token from one request cannot verify another."""
        verifier = TokenVerifier()
        verifier.generate_token("req_a")

        with pytest.raises(InvalidTokenError):
            verifier.verify("req_b", "omnis_approval_fake")

    def test_policy_all_risk_levels(self):
        """Every risk level produces expected requires_human behavior."""
        policy = ApprovalPolicy(dry_run=True)
        cases = [
            (RiskLevel.LOW, False, False),
            (RiskLevel.LOW, True, True),
            (RiskLevel.MEDIUM, False, True),
            (RiskLevel.MEDIUM, True, True),
            (RiskLevel.HIGH, False, True),
            (RiskLevel.CRITICAL, False, True),
        ]
        for risk, is_dest, expects_human in cases:
            req = ApprovalRequest(risk=risk, is_destructive=is_dest)
            decision = policy.evaluate(req)
            assert decision.requires_human == expects_human, (
                f"Failed for {risk.value} destructive={is_dest}"
            )

    def test_store_persistence_roundtrip(self):
        """Store persists to file and loads back correctly."""
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "approvals.json"
            store = ApprovalStore(str(store_path), dry_run=False)

            req = ApprovalRequest(
                risk=RiskLevel.HIGH,
                is_destructive=False,
                reason="Persist test",
            )
            store.save_request(req)
            store.approve(req.request_id, approved_by="operator")

            store2 = ApprovalStore(str(store_path), dry_run=False)
            store2.load()
            decision = store2.get_decision(req.request_id)
            assert decision is not None
            assert decision.status == ApprovalStatus.APPROVED
            assert decision.decided_by == "operator"
