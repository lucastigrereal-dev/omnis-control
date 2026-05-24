"""RCE bypass tests — all 3 attack paths must fail after _SAFE_BUILTINS fix."""
import pytest
from src.capability_forge_real.sandbox import SandboxRunner, SandboxStatus


@pytest.fixture
def runner():
    return SandboxRunner()


def test_bypass_getattr_builtins_denied(runner):
    """getattr(__builtins__, 'eval') fails — getattr not in _SAFE_BUILTINS."""
    result = runner.run("getattr(__builtins__, 'eval')")
    assert result.status == SandboxStatus.ERROR
    assert "getattr" in result.error.lower() or "nameerror" in result.error.lower()


def test_bypass_vars_builtins_denied(runner):
    """vars(__builtins__)['eval'] fails — vars not in _SAFE_BUILTINS."""
    result = runner.run("vars(__builtins__)['eval']")
    assert result.status == SandboxStatus.ERROR
    assert "vars" in result.error.lower() or "nameerror" in result.error.lower()


def test_bypass_dunder_dict_denied(runner):
    """__builtins__.__dict__['exec'] fails — dict instances have no __dict__."""
    result = runner.run("__builtins__.__dict__['exec']")
    assert result.status == SandboxStatus.ERROR


def test_direct_eval_blocked_by_scanner(runner):
    """eval() is caught by the static scanner before exec."""
    result = runner.run("eval('1+1')")
    assert result.status == SandboxStatus.BLOCKED


def test_direct_exec_blocked_by_scanner(runner):
    """exec() is caught by the static scanner before exec."""
    result = runner.run("exec('print(1)')")
    assert result.status == SandboxStatus.BLOCKED


def test_safe_print_works(runner):
    """print() must still work — it is in _SAFE_BUILTINS."""
    result = runner.run("print('hello sandbox')")
    assert result.status == SandboxStatus.PASSED
    assert "hello sandbox" in result.stdout


def test_safe_exception_works(runner):
    """raise ValueError() must still work — ValueError is in _SAFE_BUILTINS."""
    result = runner.run("raise ValueError('test rce')")
    assert result.status == SandboxStatus.ERROR
    assert "test rce" in result.error


def test_safe_arithmetic_works(runner):
    """Basic arithmetic must work with no builtins needed."""
    result = runner.run("x = 1 + 1\nresult = x * 2")
    assert result.status == SandboxStatus.PASSED
