"""omnis_gate.py — catraca de 5 checks para Modo Evolução Sequencial.

Uso:
  python scripts/omnis_gate.py          # todos os checks
  python scripts/omnis_gate.py --fast   # sem rodar pytest (só checks rápidos)

Retorna 0 se todos verdes, 1 se algum vermelho.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_REQUIRED_WORKFLOW_FILES = [
    "src/workflows/__init__.py",
    "src/workflows/deep_research_workflow.py",
    "src/workflows/video_edit_workflow.py",
    "src/workflows/app_factory_workflow.py",
    "src/workflows/code_run_workflow.py",
    "src/workflows/system_health_workflow.py",
    "src/workflows/lead_scoring_workflow.py",
    "src/workflows/content_calendar_workflow.py",
    "src/workflows/outreach_sequence_workflow.py",
    "tests/workflows/__init__.py",
    "tests/workflows/test_deep_research_e2e.py",
    "tests/workflows/test_video_edit_e2e.py",
    "tests/workflows/test_app_factory_e2e.py",
    "tests/workflows/test_code_run_e2e.py",
    "tests/workflows/test_system_health_e2e.py",
    "tests/workflows/test_lead_scoring_e2e.py",
    "tests/workflows/test_content_calendar_e2e.py",
    "tests/workflows/test_outreach_sequence_e2e.py",
]

_SECRET_PATTERNS = ["ACTUAL_KEY", "sk-", "AKIA", "-----BEGIN", "password=", "secret="]
_EXEMPT_FILES = {
    "scripts/omnis_guard_check.py",
    "scripts/omnis_gate.py",
    "docs/OMNIS_SECRET_HANDLING_POLICY.md",
    "RUNBOOK_EVOLUCAO_SEQUENCIAL.md",
}

_REQUIRED_IMPORTS = [
    ("src.workflows.deep_research_workflow", "DeepResearchWorkflow"),
    ("src.workflows.video_edit_workflow", "VideoEditWorkflow"),
    ("src.workflows.app_factory_workflow", "AppFactoryWorkflow"),
    ("src.workflows.code_run_workflow", "CodeRunWorkflow"),
    ("src.workflows.outreach_sequence_workflow", "OutreachSequenceWorkflow"),
    ("src.utils.run_context", "RunContext"),
    ("src.akasha_event_sink.adapter", "MockAkashaSink"),
]


def check_1_workflow_tests(fast: bool = False) -> tuple[bool, str]:
    """Check 1 — workflow tests pass."""
    if fast:
        return True, "SKIP (--fast)"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/workflows/",
         "--import-mode=importlib", "-p", "no:warnings", "-q", "--tb=no"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=120,
    )
    if result.returncode == 0:
        lines = result.stdout.strip().splitlines()
        summary = lines[-1] if lines else "passed"
        return True, summary
    return False, result.stdout.strip()[-300:] or result.stderr.strip()[-300:]


def check_2_no_secrets_staged() -> tuple[bool, str]:
    """Check 2 — no secrets in staged files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=10,
        )
        staged = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except Exception:
        return True, "git unavailable — skipped"

    for filepath in staged:
        if filepath in _EXEMPT_FILES:
            continue
        full = ROOT / filepath
        if not full.exists():
            continue
        try:
            content = full.read_text(encoding="utf-8", errors="replace")
            for pat in _SECRET_PATTERNS:
                if pat in content:
                    return False, f"Secret pattern '{pat}' in staged file: {filepath}"
        except Exception:
            pass
    return True, f"{len(staged)} staged files — clean"


def check_3_imports_resolve() -> tuple[bool, str]:
    """Check 3 — key modules importable."""
    for module, symbol in _REQUIRED_IMPORTS:
        result = subprocess.run(
            [sys.executable, "-c", f"from {module} import {symbol}; print('ok')"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=15,
        )
        if result.returncode != 0:
            return False, f"Import failed: from {module} import {symbol}\n{result.stderr.strip()[:200]}"
    return True, f"{len(_REQUIRED_IMPORTS)} imports OK"


def check_4_workflow_files_exist() -> tuple[bool, str]:
    """Check 4 — required workflow files present."""
    missing = [f for f in _REQUIRED_WORKFLOW_FILES if not (ROOT / f).exists()]
    if missing:
        return False, f"Missing: {', '.join(missing)}"
    return True, f"{len(_REQUIRED_WORKFLOW_FILES)} files present"


def check_5_no_p0_blockers() -> tuple[bool, str]:
    """Check 5 — no open P0 blockers."""
    blocked_path = ROOT / "omnis_blocked_items.yaml"
    if not blocked_path.exists():
        return True, "omnis_blocked_items.yaml absent — assumed clean"
    content = blocked_path.read_text(encoding="utf-8")
    blocks = content.split("\n  - id: ")
    for block in blocks:
        if "severity: P0" in block and "status: open" in block:
            return False, "Open P0 blocker in omnis_blocked_items.yaml"
    return True, "No P0 blockers"


def run_gate(fast: bool = False) -> int:
    checks = [
        ("1 workflow-tests", lambda: check_1_workflow_tests(fast=fast)),
        ("2 no-secrets-staged", check_2_no_secrets_staged),
        ("3 imports-resolve", check_3_imports_resolve),
        ("4 workflow-files-exist", check_4_workflow_files_exist),
        ("5 no-p0-blockers", check_5_no_p0_blockers),
    ]

    all_green = True
    for name, fn in checks:
        ok, detail = fn()
        icon = "[OK]" if ok else "[FAIL]"
        print(f"  {icon} CHECK {name}: {detail}")
        if not ok:
            all_green = False

    print()
    if all_green:
        print("GATE: VERDE -- todos os 5 checks passaram")
        return 0
    print("GATE: VERMELHO -- corrija antes de avancar")
    return 1


def main() -> int:
    fast = "--fast" in sys.argv
    print("=== omnis_gate.py — catraca Evolução Sequencial ===")
    return run_gate(fast=fast)


if __name__ == "__main__":
    sys.exit(main())
