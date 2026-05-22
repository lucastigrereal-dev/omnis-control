"""P22 Capability Forge Real — policy scanner wrapper for PolicyEngine v1."""
from __future__ import annotations

import tempfile
from pathlib import Path

from src.capability_forge_real.policy import PolicyEngine, PolicyReport


def scan_code(code: str) -> dict:
    """Scaneia codigo fonte contra regras de seguranca.

    Args:
        code: String com codigo Python a escanear

    Returns:
        dict com passed, violations (list[dict])
    """
    engine = PolicyEngine()

    # Write code to temp file for policy engine
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(code)
        tmp_path = Path(tmp.name)

    try:
        report: PolicyReport = engine.check_file(tmp_path)
        return {
            "passed": report.passed,
            "violations": [
                {"line": v.line, "pattern": v.pattern, "description": v.description}
                for v in report.violations
            ],
        }
    finally:
        tmp_path.unlink(missing_ok=True)


def scan_file(file_path: Path) -> dict:
    """Scaneia um arquivo em disco.

    Args:
        file_path: Path para arquivo Python

    Returns:
        dict com passed, violations
    """
    engine = PolicyEngine()
    report: PolicyReport = engine.check_file(file_path)
    return {
        "passed": report.passed,
        "violations": [
            {"line": v.line, "pattern": v.pattern, "description": v.description}
            for v in report.violations
        ],
    }
