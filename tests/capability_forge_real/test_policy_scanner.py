"""Tests for P22 Policy Scanner."""
from __future__ import annotations

import pytest
from pathlib import Path

from src.capability_forge_real.policy_scanner import scan_code, scan_file


# ── scan_code ───────────────────────────────────────────────────────────────

class TestScanCode:
    def test_clean_code_passes(self):
        code = '''"""A clean module."""
def hello():
    return "hello world"
'''
        result = scan_code(code)
        assert result["passed"] is True
        assert result["violations"] == []

    def test_code_with_eval_fails(self):
        code = 'x = eval("1+1")'
        result = scan_code(code)
        assert result["passed"] is False
        assert any("eval" in str(v) for v in result["violations"])

    def test_code_with_exec_fails(self):
        code = 'exec("x=1")'
        result = scan_code(code)
        assert result["passed"] is False

    def test_code_with_subprocess_fails(self):
        code = 'import subprocess; subprocess.run(["ls"])'
        result = scan_code(code)
        assert result["passed"] is False

    def test_code_with_requests_fails(self):
        code = 'import requests; requests.get("http://example.com")'
        result = scan_code(code)
        assert result["passed"] is False

    def test_code_with_os_system_fails(self):
        code = 'import os; os.system("ls")'
        result = scan_code(code)
        assert result["passed"] is False

    def test_code_with_forbidden_import_fails(self):
        code = 'import socket'
        result = scan_code(code)
        assert result["passed"] is False

    def test_violations_have_required_fields(self):
        code = 'eval("1+1")'
        result = scan_code(code)
        for v in result["violations"]:
            assert "line" in v
            assert "pattern" in v
            assert "description" in v


# ── scan_file ───────────────────────────────────────────────────────────────

class TestScanFile:
    def test_clean_file_passes(self, tmp_path):
        f = tmp_path / "clean.py"
        f.write_text('def hello():\n    return "hello"\n')
        result = scan_file(f)
        assert result["passed"] is True

    def test_dirty_file_fails(self, tmp_path):
        f = tmp_path / "dirty.py"
        f.write_text('eval("1+1")\n')
        result = scan_file(f)
        assert result["passed"] is False

    def test_nonexistent_file(self, tmp_path):
        f = tmp_path / "nonexistent.py"
        result = scan_file(f)
        assert result["passed"] is False
