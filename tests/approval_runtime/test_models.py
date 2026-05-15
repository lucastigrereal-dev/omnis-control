from src.approval_runtime.models import (
    ApprovalRequest,
    ApprovalDecision,
    ApprovalStatus,
    RiskLevel,
)


class TestRiskLevel:
    def test_values(self):
        assert RiskLevel.LOW == "LOW"
        assert RiskLevel.CRITICAL == "CRITICAL"
        assert RiskLevel("MEDIUM") == RiskLevel.MEDIUM


class TestApprovalStatus:
    def test_values(self):
        assert ApprovalStatus.PENDING == "PENDING"
        assert ApprovalStatus.AUTO_APPROVED == "AUTO_APPROVED"
        assert ApprovalStatus.APPROVED == "APPROVED"
        assert ApprovalStatus.REJECTED == "REJECTED"


class TestApprovalRequest:
    def test_defaults(self):
        req = ApprovalRequest()
        assert req.request_id.startswith("apr_")
        assert req.risk == RiskLevel.LOW
        assert req.is_destructive is False
        assert req.dry_run_possible is True

    def test_to_dict_round_trip(self):
        req = ApprovalRequest(
            action="write_report",
            target="war-room/reports/",
            risk=RiskLevel.MEDIUM,
            is_destructive=False,
            reason="Automated report generation",
        )
        data = req.to_dict()
        assert data["action"] == "write_report"
        assert data["risk"] == "MEDIUM"

    def test_from_dict(self):
        req = ApprovalRequest.from_dict({
            "request_id": "apr_test",
            "action": "test",
            "risk": "HIGH",
            "is_destructive": True,
        })
        assert req.request_id == "apr_test"
        assert req.risk == RiskLevel.HIGH
        assert req.is_destructive is True


class TestApprovalDecision:
    def test_defaults(self):
        dec = ApprovalDecision()
        assert dec.decision_id.startswith("apd_")
        assert dec.status == ApprovalStatus.PENDING
        assert dec.requires_human is False

    def test_is_blocked(self):
        assert ApprovalDecision(status=ApprovalStatus.REJECTED).is_blocked is True
        assert ApprovalDecision(status=ApprovalStatus.PENDING).is_blocked is False

    def test_is_approved(self):
        assert ApprovalDecision(status=ApprovalStatus.AUTO_APPROVED).is_approved is True
        assert ApprovalDecision(status=ApprovalStatus.APPROVED).is_approved is True
        assert ApprovalDecision(status=ApprovalStatus.PENDING).is_approved is False

    def test_to_dict(self):
        dec = ApprovalDecision(
            request_id="apr_x",
            status=ApprovalStatus.APPROVED,
            requires_human=True,
            message="ok",
        )
        data = dec.to_dict()
        assert data["request_id"] == "apr_x"
        assert data["status"] == "APPROVED"
