import pytest
from src.capability_forge_real.sandbox import (
    SandboxRunner,
    SandboxResult,
    SandboxStatus,
    SandboxDisabledError,
    FORBIDDEN_CALLS,
    FORBIDDEN_IMPORTS,
)


class TestSandboxStatus:
    def test_all_statuses(self):
        assert SandboxStatus.PASSED.value == "passed"
        assert SandboxStatus.FAILED.value == "failed"
        assert SandboxStatus.TIMEOUT.value == "timeout"
        assert SandboxStatus.ERROR.value == "error"
        assert SandboxStatus.BLOCKED.value == "blocked"


class TestSandboxResult:
    def test_defaults(self):
        r = SandboxResult()
        assert r.status == SandboxStatus.PASSED
        assert r.is_clean is True

    def test_blocked_not_clean(self):
        r = SandboxResult(status=SandboxStatus.BLOCKED, blocked_patterns=["subprocess"])
        assert r.is_clean is False

    def test_to_dict(self):
        r = SandboxResult(
            run_id="r1",
            status=SandboxStatus.PASSED,
            stdout="hello",
            duration_ms=42.0,
            blocked_patterns=[],
        )
        d = r.to_dict()
        assert d["run_id"] == "r1"
        assert d["status"] == "passed"
        assert d["stdout"] == "hello"
        assert d["duration_ms"] == 42.0
        assert d["is_clean"] is True


class TestSandboxRunner:
    def test_safe_code_passes(self):
        runner = SandboxRunner()
        with pytest.raises(SandboxDisabledError):
            runner.run("x = 1 + 1\nresult = x * 2")

    def test_blocks_subprocess(self):
        runner = SandboxRunner()
        result = runner.dry_run_validate("import subprocess\nsubprocess.run(['ls'])")
        assert result.status == SandboxStatus.BLOCKED
        assert any("subprocess" in p for p in result.blocked_patterns)

    def test_blocks_os_system(self):
        runner = SandboxRunner()
        result = runner.dry_run_validate("os.system('rm -rf /')")
        assert result.status == SandboxStatus.BLOCKED

    def test_blocks_eval(self):
        runner = SandboxRunner()
        result = runner.dry_run_validate("eval('1+1')")
        assert result.status == SandboxStatus.BLOCKED
        assert any("eval(" in p for p in result.blocked_patterns)

    def test_blocks_socket_import(self):
        runner = SandboxRunner()
        result = runner.dry_run_validate("import socket\ns = socket.socket()")
        assert result.status == SandboxStatus.BLOCKED
        assert any("socket" in p for p in result.blocked_patterns)

    def test_blocks_requests_import(self):
        runner = SandboxRunner()
        result = runner.dry_run_validate("from requests import get")
        assert result.status == SandboxStatus.BLOCKED

    def test_dry_run_validate_safe_code(self):
        runner = SandboxRunner()
        result = runner.dry_run_validate("def hello():\n    return 'world'")
        assert result.status == SandboxStatus.PASSED

    def test_error_code_raises_disabled(self):
        runner = SandboxRunner()
        with pytest.raises(SandboxDisabledError):
            runner.run("raise ValueError('test error')")

    def test_stdout_code_raises_disabled(self):
        runner = SandboxRunner()
        with pytest.raises(SandboxDisabledError):
            runner.run("print('hello sandbox')")

    def test_forbidden_calls_set(self):
        assert "subprocess" in FORBIDDEN_CALLS
        assert "os.system" in FORBIDDEN_CALLS
        assert "eval(" in FORBIDDEN_CALLS
        assert "exec(" in FORBIDDEN_CALLS

    def test_forbidden_imports_set(self):
        assert "socket" in FORBIDDEN_IMPORTS
        assert "requests" in FORBIDDEN_IMPORTS
