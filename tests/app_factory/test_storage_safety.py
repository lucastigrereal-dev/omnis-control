"""Tests for storage safety module."""
from __future__ import annotations

import pytest

from src.app_factory.storage_safety import (
    StorageSafetyPolicy,
    SafetyViolation,
    StorageSafetyReport,
    matches_blocked_pattern,
    validate_path_safety,
    validate_command_safety,
    validate_dry_run_enforcement,
    audit_directory,
    NO_TOUCH_PATTERNS,
    DESTRUCTIVE_PATTERNS,
)


class TestStorageSafetyPolicy:
    def test_default_policy_requires_dry_run(self):
        policy = StorageSafetyPolicy()
        assert policy.require_dry_run is True

    def test_default_policy_blocks_env_files(self):
        policy = StorageSafetyPolicy()
        assert ".env" in policy.blocked_patterns

    def test_to_dict_from_dict_round_trip(self):
        policy = StorageSafetyPolicy()
        d = policy.to_dict()
        restored = StorageSafetyPolicy.from_dict(d)
        assert restored.require_dry_run == policy.require_dry_run
        assert restored.blocked_patterns == policy.blocked_patterns

    def test_custom_policy_can_allow_overwrite(self):
        policy = StorageSafetyPolicy(allow_overwrite=True)
        assert policy.allow_overwrite is True

    def test_custom_policy_can_disable_dry_run_requirement(self):
        policy = StorageSafetyPolicy(require_dry_run=False)
        assert policy.require_dry_run is False


class TestMatchesBlockedPattern:
    def test_env_file_is_blocked(self):
        assert matches_blocked_pattern(".env", NO_TOUCH_PATTERNS) is True

    def test_env_production_is_blocked(self):
        assert matches_blocked_pattern(".env.production", NO_TOUCH_PATTERNS) is True

    def test_normal_py_file_is_not_blocked(self):
        assert matches_blocked_pattern("src/main.py", NO_TOUCH_PATTERNS) is False

    def test_secrets_dir_is_blocked(self):
        assert matches_blocked_pattern("secrets/api_key.txt", NO_TOUCH_PATTERNS) is True

    def test_pem_file_is_blocked(self):
        assert matches_blocked_pattern("ssl/private.key", NO_TOUCH_PATTERNS) is True

    def test_exports_dir_is_blocked(self):
        assert matches_blocked_pattern("exports/report.md", NO_TOUCH_PATTERNS) is True

    def test_test_file_is_not_blocked(self):
        assert matches_blocked_pattern("tests/test_app.py", NO_TOUCH_PATTERNS) is False


class TestValidatePathSafety:
    def test_safe_path_no_violations(self):
        violations = validate_path_safety("src/app_factory/models.py")
        assert len(violations) == 0

    def test_env_path_produces_violation(self):
        violations = validate_path_safety(".env")
        assert len(violations) >= 1
        assert any(v.category == "no_touch_zone" for v in violations)


class TestValidateCommandSafety:
    def test_safe_command_no_violations(self):
        violations = validate_command_safety("python -m pytest tests/")
        assert len(violations) == 0

    def test_rm_rf_is_blocked(self):
        violations = validate_command_safety("rm -rf /tmp/build")
        assert len(violations) >= 1
        assert violations[0].category == "destructive_command"

    def test_git_reset_hard_is_blocked(self):
        violations = validate_command_safety("git reset --hard HEAD~1")
        assert len(violations) >= 1

    def test_git_clean_fd_is_blocked(self):
        violations = validate_command_safety("git clean -fd")
        assert len(violations) >= 1

    def test_docker_compose_down_is_blocked(self):
        violations = validate_command_safety("docker compose down --volumes")
        assert len(violations) >= 1


class TestValidateDryRunEnforcement:
    def test_dry_run_true_passes(self):
        violations = validate_dry_run_enforcement(dry_run=True)
        assert len(violations) == 0

    def test_dry_run_false_produces_violation(self):
        violations = validate_dry_run_enforcement(dry_run=False)
        assert len(violations) >= 1
        assert violations[0].category == "dry_run_disabled"

    def test_dry_run_false_allowed_when_policy_permits(self):
        policy = StorageSafetyPolicy(require_dry_run=False)
        violations = validate_dry_run_enforcement(dry_run=False, policy=policy)
        assert len(violations) == 0


class TestAuditDirectory:
    def test_audit_nonexistent_dir(self):
        report = audit_directory("/nonexistent/path/xyz")
        assert report.passed is False

    def test_audit_clean_directory(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("print('hello')")
        report = audit_directory(str(tmp_path))
        assert report.passed is True

    def test_audit_detects_env_file(self, tmp_path):
        (tmp_path / ".env").write_text("SECRET=abc")
        report = audit_directory(str(tmp_path))
        assert report.passed is False
        assert len(report.violations) >= 1

    def test_audit_no_scan_skips(self, tmp_path):
        (tmp_path / ".env").write_text("SECRET=abc")
        report = audit_directory(str(tmp_path), scan_files=False)
        assert report.passed is True
        assert report.scanned_files == 0


class TestSafetyViolation:
    def test_to_dict(self):
        v = SafetyViolation("blocked", "no_touch_zone", "/path/.env", "detail")
        d = v.to_dict()
        assert d["severity"] == "blocked"
        assert d["category"] == "no_touch_zone"


class TestStorageSafetyReport:
    def test_is_clean_when_passed_and_no_warnings(self):
        report = StorageSafetyReport(
            report_id="r1", target_path="/tmp", passed=True,
            violations=[], warnings=[], scanned_files=5,
            generated_at="2026-01-01T00:00:00Z", policy={},
        )
        assert report.is_clean is True

    def test_not_clean_when_not_passed(self):
        report = StorageSafetyReport(
            report_id="r1", target_path="/tmp", passed=False,
            violations=[{"severity": "blocked", "category": "test", "path": "/x", "detail": "x"}],
            warnings=[], scanned_files=5,
            generated_at="2026-01-01T00:00:00Z", policy={},
        )
        assert report.is_clean is False

    def test_critical_count(self):
        report = StorageSafetyReport(
            report_id="r1", target_path="/tmp", passed=False,
            violations=[{"k": "v1"}, {"k": "v2"}],
            warnings=[{"k": "w"}], scanned_files=3,
            generated_at="2026-01-01T00:00:00Z", policy={},
        )
        assert report.critical_count == 2
        assert report.warning_count == 1
