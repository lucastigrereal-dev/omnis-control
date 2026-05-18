"""OMNIS State Check — verifica integridade dos YAMLs de governança."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_YAMLS = [
    "omnis.project.yaml",
    "omnis_state.yaml",
    "omnis_wave_registry.yaml",
    "omnis_worktrees.yaml",
    "omnis_blocked_items.yaml",
    "omnis_guardrails.yaml",
    "omnis_agent_tasks.yaml",
]

REQUIRED_DOCS = [
    "docs/OMNIS_SUPREME_OPERATING_SYSTEM.md",
    "docs/OMNIS_CURRENT_STATE.md",
    "docs/OMNIS_WAVE_REGISTRY.md",
    "docs/OMNIS_ACTIVE_WORKTREES.md",
    "docs/OMNIS_GUARDRAILS.md",
    "docs/OMNIS_CLAUDE_RUNBOOK.md",
    "docs/OMNIS_NEXT_ACTIONS.md",
]


def check_yamls_exist():
    missing = []
    for yf in REQUIRED_YAMLS:
        if not (ROOT / yf).exists():
            missing.append(yf)
    return missing


def check_docs_exist():
    missing = []
    for doc in REQUIRED_DOCS:
        if not (ROOT / doc).exists():
            missing.append(doc)
    return missing


def check_state_structure():
    """Check omnis_state.yaml has required keys."""
    state_path = ROOT / "omnis_state.yaml"
    if not state_path.exists():
        return ["omnis_state.yaml not found"]
    content = state_path.read_text(encoding="utf-8")
    issues = []
    for key in ["current_focus", "p0_blockers", "known_completed", "next_safe_actions"]:
        if key not in content:
            issues.append(f"omnis_state.yaml missing key: {key}")
    return issues


def check_wave_registry_structure():
    """Check omnis_wave_registry.yaml has waves defined."""
    wave_path = ROOT / "omnis_wave_registry.yaml"
    if not wave_path.exists():
        return ["omnis_wave_registry.yaml not found"]
    content = wave_path.read_text(encoding="utf-8")
    if "- id: W" not in content:
        return ["omnis_wave_registry.yaml has no waves defined"]
    return []


def check_p0_blockers():
    """Report open P0 blockers."""
    blocked_path = ROOT / "omnis_blocked_items.yaml"
    if not blocked_path.exists():
        return []
    content = blocked_path.read_text(encoding="utf-8")
    p0s = []
    # Check per-block to avoid false positives
    blocks = content.split("\n  - id: ")
    for block in blocks:
        if "severity: P0" in block and "status: open" in block:
            p0s.append("Open P0 blocker exists — check omnis_blocked_items.yaml")
            break
    return p0s


def main():
    errors = []
    warnings = []

    missing_yamls = check_yamls_exist()
    if missing_yamls:
        errors.append(f"Missing YAMLs: {', '.join(missing_yamls)}")

    missing_docs = check_docs_exist()
    if missing_docs:
        warnings.append(f"Missing docs: {', '.join(missing_docs)}")

    state_issues = check_state_structure()
    errors.extend(state_issues)

    wave_issues = check_wave_registry_structure()
    errors.extend(wave_issues)

    p0s = check_p0_blockers()
    if p0s:
        warnings.extend(p0s)

    # Print results
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  [ERROR] {e}")

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  [WARN]  {w}")

    if not errors and not warnings:
        print("OMNIS State Check: ALL GOOD — YAMLs, docs, and structure valid.")
        return 0

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
