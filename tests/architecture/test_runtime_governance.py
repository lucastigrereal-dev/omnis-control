"""T-009 runtime governance meta-tests.

These tests protect the local-first contract: model calls must stay behind the
router/adapters, cost limits must fail closed, and source code must not read
secrets directly.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.multi_model_orchestration.cost_tracker import CostTracker
from src.multi_model_orchestration.errors import CostLimitError
from src.multi_model_orchestration.models import ModelConfig, PROVIDER_ANTHROPIC


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

LLM_SDK_MODULES = {"anthropic", "openai"}
LLM_SDK_IMPORT_ALLOWLIST = {
    Path("src/multi_model_orchestration/adapters/anthropic_adapter.py"),
    Path("src/multi_model_orchestration/adapters/openai_adapter.py"),
}
PRINT_ALLOWLIST_PREFIXES = (
    Path("src/cli.py"),
    Path("src/cli_commands"),
    Path("src/multi_model_orchestration/cli.py"),
    Path("src/reports"),
    Path("src/publishing/approval_gate.py"),
)


def _source_files() -> list[Path]:
    return sorted(p for p in SRC_ROOT.rglob("*.py") if "__pycache__" not in p.parts)


def _relative(path: Path) -> Path:
    return path.relative_to(REPO_ROOT)


def _parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_cloud_llm_sdks_are_only_imported_by_model_adapters():
    violations: list[str] = []

    for path in _source_files():
        rel = _relative(path)
        tree = _parse(path)
        for node in ast.walk(tree):
            imported_module = ""
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_module = alias.name.split(".", 1)[0]
                    if imported_module in LLM_SDK_MODULES and rel not in LLM_SDK_IMPORT_ALLOWLIST:
                        violations.append(f"{rel}:{node.lineno} imports {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_module = node.module.split(".", 1)[0]
                if imported_module in LLM_SDK_MODULES and rel not in LLM_SDK_IMPORT_ALLOWLIST:
                    violations.append(f"{rel}:{node.lineno} imports from {node.module}")

    assert violations == []


def test_cost_tracker_fails_closed_when_daily_limit_is_exceeded():
    tracker = CostTracker(daily_limit_usd=0.01, dry_run=False)
    model = ModelConfig.new("claude-test", PROVIDER_ANTHROPIC, cost_per_1k_tokens=0.01)

    tracker.record(model, "seed_spend", 1000)

    with pytest.raises(CostLimitError):
        tracker.assert_within_limit(0.001)


def test_source_does_not_read_dotenv_files_or_dump_full_environment():
    violations: list[str] = []

    for path in _source_files():
        rel = _relative(path)
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                first_arg = node.args[0] if node.args else None

                if isinstance(func, ast.Name) and func.id == "open":
                    if isinstance(first_arg, ast.Constant) and str(first_arg.value).startswith(".env"):
                        violations.append(f"{rel}:{node.lineno} opens {first_arg.value!r}")

                if isinstance(func, ast.Attribute) and func.attr in {"read_text", "read_bytes"}:
                    receiver = func.value
                    if (
                        isinstance(receiver, ast.Call)
                        and isinstance(receiver.func, ast.Name)
                        and receiver.func.id == "Path"
                        and receiver.args
                        and isinstance(receiver.args[0], ast.Constant)
                        and str(receiver.args[0].value).startswith(".env")
                    ):
                        violations.append(f"{rel}:{node.lineno} reads dotenv via Path")

                if isinstance(func, ast.Name) and func.id in {"print", "json_dump", "json_dumps"}:
                    for arg in node.args:
                        if (
                            isinstance(arg, ast.Attribute)
                            and isinstance(arg.value, ast.Name)
                            and arg.value.id == "os"
                            and arg.attr == "environ"
                        ):
                            violations.append(f"{rel}:{node.lineno} may dump os.environ")

    assert violations == []


def test_print_is_not_used_outside_cli_and_report_boundaries():
    violations: list[str] = []

    for path in _source_files():
        rel = _relative(path)
        if rel.name == "cli.py" or any(rel == allowed or allowed in rel.parents for allowed in PRINT_ALLOWLIST_PREFIXES):
            continue

        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                violations.append(f"{rel}:{node.lineno} uses print()")

    assert violations == []
