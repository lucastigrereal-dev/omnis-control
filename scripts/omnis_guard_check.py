"""OMNIS Guard Check — verifica segredos e riscos sem modificar arquivos."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HIGH_RISK_FILES = [".env", "config/*.yaml", "config/*.json"]
SECRET_PATTERNS = ["api_key", "secret", "token", "sk-", "AKIA", "master key", "password"]

EXEMPT_FILES = {"scripts/omnis_guard_check.py", "docs/OMNIS_SECRET_HANDLING_POLICY.md"}


def check_blocked_items():
    """Check if there are open P0 blockers."""
    blocked_path = ROOT / "omnis_blocked_items.yaml"
    if not blocked_path.exists():
        return [("WARNING", "omnis_blocked_items.yaml not found")]
    content = blocked_path.read_text(encoding="utf-8")
    issues = []
    # Check per-block to avoid false positives (P0 resolved + P1 open = false alarm)
    blocks = content.split("\n  - id: ")
    for block in blocks:
        if "severity: P0" in block and "status: open" in block:
            issues.append(("P0", "Open P0 blocker found in omnis_blocked_items.yaml"))
            break
    return issues


def check_staged_files():
    """Check git staged files for secret patterns (non-invasive, reads diff if available)."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=10
        )
        if result.returncode != 0:
            return []
        staged = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except Exception:
        return []

    issues = []
    for filepath in staged:
        if filepath in EXEMPT_FILES:
            continue
        try:
            full_path = ROOT / filepath
            if not full_path.exists():
                continue
            content = full_path.read_text(encoding="utf-8", errors="replace")
            for pattern in SECRET_PATTERNS:
                if pattern.lower() in content.lower():
                    issues.append(("WARNING", f"Pattern '{pattern}' found in staged file: {filepath}"))
                    break
        except Exception:
            pass
    return issues


def check_high_risk_files():
    """Check if high-risk files exist and have suspicious content."""
    issues = []
    for pattern in HIGH_RISK_FILES:
        for f in ROOT.glob(pattern):
            if f.name.startswith(".example"):
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                for sp in SECRET_PATTERNS:
                    if sp.lower() in content.lower():
                        issues.append(("WARNING", f"Pattern '{sp}' found in {f.relative_to(ROOT)}"))
                        break
            except Exception:
                pass
    return issues


def check_git_state():
    """Check if working tree has too many staged files (possible git add .)."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=10
        )
        staged_count = len([f for f in result.stdout.splitlines() if f.strip()])
        if staged_count > 20:
            return [("WARNING", f"{staged_count} files staged — possible 'git add .' detected")]
    except Exception:
        pass
    return []


def main():
    all_issues = []
    all_issues.extend(check_blocked_items())
    all_issues.extend(check_staged_files())
    all_issues.extend(check_high_risk_files())
    all_issues.extend(check_git_state())

    if not all_issues:
        print("OMNIS Guard Check: CLEAN — no issues detected.")
        return 0

    p0s = [i for i in all_issues if i[0] == "P0"]
    warnings = [i for i in all_issues if i[0] != "P0"]

    if p0s:
        print(f"P0 BLOCKERS ({len(p0s)}):")
        for _, msg in p0s:
            print(f"  [P0] {msg}")

    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for _, msg in warnings:
            print(f"  [!]  {msg}")

    return 1 if p0s else 0


if __name__ == "__main__":
    sys.exit(main())
