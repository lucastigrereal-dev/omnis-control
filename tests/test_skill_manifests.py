"""Tests for skill manifest validation."""
import json
import os
import shutil
import tempfile
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE / "schemas" / "skill_manifest.schema.json"
SKILLS_DIR = BASE / "skills"
VALIDATOR = BASE / "scripts" / "validate_skills.py"

# Import the validator module
sys.path.insert(0, str(BASE / "scripts"))
import importlib.util
spec = importlib.util.spec_from_file_location("validate_skills", VALIDATOR)
vmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vmod)


def test_schema_exists():
    assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"


def test_schema_loads():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    assert schema["title"] == "Skill Manifest"
    assert "required" in schema
    assert "allOf" in schema  # approval_required rule


def test_at_least_one_manifest():
    manifests = list(SKILLS_DIR.glob("*/manifest.json"))
    assert len(manifests) >= 1, f"No manifests found in {SKILLS_DIR}"


def test_all_manifests_pass_validator():
    """Run the full validator against all real manifests."""
    assert vmod.validate_all(), "One or more manifests failed validation"


def test_approval_rule_enforced():
    """external_action mode must have approval_required=true."""
    test_dir = Path(tempfile.mkdtemp())
    try:
        manifest = {
            "name": "test_risk_skill",
            "version": "1.0.0",
            "description": "test",
            "status": "active",
            "risk_level": "high",
            "mode": "external_action",
            "owner": "test",
            "tags": ["test"],
            "inputs_schema": {"type": "object", "properties": {}, "required": []},
            "outputs_schema": {"type": "object", "properties": {}, "required": []},
            "approval_required": False,  # Violation!
            "lifecycle": "experimental",
            "deprecated": False,
            "replacement": "",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z"
        }
        errors = vmod._check_approval_rule(manifest)
        assert len(errors) > 0, "Should have caught missing approval for external_action"

        # Fix
        manifest["approval_required"] = True
        errors = vmod._check_approval_rule(manifest)
        assert len(errors) == 0, "Should pass after fixing approval_required"
    finally:
        shutil.rmtree(test_dir)


def test_invalid_manifest_detected(tmp_path):
    """Validator should reject an invalid manifest."""
    bad = tmp_path / "bad_manifest.json"
    bad.write_text(json.dumps({"name": 123}), encoding="utf-8")  # name should be string

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    with open(bad, "r", encoding="utf-8") as f:
        instance = json.load(f)
    errors = vmod._validate_schema(instance, schema)
    assert len(errors) > 0, "Should have detected invalid manifest"


def test_manifest_has_inputs_schema():
    manifests = list(SKILLS_DIR.glob("*/manifest.json"))
    for mf in manifests:
        with open(mf, "r", encoding="utf-8") as f:
            m = json.load(f)
        assert "inputs_schema" in m, f"{mf.name} missing inputs_schema"
        assert "properties" in m["inputs_schema"], f"{mf.name} inputs_schema missing properties"


def test_manifest_has_outputs_schema():
    manifests = list(SKILLS_DIR.glob("*/manifest.json"))
    for mf in manifests:
        with open(mf, "r", encoding="utf-8") as f:
            m = json.load(f)
        assert "outputs_schema" in m, f"{mf.name} missing outputs_schema"
        assert "properties" in m["outputs_schema"], f"{mf.name} outputs_schema missing properties"


def test_status_enum_valid():
    valid = {"draft", "proposed", "active", "deprecated", "blocked"}
    manifests = list(SKILLS_DIR.glob("*/manifest.json"))
    for mf in manifests:
        with open(mf, "r", encoding="utf-8") as f:
            m = json.load(f)
        assert m["status"] in valid, f"{mf.name}: invalid status '{m['status']}'"


def test_lifecycle_enum_valid():
    valid = {"experimental", "validated", "production", "deprecated"}
    manifests = list(SKILLS_DIR.glob("*/manifest.json"))
    for mf in manifests:
        with open(mf, "r", encoding="utf-8") as f:
            m = json.load(f)
        assert m["lifecycle"] in valid, f"{mf.name}: invalid lifecycle '{m['lifecycle']}'"


def test_risk_level_enum():
    valid = {"low", "medium", "high"}
    manifests = list(SKILLS_DIR.glob("*/manifest.json"))
    for mf in manifests:
        with open(mf, "r", encoding="utf-8") as f:
            m = json.load(f)
        assert m["risk_level"] in valid, f"{mf.name}: invalid risk_level '{m['risk_level']}'"


def test_mode_enum():
    valid = {"read_only", "draft_only", "local_write", "external_action", "dangerous"}
    manifests = list(SKILLS_DIR.glob("*/manifest.json"))
    for mf in manifests:
        with open(mf, "r", encoding="utf-8") as f:
            m = json.load(f)
        assert m["mode"] in valid, f"{mf.name}: invalid mode '{m['mode']}'"
