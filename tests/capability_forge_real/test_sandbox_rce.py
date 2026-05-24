"""Security tests: SandboxRunner real-execution lock.

The subprocess sandbox is not a true sandbox (host-exec residual). Real execution
is locked via _EXEC_DISABLED until a container-isolated sandbox is built.

Tests verify:
  1. Static scanner still blocks known literal patterns (first layer, unaffected).
  2. Any code that passes the scanner raises SandboxDisabledError — real execution
     is impossible regardless of bypass technique.
  3. This includes vector 4 (subclass introspection): even though it bypasses the
     scanner, it is stopped by the disabled lock before any subprocess starts.
  4. dry_run_validate() (scan only) remains fully functional.

See: docs/INCIDENTE_RCE1.md
"""
import pytest
from src.capability_forge_real.sandbox import (
    SandboxRunner,
    SandboxDisabledError,
    SandboxStatus,
)


@pytest.fixture
def runner():
    return SandboxRunner()


# ── Static scanner still catches known literal patterns ───────────────────────

def test_literal_os_system_blocked_by_scanner(runner):
    """'os.system' literal → BLOCKED before disabled check is even reached."""
    result = runner.run("import os\nos.system('whoami')")
    assert result.status == SandboxStatus.BLOCKED


def test_direct_eval_blocked_by_scanner(runner):
    result = runner.run("eval('1+1')")
    assert result.status == SandboxStatus.BLOCKED


def test_direct_exec_blocked_by_scanner(runner):
    result = runner.run("exec('print(1)')")
    assert result.status == SandboxStatus.BLOCKED


def test_direct_import_blocked_by_scanner(runner):
    result = runner.run("__import__('os').system('id')")
    assert result.status == SandboxStatus.BLOCKED


# ── Real execution lock: SandboxDisabledError for anything that passes scanner ─

def test_safe_code_raises_disabled(runner):
    """Harmless code passes scanner but hits the disabled lock."""
    with pytest.raises(SandboxDisabledError, match="INCIDENTE_RCE1"):
        runner.run("x = 1 + 1")


def test_print_code_raises_disabled(runner):
    with pytest.raises(SandboxDisabledError):
        runner.run("print('hello')")


def test_exception_code_raises_disabled(runner):
    with pytest.raises(SandboxDisabledError):
        runner.run("raise ValueError('test')")


# ── Vector 4: subclass introspection — scanner bypass → still hits lock ───────

def test_subclass_introspection_bypasses_scanner(runner):
    """Subclass escape has no literal forbidden pattern — scanner does not block."""
    attack = (
        "for c in ().__class__.__base__.__subclasses__():\n"
        "    try:\n"
        "        g = getattr(getattr(c, '__init__', None), '__globals__', {})\n"
        "        if 'os' in g:\n"
        "            g['os'].system('echo RCE_POC_OK')\n"
        "            break\n"
        "    except Exception:\n"
        "        pass\n"
    )
    # Scanner does NOT block this (no literal 'os.system', no 'eval(' etc.)
    # But the disabled lock stops it before any subprocess starts
    with pytest.raises(SandboxDisabledError):
        runner.run(attack)


def test_subclass_introspection_cannot_execute(runner):
    """Confirm: vector 4 raises SandboxDisabledError, no subprocess ever starts."""
    # Uses os via globals traversal — no literal 'os.system' so scanner passes
    attack = (
        "for c in ().__class__.__base__.__subclasses__():\n"
        "    try:\n"
        "        g = getattr(getattr(c, '__init__', None), '__globals__', {})\n"
        "        if 'os' in g:\n"
        "            g['os'].system('echo PWNED')\n"
        "            break\n"
        "    except Exception:\n"
        "        pass\n"
    )
    with pytest.raises(SandboxDisabledError, match="container isolado"):
        runner.run(attack)


# ── dry_run_validate() unaffected — scan only, no exec path ──────────────────

def test_dry_run_validate_safe_code_still_works(runner):
    """dry_run_validate() is scan-only — lock does not affect it."""
    result = runner.dry_run_validate("x = 1 + 1\nprint(x)")
    assert result.status == SandboxStatus.PASSED


def test_dry_run_validate_still_blocks_forbidden(runner):
    """dry_run_validate() still catches forbidden patterns."""
    result = runner.dry_run_validate("os.system('whoami')")
    assert result.status == SandboxStatus.BLOCKED
