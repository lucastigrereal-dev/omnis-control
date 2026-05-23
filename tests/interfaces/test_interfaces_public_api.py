"""Public API tests for src.interfaces package exports."""
from __future__ import annotations

from src.interfaces import (
    BrowserExecutor,
    BrowserResult,
    BrowserTask,
    CodeExecutor,
    CodeResult,
    CodeSpec,
)


def test_interfaces_exports_contract_symbols():
    assert BrowserTask.__name__ == "BrowserTask"
    assert BrowserResult.__name__ == "BrowserResult"
    assert CodeSpec.__name__ == "CodeSpec"
    assert CodeResult.__name__ == "CodeResult"
    assert hasattr(BrowserExecutor, "__dict__")
    assert hasattr(CodeExecutor, "__dict__")

