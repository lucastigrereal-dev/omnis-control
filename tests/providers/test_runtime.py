"""Tests for RuntimeProvider — MockRuntimeProvider and SubprocessRuntimeProvider."""
import pytest
from src.providers.runtime import MockRuntimeProvider, SubprocessRuntimeProvider, RuntimeResult


class TestMockRuntimeProvider:
    def test_health_ok(self):
        assert MockRuntimeProvider().health_check().ok

    def test_run_returns_mock_result(self):
        p = MockRuntimeProvider()
        result = p.run("my_skill", {"x": 1})
        assert isinstance(result, RuntimeResult)
        assert result.success
        assert result.dry_run

    def test_run_with_preset_outcome(self):
        p = MockRuntimeProvider(outcomes={"s1": {"response": "hello"}})
        result = p.run("s1", {})
        assert result.output == {"response": "hello"}

    def test_run_with_exception_outcome(self):
        p = MockRuntimeProvider(outcomes={"fail": RuntimeError("broken")})
        result = p.run("fail", {})
        assert result.success is False
        assert "broken" in result.error

    def test_available_always_true(self):
        p = MockRuntimeProvider()
        assert p.available("any_skill") is True

    def test_to_dict(self):
        p = MockRuntimeProvider()
        result = p.run("skill", {})
        d = result.to_dict()
        assert d["skill_id"] == "skill"
        assert d["success"] is True

    def test_backend(self):
        assert MockRuntimeProvider().backend == "mock"

    def test_name(self):
        assert MockRuntimeProvider().name == "runtime"


class TestSubprocessRuntimeProvider:
    def test_health_ok(self):
        p = SubprocessRuntimeProvider()
        h = p.health_check()
        assert h.status.value in ("ok", "degraded")

    def test_dry_run_returns_success(self):
        p = SubprocessRuntimeProvider()
        result = p.run("test_skill", {}, dry_run=True)
        assert result.success
        assert result.dry_run

    def test_backend(self):
        assert SubprocessRuntimeProvider().backend == "subprocess"
