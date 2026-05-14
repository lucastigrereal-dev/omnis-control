"""Tests for P21 Memory Intelligence safety module."""
from __future__ import annotations

import pytest

from src.memory_intel.safety import sanitize_context_text, validate_safety_rules
from src.memory_intel.models import MAX_ASSEMBLED_TEXT_CHARS


# ── sanitize_context_text ───────────────────────────────────────────────────

class TestSanitizeContextText:
    def test_short_text_unchanged(self):
        text = "This is a short text"
        result = sanitize_context_text(text)
        assert result == text

    def test_empty_string(self):
        result = sanitize_context_text("")
        assert result == ""

    def test_truncates_long_text(self):
        text = "x" * (MAX_ASSEMBLED_TEXT_CHARS + 100)
        result = sanitize_context_text(text)
        assert len(result) <= MAX_ASSEMBLED_TEXT_CHARS

    def test_truncated_text_ends_with_ellipsis(self):
        text = "x" * (MAX_ASSEMBLED_TEXT_CHARS + 100)
        result = sanitize_context_text(text)
        assert result.endswith("...")

    def test_removes_code_blocks(self):
        text = "Hello ```code block``` world"
        result = sanitize_context_text(text)
        assert "```" not in result
        assert "Hello code block world" in result

    def test_respects_custom_max_chars(self):
        text = "x" * 100
        result = sanitize_context_text(text, max_chars=50)
        assert len(result) == 50
        assert result.endswith("...")

    def test_exact_max_length_unchanged(self):
        text = "x" * MAX_ASSEMBLED_TEXT_CHARS
        result = sanitize_context_text(text)
        assert len(result) == MAX_ASSEMBLED_TEXT_CHARS

    def test_one_below_max_unchanged(self):
        text = "x" * (MAX_ASSEMBLED_TEXT_CHARS - 1)
        result = sanitize_context_text(text)
        assert len(result) == MAX_ASSEMBLED_TEXT_CHARS - 1
        assert not result.endswith("...")


# ── validate_safety_rules ───────────────────────────────────────────────────

class TestValidateSafetyRules:
    def test_valid_config_passes(self):
        result = validate_safety_rules(
            is_dry_run=True,
            requires_approval=True,
            action="upsert",
            record_count=3,
            max_records=5,
        )
        assert result["valid"] is True
        assert result["violations"] == []

    def test_non_dry_run_violation(self):
        result = validate_safety_rules(
            is_dry_run=False,
            requires_approval=True,
            action="upsert",
            record_count=1,
            max_records=5,
        )
        assert result["valid"] is False
        assert any("dry_run" in v for v in result["violations"])

    def test_no_approval_violation(self):
        result = validate_safety_rules(
            is_dry_run=True,
            requires_approval=False,
            action="upsert",
            record_count=1,
            max_records=5,
        )
        assert result["valid"] is False
        assert any("approval" in v for v in result["violations"])

    def test_delete_action_blocked(self):
        result = validate_safety_rules(
            is_dry_run=True,
            requires_approval=True,
            action="delete",
            record_count=1,
            max_records=5,
        )
        assert result["valid"] is False
        assert any("DELETE" in v for v in result["violations"])

    def test_record_count_exceeded(self):
        result = validate_safety_rules(
            is_dry_run=True,
            requires_approval=True,
            action="upsert",
            record_count=10,
            max_records=5,
        )
        assert result["valid"] is False
        assert any("memory_pollution" in v for v in result["violations"])

    def test_multiple_violations(self):
        result = validate_safety_rules(
            is_dry_run=False,
            requires_approval=False,
            action="delete",
            record_count=10,
            max_records=2,
        )
        assert result["valid"] is False
        assert len(result["violations"]) >= 3

    def test_rules_checked_present(self):
        result = validate_safety_rules(
            is_dry_run=True,
            requires_approval=True,
            action="upsert",
            record_count=1,
            max_records=5,
        )
        assert "rules_checked" in result
        assert len(result["rules_checked"]) == 5

    def test_boundary_record_count(self):
        result = validate_safety_rules(
            is_dry_run=True,
            requires_approval=True,
            action="upsert",
            record_count=5,
            max_records=5,
        )
        assert result["valid"] is True
