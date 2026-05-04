#!/usr/bin/env python3
"""
validate_skills.py — Validate all skill manifests against the JSON schema.

Usage:
    python scripts/validate_skills.py

Exit code 0 = all valid, 1 = any invalid or missing.
"""
import json
import os
import sys
import glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(BASE, "schemas", "skill_manifest.schema.json")
SKILLS_GLOB = os.path.join(BASE, "skills", "*", "manifest.json")

# Minimal JSON Schema draft-07 validator (no deps needed)
def _validate_schema(instance, schema, path="$"):
    """Recursive JSON Schema validator for draft-07 subset."""
    errors = []

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {json.dumps(instance)} not in enum {schema['enum']}")
        return errors

    if schema.get("type") == "object" and isinstance(instance, dict):
        if "required" in schema:
            for req in schema["required"]:
                if req not in instance:
                    errors.append(f"{path}: missing required field '{req}'")
        if "properties" in schema:
            for key, prop_schema in schema["properties"].items():
                if key in instance:
                    errors.extend(_validate_schema(instance[key], prop_schema, f"{path}.{key}"))

    if schema.get("type") == "array" and isinstance(instance, list):
        if "items" in schema:
            for i, item in enumerate(instance):
                errors.extend(_validate_schema(item, schema["items"], f"{path}[{i}]"))

    if schema.get("type") == "string" and isinstance(instance, str):
        if "pattern" in schema:
            import re
            if not re.match(schema["pattern"], instance):
                errors.append(f"{path}: '{instance}' does not match pattern {schema['pattern']}")
        if "enum" in schema and instance not in schema["enum"]:
            errors.append(f"{path}: '{instance}' not in enum {schema['enum']}")

    if schema.get("type") == "boolean" and not isinstance(instance, bool):
        errors.append(f"{path}: expected boolean, got {type(instance).__name__}")

    return errors


def _check_approval_rule(manifest):
    """Check that external_action/dangerous modes require approval."""
    errors = []
    if manifest.get("mode") in ("external_action", "dangerous"):
        if manifest.get("approval_required") is not True:
            errors.append(
                f"  mode={manifest['mode']} but approval_required={manifest.get('approval_required')} "
                "(must be true)"
            )
    return errors


def validate_all():
    if not os.path.exists(SCHEMA_PATH):
        print(f"ERROR: Schema not found at {SCHEMA_PATH}")
        return False

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    manifest_files = sorted(glob.glob(SKILLS_GLOB))
    if not manifest_files:
        print("ERROR: No manifests found matching skills/*/manifest.json")
        return False

    total_errors = 0
    total_warnings = 0
    valid_count = 0

    print(f"Validating {len(manifest_files)} manifests against schema...\n")

    for mf in manifest_files:
        rel = os.path.relpath(mf, BASE)
        with open(mf, "r", encoding="utf-8") as f:
            try:
                manifest = json.load(f)
            except json.JSONDecodeError as e:
                print(f"  {rel}: INVALID JSON — {e}")
                total_errors += 1
                continue

        errors = _validate_schema(manifest, schema)
        errors += _check_approval_rule(manifest)

        name = manifest.get("name", "?")
        if errors:
            print(f"  {rel} ({name}): FAIL")
            for e in errors:
                print(f"    - {e}")
            total_errors += len(errors)
        else:
            print(f"  {rel} ({name}): OK")
            valid_count += 1

    print(f"\nResults: {valid_count} valid, {total_errors} errors, {total_warnings} warnings")

    extras = len(manifest_files) - valid_count
    if extras:
        print(f"  ({extras} manifests have issues)")

    return total_errors == 0


if __name__ == "__main__":
    success = validate_all()
    sys.exit(0 if success else 1)
