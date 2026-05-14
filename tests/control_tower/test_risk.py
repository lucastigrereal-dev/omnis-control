import pytest
from src.control_tower.risk import RiskClassifier
from src.control_tower.models import RiskLevel, ActionType


class TestRiskClassifier:
    @pytest.fixture
    def classifier(self):
        return RiskClassifier(dry_run=True)

    def test_local_read_is_low(self, classifier):
        risk = classifier.classify(
            action="read_status",
            is_external=False,
            is_destructive=False,
        )
        assert risk == RiskLevel.LOW

    def test_local_test_is_low(self, classifier):
        risk = classifier.classify(
            action="run_tests",
            is_external=False,
            is_destructive=False,
        )
        assert risk == RiskLevel.LOW

    def test_push_is_high(self, classifier):
        risk = classifier.classify(
            action="push_to_origin",
            is_external=True,
            is_destructive=False,
        )
        assert risk == RiskLevel.HIGH

    def test_merge_is_high(self, classifier):
        risk = classifier.classify(
            action="merge_branch",
            is_external=False,
            is_destructive=False,
        )
        assert risk == RiskLevel.HIGH

    def test_deploy_is_high(self, classifier):
        risk = classifier.classify(
            action="deploy_to_production",
            is_external=True,
            is_destructive=False,
        )
        assert risk == RiskLevel.HIGH

    def test_install_is_high(self, classifier):
        risk = classifier.classify(
            action="install_dependency",
            is_external=False,
            is_destructive=False,
        )
        assert risk == RiskLevel.HIGH

    def test_delete_is_critical(self, classifier):
        risk = classifier.classify(
            action="delete_records",
            is_external=False,
            is_destructive=True,
        )
        assert risk == RiskLevel.CRITICAL

    def test_external_destructive_is_critical(self, classifier):
        risk = classifier.classify(
            action="drop_table",
            is_external=True,
            is_destructive=True,
        )
        assert risk == RiskLevel.CRITICAL

    def test_health_check_external_is_low(self, classifier):
        risk = classifier.classify(
            action="health_check",
            is_external=True,
            is_destructive=False,
        )
        assert risk == RiskLevel.LOW

    def test_kratos_write_is_critical(self, classifier):
        risk = classifier.classify(
            action="modify_file",
            target_system="KRATOS",
            is_external=False,
            is_destructive=True,
        )
        assert risk == RiskLevel.CRITICAL

    def test_kratos_path_touched_is_blocked(self, classifier):
        risk = classifier.classify(
            action="read_report",
            paths_touched=[".kratos/war-room/canon/test.md"],
            is_external=False,
            is_destructive=False,
        )
        assert risk == RiskLevel.CRITICAL

    def test_external_api_write_is_high(self, classifier):
        risk = classifier.classify(
            action="write_post",
            is_external=True,
            is_destructive=False,
        )
        assert risk == RiskLevel.HIGH

    def test_configure_is_medium(self, classifier):
        risk = classifier.classify(
            action="configure_settings",
            is_external=False,
            is_destructive=False,
        )
        assert risk == RiskLevel.MEDIUM

    def test_recommended_action_low(self, classifier):
        atype = classifier.recommended_action_type(RiskLevel.LOW)
        assert atype == ActionType.OBSERVE

    def test_recommended_action_medium(self, classifier):
        atype = classifier.recommended_action_type(RiskLevel.MEDIUM)
        assert atype == ActionType.DRY_RUN

    def test_recommended_action_high(self, classifier):
        atype = classifier.recommended_action_type(RiskLevel.HIGH)
        assert atype == ActionType.EXECUTE_WITH_APPROVAL

    def test_recommended_action_critical(self, classifier):
        atype = classifier.recommended_action_type(RiskLevel.CRITICAL)
        assert atype == ActionType.BLOCK
