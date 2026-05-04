"""Tests for n8n workflow spec files."""
import json
import re
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = BASE / "workflows" / "n8n"
DOC_DIR = BASE / "docs" / "workflows"

SECRET_PATTERNS = [
    r"(?i)sk-[a-zA-Z0-9]{20,}",        # API keys (sk-...)
    r"(?i)secret.*=.*['\"][a-zA-Z0-9]{16,}",
    r"(?i)token.*=.*['\"][a-zA-Z0-9]{16,}",
    r"META_APP_SECRET",
    r"META_APP_ID",
    r"OPENAI_API_KEY",
    r"SUPABASE_KEY",
    r"NOTION_TOKEN",
]


def _find_json_files():
    return sorted(WORKFLOW_DIR.glob("*.json"))


def _check_secrets(content: str) -> list:
    matches = []
    for pat in SECRET_PATTERNS:
        found = re.findall(pat, content)
        if found:
            matches.append(f"Pattern {pat} matched: {found}")
    return matches


def test_workflow_json_exists():
    files = _find_json_files()
    assert len(files) >= 1, f"No JSON workflow files found in {WORKFLOW_DIR}"


def test_workflow_json_valid():
    for wf in _find_json_files():
        with open(wf, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "nodes" in data, f"{wf.name}: missing 'nodes'"
        assert isinstance(data["nodes"], list), f"{wf.name}: nodes not a list"
        assert len(data["nodes"]) > 0, f"{wf.name}: empty nodes"


def test_workflow_has_connections():
    for wf in _find_json_files():
        with open(wf, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "connections" in data, f"{wf.name}: missing 'connections'"


def test_no_real_secrets_in_json():
    for wf in _find_json_files():
        content = wf.read_text(encoding="utf-8")
        secrets = _check_secrets(content)
        assert len(secrets) == 0, f"{wf.name}: secrets found:\n" + "\n".join(secrets)


def test_no_redacted_placeholders():
    """Ensure no [REDACTED-REAL] from the redacted report leaks into workflow specs."""
    for wf in _find_json_files():
        content = wf.read_text(encoding="utf-8")
        assert "[REDACTED" not in content, f"{wf.name}: contains [REDACTED...] placeholder"


def test_has_manual_trigger():
    for wf in _find_json_files():
        with open(wf, "r", encoding="utf-8") as f:
            data = json.load(f)
        node_types = [n.get("type", "") for n in data["nodes"]]
        assert "n8n-nodes-base.manualTrigger" in node_types, (
            f"{wf.name}: missing Manual Trigger node"
        )


def test_has_validation_node():
    for wf in _find_json_files():
        with open(wf, "r", encoding="utf-8") as f:
            data = json.load(f)
        names = [n.get("name", "").lower() for n in data["nodes"]]
        assert any("valid" in name for name in names), (
            f"{wf.name}: no validation node found"
        )


def test_has_export_node():
    for wf in _find_json_files():
        with open(wf, "r", encoding="utf-8") as f:
            data = json.load(f)
        names = [n.get("name", "").lower() for n in data["nodes"]]
        assert any("export" in name for name in names), (
            f"{wf.name}: no export node found"
        )


def test_has_notification_node():
    for wf in _find_json_files():
        with open(wf, "r", encoding="utf-8") as f:
            data = json.load(f)
        names = [n.get("name", "").lower() for n in data["nodes"]]
        assert any("notif" in name for name in names), (
            f"{wf.name}: no notification node found"
        )


def test_documentation_exists():
    doc_file = DOC_DIR / "N8N_APPROVAL_TO_EXPORT.md"
    assert doc_file.exists(), f"Documentation not found at {doc_file}"
    content = doc_file.read_text(encoding="utf-8")
    assert "## Objetivo" in content
    assert "## Como Importar" in content
    assert "## Riscos" in content
    assert "## Rollback" in content


def test_doc_no_secrets():
    doc_file = DOC_DIR / "N8N_APPROVAL_TO_EXPORT.md"
    if doc_file.exists():
        content = doc_file.read_text(encoding="utf-8")
        secrets = _check_secrets(content)
        assert len(secrets) == 0, "Secrets found in doc:\n" + "\n".join(secrets)
