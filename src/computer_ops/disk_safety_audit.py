"""P15 Computer Ops — DiskSafetyAuditor: read-only disk audit, CSV and quarantine plan."""
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Category constants ────────────────────────────────────────────────────────
CAT_SAFE_TO_DELETE = "safe_to_delete"
CAT_NEEDS_REVIEW = "needs_review"
CAT_DO_NOT_TOUCH = "do_not_touch"
CAT_ACTIVE_PROJECT = "active_project"
CAT_ARCHIVED_PROJECT = "archived_project"

ALL_CATEGORIES = [
    CAT_SAFE_TO_DELETE,
    CAT_NEEDS_REVIEW,
    CAT_DO_NOT_TOUCH,
    CAT_ACTIVE_PROJECT,
    CAT_ARCHIVED_PROJECT,
]

# ── Paths that must NEVER appear in safe_to_delete ───────────────────────────
PROTECTED_NAMES = {
    ".git",
    "src",
    "tests",
    "docs",
    "config",
    ".claude",
    ".env",
    "secrets",
    "CLAUDE.md",
}

# Patterns that indicate a path is safe-to-delete
SAFE_PATTERNS = [
    "node_modules",
    "__pycache__",
    ".cache",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "htmlcov",
    ".coverage",
]

LOG_SIZE_THRESHOLD = 1 * 1024 * 1024  # 1 MB


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dir_size(path: Path) -> int:
    """Return total bytes of all files under path (best-effort)."""
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    except (PermissionError, OSError):
        pass
    return total


def _is_protected(path: Path, root: Path) -> bool:
    """Return True if path contains a protected component."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    parts = set(rel.parts)
    if parts & PROTECTED_NAMES:
        return True
    # Never mark root itself
    if path == root:
        return True
    return False


def _classify_path(path: Path, root: Path) -> tuple[str, str]:
    """Return (category, reason) for a given path."""
    name = path.name

    # Protected check first
    if _is_protected(path, root):
        return CAT_DO_NOT_TOUCH, "protected system path"

    # Active git repo indicators
    if name == ".git":
        return CAT_DO_NOT_TOUCH, "git repository root"

    # Orphaned git worktrees
    if path.parts and ".git" in path.parts and "worktrees" in path.parts:
        return CAT_NEEDS_REVIEW, "possible orphaned git worktree"

    # Safe patterns (caches, build artifacts)
    for pattern in SAFE_PATTERNS:
        if pattern in name or name == pattern:
            return CAT_SAFE_TO_DELETE, f"matches safe pattern: {pattern}"

    # Large log files
    if path.is_file() and name.endswith(".log"):
        try:
            if path.stat().st_size > LOG_SIZE_THRESHOLD:
                return CAT_SAFE_TO_DELETE, f"log file > 1MB ({path.stat().st_size} bytes)"
        except OSError:
            pass

    # Zip files in exports/
    if path.is_file() and name.endswith(".zip"):
        try:
            rel = str(path.relative_to(root))
            if "exports" in rel.lower():
                return CAT_NEEDS_REVIEW, "zip file in exports/"
        except ValueError:
            pass

    # Archived projects heuristic: contains "archive", "old", "backup", "deprecated"
    name_lower = name.lower()
    if any(kw in name_lower for kw in ("archive", "backup", "deprecated", "_old", "-old")):
        return CAT_ARCHIVED_PROJECT, "name suggests archived/backup content"

    # Active project (has src/ or pyproject.toml or package.json)
    if path.is_dir():
        markers = ["src", "pyproject.toml", "package.json", "requirements.txt"]
        for m in markers:
            if (path / m).exists():
                return CAT_ACTIVE_PROJECT, f"active project marker: {m}"

    return CAT_NEEDS_REVIEW, "no specific rule matched"


# ── DiskSafetyAuditor ─────────────────────────────────────────────────────────

class DiskSafetyAuditor:
    """Read-only disk auditor.  NEVER deletes or modifies anything."""

    def scan(self, root: Path, dry_run: bool = True) -> dict:
        """Scan root and categorize paths.

        Returns:
            {
                "root": str,
                "dry_run": bool,
                "scanned_at": str,
                "candidates": {
                    "safe_to_delete": [...],
                    "needs_review": [...],
                    "do_not_touch": [...],
                    "active_project": [...],
                    "archived_project": [...],
                },
                "summary": {
                    "total_paths": int,
                    "total_size_bytes": int,
                    "by_category": {...},
                },
            }
        """
        candidates: dict[str, list[dict]] = {cat: [] for cat in ALL_CATEGORIES}
        total_size = 0

        # Walk top-level entries first, then recurse into select dirs
        entries_to_check: list[Path] = []

        try:
            for entry in sorted(root.iterdir()):
                entries_to_check.append(entry)
        except PermissionError:
            pass

        # Also check nested __pycache__, node_modules etc. 2 levels deep
        for top in list(entries_to_check):
            if top.is_dir() and top.name not in PROTECTED_NAMES:
                try:
                    for sub in sorted(top.iterdir()):
                        if sub.is_dir() and sub.name in SAFE_PATTERNS:
                            entries_to_check.append(sub)
                except (PermissionError, OSError):
                    pass

        # Deduplicate
        seen: set[Path] = set()
        unique_entries: list[Path] = []
        for e in entries_to_check:
            if e not in seen:
                seen.add(e)
                unique_entries.append(e)

        for path in unique_entries:
            category, reason = _classify_path(path, root)
            try:
                if path.is_file():
                    size = path.stat().st_size
                elif path.is_dir():
                    size = _dir_size(path)
                else:
                    size = 0
            except OSError:
                size = 0

            total_size += size
            candidates[category].append(
                {
                    "path": str(path),
                    "size_bytes": size,
                    "reason": reason,
                    "is_dir": path.is_dir(),
                    "name": path.name,
                }
            )

        by_category = {
            cat: {
                "count": len(items),
                "total_bytes": sum(i["size_bytes"] for i in items),
            }
            for cat, items in candidates.items()
        }

        return {
            "root": str(root),
            "dry_run": dry_run,
            "scanned_at": _now_iso(),
            "candidates": candidates,
            "summary": {
                "total_paths": sum(len(v) for v in candidates.values()),
                "total_size_bytes": total_size,
                "by_category": by_category,
            },
        }

    def generate_csv(self, candidates: dict, output_path: Path) -> Path:
        """Write candidates to CSV.  Never deletes anything."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rows: list[dict] = []
        for category, items in candidates.items():
            for item in items:
                rows.append(
                    {
                        "category": category,
                        "path": item["path"],
                        "name": item["name"],
                        "size_bytes": item["size_bytes"],
                        "is_dir": item["is_dir"],
                        "reason": item["reason"],
                    }
                )

        fieldnames = ["category", "path", "name", "size_bytes", "is_dir", "reason"]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return output_path

    def generate_quarantine_plan(self, candidates: dict, output_path: Path) -> Path:
        """Write quarantine plan markdown.  Never deletes anything."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        safe = candidates.get(CAT_SAFE_TO_DELETE, [])
        review = candidates.get(CAT_NEEDS_REVIEW, [])
        dnt = candidates.get(CAT_DO_NOT_TOUCH, [])
        active = candidates.get(CAT_ACTIVE_PROJECT, [])
        archived = candidates.get(CAT_ARCHIVED_PROJECT, [])

        def fmt_bytes(b: int) -> str:
            if b >= 1_073_741_824:
                return f"{b / 1_073_741_824:.1f} GB"
            if b >= 1_048_576:
                return f"{b / 1_048_576:.1f} MB"
            if b >= 1024:
                return f"{b / 1024:.1f} KB"
            return f"{b} B"

        def section(title: str, items: list[dict], instructions: str) -> list[str]:
            lines = [f"## {title}", "", f"> {instructions}", ""]
            if not items:
                lines += ["_(none)_", ""]
                return lines
            lines.append("| Path | Size | Reason |")
            lines.append("|------|------|--------|")
            for item in items:
                size = fmt_bytes(item["size_bytes"])
                lines.append(f"| `{item['path']}` | {size} | {item['reason']} |")
            lines.append("")
            return lines

        total_safe_bytes = sum(i["size_bytes"] for i in safe)
        total_review_bytes = sum(i["size_bytes"] for i in review)

        content_lines = [
            "# Quarantine Plan — OMNIS Disk Safety Audit",
            "",
            f"**Generated:** {_now_iso()}",
            f"**Status:** READ-ONLY — no files have been modified",
            "",
            "## Summary",
            "",
            f"| Category | Count | Size |",
            f"|----------|-------|------|",
            f"| safe_to_delete | {len(safe)} | {fmt_bytes(total_safe_bytes)} |",
            f"| needs_review | {len(review)} | {fmt_bytes(total_review_bytes)} |",
            f"| do_not_touch | {len(dnt)} | — |",
            f"| active_project | {len(active)} | — |",
            f"| archived_project | {len(archived)} | — |",
            "",
            "## Safety Rules",
            "",
            "1. **NEVER delete** without explicit operator approval",
            "2. Move to quarantine dir first, keep for 14 days before permanent removal",
            "3. `do_not_touch` paths are immutable — any action requires human override",
            "4. `needs_review` paths require human decision before any action",
            "",
        ]

        content_lines += section(
            "Safe to Delete",
            safe,
            "These paths match known safe patterns (caches, build artifacts, large logs). "
            "Quarantine first, delete only after operator approval.",
        )
        content_lines += section(
            "Needs Review",
            review,
            "These paths could not be auto-classified. Human review required before any action.",
        )
        content_lines += section(
            "Do Not Touch",
            dnt,
            "Protected system paths. No action permitted.",
        )
        content_lines += section(
            "Active Projects",
            active,
            "Detected active project roots. Keep unless explicitly archiving.",
        )
        content_lines += section(
            "Archived Projects",
            archived,
            "Possible archived/backup content. Verify before removal.",
        )

        output_path.write_text("\n".join(content_lines), encoding="utf-8")
        return output_path
