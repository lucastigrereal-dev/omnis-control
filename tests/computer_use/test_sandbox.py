"""Tests for SecuritySandbox — safety guardrails."""
from __future__ import annotations

import pytest

from src.computer_use.sandbox import (
    SecuritySandbox,
    SandboxViolation,
    BLOCKED_DOMAINS,
    BLOCKED_ACTIONS,
    ALLOWED_PATHS,
)


class TestSandboxViolation:
    def test_violation_str(self):
        v = SandboxViolation(rule="blocked_domain", detail="test")
        assert "SANDBOX VIOLATION" in str(v)
        assert "blocked_domain" in str(v)

    def test_violation_to_dict(self):
        v = SandboxViolation(rule="blocked_domain", detail="test")
        d = v.to_dict()
        assert d["rule"] == "blocked_domain"
        assert d["detail"] == "test"


class TestSecuritySandbox:
    def test_validate_url_allows_instagram(self):
        sb = SecuritySandbox()
        assert sb.validate_url("https://www.instagram.com/explore/tags/viagem/") is True

    def test_validate_url_blocks_bank(self):
        sb = SecuritySandbox(strict=False)
        assert sb.validate_url("https://www.banco.com") is False

    def test_validate_url_blocks_bank_strict(self):
        sb = SecuritySandbox(strict=True)
        with pytest.raises(SandboxViolation) as exc:
            sb.validate_url("https://www.banco.com.br")
        assert "blocked_domain" in str(exc.value)

    def test_validate_url_blocks_email_strict(self):
        sb = SecuritySandbox(strict=True)
        with pytest.raises(SandboxViolation):
            sb.validate_url("https://gmail.com")

    def test_validate_url_allows_localhost_characterization(self):
        """Caracterização de risco: localhost não é bloqueado na regra atual."""
        sb = SecuritySandbox()
        assert sb.validate_url("http://localhost:8000/internal") is True

    def test_validate_url_allows_private_ip_characterization(self):
        """Caracterização de risco: IP privado não é bloqueado na regra atual."""
        sb = SecuritySandbox()
        assert sb.validate_url("http://10.0.0.5/admin") is True

    def test_validate_url_allows_file_scheme_characterization(self):
        """Caracterização de risco: esquema file:// não é bloqueado na regra atual."""
        sb = SecuritySandbox()
        assert sb.validate_url("file:///C:/Users/lucas/secret.txt") is True

    def test_validate_action_allows_scrape(self):
        sb = SecuritySandbox()
        assert sb.validate_action("scrape_profile") is True

    def test_validate_action_blocks_delete(self):
        sb = SecuritySandbox(strict=False)
        assert sb.validate_action("delete_all_posts") is False

    def test_validate_action_blocks_delete_strict(self):
        sb = SecuritySandbox(strict=True)
        with pytest.raises(SandboxViolation):
            sb.validate_action("delete_all_posts")

    def test_validate_path_allows_omnis(self):
        sb = SecuritySandbox()
        assert sb.validate_path("C:\\Users\\lucas\\omnis-control\\exports\\test.txt") is True

    def test_validate_path_blocks_unknown(self):
        sb = SecuritySandbox(strict=False)
        assert sb.validate_path("C:\\Windows\\System32\\evil.exe") is False

    def test_validate_path_blocks_unknown_strict(self):
        sb = SecuritySandbox(strict=True)
        with pytest.raises(SandboxViolation):
            sb.validate_path("C:\\Windows\\System32\\evil.exe")

    def test_preflight_all_clear(self):
        sb = SecuritySandbox()
        assert sb.preflight(
            url="https://instagram.com",
            action="search_instagram",
            path="C:\\Users\\lucas\\omnis-control\\output\\test.png",
        ) is True

    def test_preflight_blocks_bad_url(self):
        sb = SecuritySandbox(strict=False)
        assert sb.preflight(url="https://banco.com") is False

    def test_preflight_blocks_bad_action(self):
        sb = SecuritySandbox(strict=False)
        assert sb.preflight(action="delete") is False

    def test_record_allowed(self):
        sb = SecuritySandbox()
        sb.record_allowed("search_instagram", "viagem")
        assert len(sb.allowed_actions) == 1
        assert sb.allowed_actions[0]["action"] == "search_instagram"

    def test_is_clean_initial(self):
        sb = SecuritySandbox()
        assert sb.is_clean is True

    def test_is_clean_after_violation(self):
        sb = SecuritySandbox(strict=False)
        sb.validate_url("https://banco.com")
        assert sb.is_clean is False

    def test_summary(self):
        sb = SecuritySandbox()
        sb.record_allowed("search", "test")
        summary = sb.summary
        assert "1 allowed" in summary
        assert "0 violations" in summary

    def test_all_blocked_domains(self):
        for domain in BLOCKED_DOMAINS[:3]:
            sb = SecuritySandbox(strict=False)
            assert sb.validate_url(f"https://{domain}.com") is False

    def test_all_blocked_actions(self):
        for action in BLOCKED_ACTIONS[:3]:
            sb = SecuritySandbox(strict=False)
            assert sb.validate_action(action) is False

    def test_allowed_paths(self):
        for path in ALLOWED_PATHS[:3]:
            sb = SecuritySandbox()
            assert sb.validate_path(path) is True
