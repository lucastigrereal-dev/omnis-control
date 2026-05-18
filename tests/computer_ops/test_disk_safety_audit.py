"""Tests for DiskSafetyAuditor — read-only disk safety audit."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.computer_ops.disk_safety_audit import (
    ALL_CATEGORIES,
    CAT_DO_NOT_TOUCH,
    CAT_NEEDS_REVIEW,
    CAT_SAFE_TO_DELETE,
    DiskSafetyAuditor,
    PROTECTED_NAMES,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_tree(tmp_path: Path) -> Path:
    """Create a minimal fake project tree."""
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "some-pkg").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "mod.cpython-312.pyc").write_bytes(b"x" * 100)
    (tmp_path / ".cache").mkdir()
    big_log = tmp_path / "app.log"
    big_log.write_bytes(b"x" * 2_000_000)  # 2 MB
    small_log = tmp_path / "tiny.log"
    small_log.write_bytes(b"x" * 500)  # < 1 MB
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("# code", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    exports = tmp_path / "exports"
    exports.mkdir()
    (exports / "bundle.zip").write_bytes(b"PK" + b"x" * 1000)
    return tmp_path


@pytest.fixture()
def auditor() -> DiskSafetyAuditor:
    return DiskSafetyAuditor()


# ── scan() tests ──────────────────────────────────────────────────────────────

def test_scan_returns_dict_with_expected_keys(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    result = auditor.scan(tmp_tree)
    assert "root" in result
    assert "dry_run" in result
    assert "scanned_at" in result
    assert "candidates" in result
    assert "summary" in result


def test_scan_candidates_has_all_categories(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    result = auditor.scan(tmp_tree)
    for cat in ALL_CATEGORIES:
        assert cat in result["candidates"], f"Missing category: {cat}"


def test_scan_summary_has_required_fields(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    result = auditor.scan(tmp_tree)
    summary = result["summary"]
    assert "total_paths" in summary
    assert "total_size_bytes" in summary
    assert "by_category" in summary


def test_scan_node_modules_is_safe_to_delete(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    result = auditor.scan(tmp_tree)
    safe = result["candidates"][CAT_SAFE_TO_DELETE]
    paths = [item["name"] for item in safe]
    assert "node_modules" in paths


def test_scan_pycache_is_safe_to_delete(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    result = auditor.scan(tmp_tree)
    safe = result["candidates"][CAT_SAFE_TO_DELETE]
    paths = [item["name"] for item in safe]
    assert "__pycache__" in paths


def test_scan_big_log_is_safe_to_delete(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    result = auditor.scan(tmp_tree)
    safe = result["candidates"][CAT_SAFE_TO_DELETE]
    paths = [item["name"] for item in safe]
    assert "app.log" in paths


def test_scan_small_log_not_safe_to_delete(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    result = auditor.scan(tmp_tree)
    safe = result["candidates"][CAT_SAFE_TO_DELETE]
    paths = [item["name"] for item in safe]
    assert "tiny.log" not in paths


def test_scan_dry_run_default_true(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    result = auditor.scan(tmp_tree)
    assert result["dry_run"] is True


def test_scan_dry_run_never_deletes(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    """Scanning must not remove any file from the tree."""
    before = {p for p in tmp_tree.rglob("*")}
    auditor.scan(tmp_tree, dry_run=True)
    after = {p for p in tmp_tree.rglob("*")}
    assert before == after, "scan() must not delete or modify any files"


def test_scan_dry_run_false_still_never_deletes(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    """dry_run=False must also not delete anything — auditor is always read-only."""
    before = {p for p in tmp_tree.rglob("*")}
    auditor.scan(tmp_tree, dry_run=False)
    after = {p for p in tmp_tree.rglob("*")}
    assert before == after


# ── Protected path tests ──────────────────────────────────────────────────────

def test_protected_paths_not_in_safe_to_delete(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    result = auditor.scan(tmp_tree)
    safe = result["candidates"][CAT_SAFE_TO_DELETE]
    safe_names = {item["name"] for item in safe}
    for protected in PROTECTED_NAMES:
        assert protected not in safe_names, (
            f"Protected path {protected!r} must never appear in safe_to_delete"
        )


def test_src_dir_is_do_not_touch(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    result = auditor.scan(tmp_tree)
    dnt = result["candidates"][CAT_DO_NOT_TOUCH]
    dnt_names = {item["name"] for item in dnt}
    assert "src" in dnt_names


def test_docs_dir_is_do_not_touch(auditor: DiskSafetyAuditor, tmp_tree: Path) -> None:
    result = auditor.scan(tmp_tree)
    dnt = result["candidates"][CAT_DO_NOT_TOUCH]
    dnt_names = {item["name"] for item in dnt}
    assert "docs" in dnt_names


# ── generate_csv() tests ──────────────────────────────────────────────────────

def test_csv_written_correctly(auditor: DiskSafetyAuditor, tmp_tree: Path, tmp_path: Path) -> None:
    result = auditor.scan(tmp_tree)
    out = tmp_path / "out" / "candidates.csv"
    returned_path = auditor.generate_csv(result["candidates"], out)
    assert returned_path == out
    assert out.exists()


def test_csv_has_correct_headers(auditor: DiskSafetyAuditor, tmp_tree: Path, tmp_path: Path) -> None:
    result = auditor.scan(tmp_tree)
    out = tmp_path / "candidates.csv"
    auditor.generate_csv(result["candidates"], out)
    with open(out, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
    for col in ["category", "path", "name", "size_bytes", "is_dir", "reason"]:
        assert col in headers


def test_csv_row_count_matches_total_paths(auditor: DiskSafetyAuditor, tmp_tree: Path, tmp_path: Path) -> None:
    result = auditor.scan(tmp_tree)
    out = tmp_path / "candidates.csv"
    auditor.generate_csv(result["candidates"], out)
    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == result["summary"]["total_paths"]


def test_csv_does_not_delete_files(auditor: DiskSafetyAuditor, tmp_tree: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    result = auditor.scan(tmp_tree)
    before = {p for p in tmp_tree.rglob("*")}
    out = tmp_path_factory.mktemp("csv_out") / "out.csv"
    auditor.generate_csv(result["candidates"], out)
    after = {p for p in tmp_tree.rglob("*")}
    assert before == after


# ── generate_quarantine_plan() tests ─────────────────────────────────────────

def test_quarantine_plan_written(auditor: DiskSafetyAuditor, tmp_tree: Path, tmp_path: Path) -> None:
    result = auditor.scan(tmp_tree)
    out = tmp_path / "plan.md"
    returned = auditor.generate_quarantine_plan(result["candidates"], out)
    assert returned == out
    assert out.exists()


def test_quarantine_plan_is_markdown(auditor: DiskSafetyAuditor, tmp_tree: Path, tmp_path: Path) -> None:
    result = auditor.scan(tmp_tree)
    out = tmp_path / "plan.md"
    auditor.generate_quarantine_plan(result["candidates"], out)
    content = out.read_text(encoding="utf-8")
    assert "# Quarantine Plan" in content


def test_quarantine_plan_contains_safety_rules(auditor: DiskSafetyAuditor, tmp_tree: Path, tmp_path: Path) -> None:
    result = auditor.scan(tmp_tree)
    out = tmp_path / "plan.md"
    auditor.generate_quarantine_plan(result["candidates"], out)
    content = out.read_text(encoding="utf-8")
    assert "NEVER delete" in content
    assert "READ-ONLY" in content


def test_quarantine_plan_does_not_delete_files(auditor: DiskSafetyAuditor, tmp_tree: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    result = auditor.scan(tmp_tree)
    before = {p for p in tmp_tree.rglob("*")}
    out = tmp_path_factory.mktemp("plan_out") / "plan.md"
    auditor.generate_quarantine_plan(result["candidates"], out)
    after = {p for p in tmp_tree.rglob("*")}
    assert before == after
