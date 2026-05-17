"""Tests for W149 — n8n CLI Commands."""
import pytest
from src.automation.n8n_cli import (
    cmd_n8n_list_templates,
    cmd_n8n_run_template,
    cmd_n8n_check_template,
    cmd_n8n_export_template,
)


def test_list_templates_count():
    result = cmd_n8n_list_templates()
    assert result["count"] == 4


def test_list_templates_structure():
    result = cmd_n8n_list_templates()
    for t in result["templates"]:
        assert "name" in t
        assert "trigger" in t
        assert "steps" in t


def test_run_template_success():
    result = cmd_n8n_run_template("daily_content_publish")
    assert result["success"] is True


def test_run_template_dry_run_default():
    result = cmd_n8n_run_template("daily_content_publish")
    assert result["registry_entry"]["export"]["dry_run"] is True


def test_run_template_not_found():
    result = cmd_n8n_run_template("nonexistent")
    assert "error" in result
    assert "available" in result


def test_check_template_passes():
    result = cmd_n8n_check_template("daily_content_publish")
    assert result["passed"] is True


def test_check_template_not_found():
    result = cmd_n8n_check_template("bad_template")
    assert "error" in result


def test_export_template_returns_json():
    result = cmd_n8n_export_template("lead_capture_webhook")
    assert "n8n_json" in result
    assert result["dry_run"] is True


def test_export_template_not_found():
    result = cmd_n8n_export_template("bad")
    assert "error" in result


def test_run_all_templates():
    for name in ["daily_content_publish", "mission_completed_hook", "lead_capture_webhook", "weekly_metrics_report"]:
        result = cmd_n8n_run_template(name)
        assert result["success"], f"Template {name} failed: {result.get('error')}"
