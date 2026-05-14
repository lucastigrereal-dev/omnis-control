"""Tests for P23 Circuit Breaker."""
import pytest

from src.autonomous_execution.circuit_breaker import CircuitBreaker
from src.autonomous_execution.errors import CircuitBreakerError


class TestCircuitBreaker:
    @pytest.fixture
    def cb(self):
        return CircuitBreaker(threshold=3)

    def test_default_threshold(self):
        cb = CircuitBreaker()
        assert cb.threshold == 3

    def test_custom_threshold(self):
        cb = CircuitBreaker(threshold=5)
        assert cb.threshold == 5

    def test_initial_state_closed(self, cb):
        assert cb.is_open is False
        assert cb.failure_count == 0

    def test_record_single_failure_does_not_open(self, cb):
        cb.record_failure("step_1")
        assert cb.is_open is False
        assert cb.failure_count == 1

    def test_record_two_failures_does_not_open(self, cb):
        cb.record_failure("step_1")
        cb.record_failure("step_2")
        assert cb.is_open is False

    def test_record_three_failures_opens(self, cb):
        cb.record_failure("step_1")
        cb.record_failure("step_2")
        cb.record_failure("step_3")
        assert cb.is_open is True
        assert cb.failure_count == 3

    def test_record_more_than_threshold_stays_open(self, cb):
        for i in range(5):
            cb.record_failure(f"step_{i}")
        assert cb.is_open is True
        assert cb.failure_count == 5

    def test_success_resets_counter(self, cb):
        cb.record_failure("step_1")
        cb.record_failure("step_2")
        cb.record_success("step_3")
        assert cb.is_open is False
        assert cb.failure_count == 0

    def test_reset_clears_all(self, cb):
        cb.record_failure("step_1")
        cb.record_failure("step_2")
        cb.record_failure("step_3")
        cb.reset()
        assert cb.is_open is False
        assert cb.failure_count == 0
        assert cb.status()["failure_history"] == []

    def test_status_returns_dict(self, cb):
        cb.record_failure("step_1")
        s = cb.status()
        assert s["failure_count"] == 1
        assert s["threshold"] == 3
        assert s["is_open"] is False
        assert s["last_failed_step_id"] == "step_1"

    def test_status_with_open_breaker(self, cb):
        for i in range(3):
            cb.record_failure(f"step_{i}")
        s = cb.status()
        assert s["is_open"] is True

    def test_failure_history_tracks_all(self, cb):
        cb.record_failure("step_a")
        cb.record_success("step_b")
        cb.record_failure("step_c")
        assert cb.status()["failure_history"] == ["step_a", "step_c"]

    def test_interleaved_success_resets_consecutive(self, cb):
        cb.record_failure("step_1")
        cb.record_success("step_2")
        cb.record_failure("step_3")
        assert cb.failure_count == 1
        assert cb.is_open is False
