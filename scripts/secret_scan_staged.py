#!/usr/bin/env python3
"""Pre-commit secret scanner for staged Python files in src/."""

import re
import subprocess
import sys
from dataclasses import dataclass


ASSIGNMENT_PATTERN = re.compile(
    r"""(?ix)
    \b[\w-]*(password|secret|api[_-]?key|access[_-]?token|token)\b
    \s*=\s*
    (["'])([^"']{3,})\2
    """
)

DSN_PATTERN = re.compile(r"""(?i)\b(password|pwd)\s*=\s*[^;\s"']+""")
PROVIDER_KEY_PATTERN = re.compile(r"""(?i)\b(sk-[a-z0-9]{10,}|ghp_[a-z0-9]{10,})\b""")


@dataclass
class Finding:
    path: str
    line_no: int
    reason: str
    line: str


def _staged_src_python_files() -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    files = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return [p for p in files if p.startswith("src/") and p.endswith(".py")]


def _read_staged_file(path: str) -> str:
    proc = subprocess.run(
        ["git", "show", f":{path}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return proc.stdout or ""


def scan_text(path: str, text: str) -> list[Finding]:
    if not text:
        return []
    findings: list[Finding] = []
    for idx, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if ASSIGNMENT_PATTERN.search(line):
            findings.append(Finding(path, idx, "hardcoded credential assignment", raw_line))
            continue

        if DSN_PATTERN.search(line):
            findings.append(Finding(path, idx, "hardcoded DSN credential fragment", raw_line))
            continue

        if PROVIDER_KEY_PATTERN.search(line):
            findings.append(Finding(path, idx, "provider key-like literal", raw_line))
            continue
    return findings


def main() -> int:
    try:
        files = _staged_src_python_files()
    except subprocess.CalledProcessError as exc:
        print(f"[codex][secret-scan] failed to list staged files: {exc}", file=sys.stderr)
        return 2

    all_findings: list[Finding] = []
    for path in files:
        try:
            content = _read_staged_file(path)
        except subprocess.CalledProcessError as exc:
            print(f"[codex][secret-scan] failed reading staged file {path}: {exc}", file=sys.stderr)
            return 2
        all_findings.extend(scan_text(path, content))

    if not all_findings:
        print(f"[codex][secret-scan] ok: scanned {len(files)} staged src/*.py files, no hardcoded secrets found.")
        return 0

    print("[codex][secret-scan] blocked: potential hardcoded secrets in staged src/*.py")
    for finding in all_findings:
        print(f"- {finding.path}:{finding.line_no} [{finding.reason}]")
        print(f"  {finding.line.strip()}")
    print("[codex][secret-scan] use os.getenv(...) and remove literals before commit.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
