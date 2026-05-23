"""Tests for staged secret scan helper used by pre-commit hook."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "secret_scan_staged.py"
SPEC = importlib.util.spec_from_file_location("secret_scan_staged", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_scan_text_flags_hardcoded_password_assignment():
    text = 'db_password = "postgres"\n'
    findings = MODULE.scan_text("src/example.py", text)
    assert len(findings) == 1
    assert findings[0].reason == "hardcoded credential assignment"


def test_scan_text_flags_dsn_fragment():
    text = 'conn = psycopg2.connect("host=localhost password=postgres dbname=akasha")\n'
    findings = MODULE.scan_text("src/example.py", text)
    assert len(findings) == 1
    assert findings[0].reason == "hardcoded DSN credential fragment"


def test_scan_text_allows_env_based_assignment():
    text = 'api_key = os.getenv("OPENAI_API_KEY", "")\n'
    findings = MODULE.scan_text("src/example.py", text)
    assert findings == []


def test_scan_text_ignores_comments():
    text = "# password='example-only'\n"
    findings = MODULE.scan_text("src/example.py", text)
    assert findings == []
