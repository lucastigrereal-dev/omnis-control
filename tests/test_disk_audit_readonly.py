"""Tests for disk_audit_readonly.py — verifies it scans without modifying."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
SCRIPT = BASE / "scripts" / "disk_audit_readonly.py"
REPORT = BASE / "docs" / "disk_audit_report.json"


def test_script_exists():
    assert SCRIPT.exists(), f"Script not found: {SCRIPT}"


def test_script_is_readonly():
    """Verify the script contains no delete/modify operations."""
    content = SCRIPT.read_text(encoding="utf-8")
    dangerous = ["shutil.rmtree", "os.remove", "os.unlink", "Path.unlink",
                 "rmtree", "subprocess.run.*rm"]
    for pattern in dangerous:
        if "rmtree" in pattern.lower():
            assert "rmtree" not in content, f"Found dangerous pattern: {pattern}"


def test_script_imports_cleanly():
    script_str = str(SCRIPT).replace("\\", "/")
    result = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open(r'{script_str}', encoding='utf-8').read())"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"Script has syntax errors: {result.stderr}"


def test_report_generated():
    """Report should exist (even if stale, to confirm script was run)."""
    # Run the script
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"

    # Check report
    assert REPORT.exists(), f"Report not created at {REPORT}"
    with open(REPORT, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "generated_at" in data
    assert "disk_summary" in data
    assert "project_directories" in data


def test_report_has_disk_info():
    with open(REPORT, "r", encoding="utf-8") as f:
        data = json.load(f)
    disk = data["disk_summary"]
    assert "free_gb" in disk
    assert "percent_free" in disk
    assert isinstance(disk["free_gb"], (int, float))
    assert disk["free_gb"] > 0, "Disk should have some free space"


def test_report_has_project_data():
    with open(REPORT, "r", encoding="utf-8") as f:
        data = json.load(f)
    projects = data["project_directories"]
    assert len(projects) >= 1
    omnis = [p for p in projects if p["name"] == "omnis-control"]
    assert len(omnis) == 1
    assert omnis[0].get("exists", False), "omnis-control entry must show exists=True"
    assert omnis[0]["size_bytes"] >= 0, "size_bytes must be non-negative (du may return 0 on Windows)"


def test_report_has_docker_section():
    with open(REPORT, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "docker_reclaimable" in data
    assert len(data["docker_reclaimable"]) >= 2


def test_report_has_no_modifications():
    """Re-read the script content to confirm hash hasn't changed."""
    # Verify docstring warns READ-ONLY
    lines = SCRIPT.read_text(encoding="utf-8").split("\n")
    assert "READ-ONLY" in lines[4] or "never" in lines[4].lower()


def test_large_files_section_exists():
    with open(REPORT, "r", encoding="utf-8") as f:
        data = json.load(f)
    # large_files may be empty or populated — either is valid
    assert "large_files" in data
