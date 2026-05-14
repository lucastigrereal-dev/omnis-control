"""Tests for P27 models."""
import pytest

from src.real_world_actions.models import (
    ActionDefinition, ActionRequest, ActionResult, RateLimit, RetryPolicy,
    RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_CRITICAL,
    ACTION_READ, ACTION_WRITE, ACTION_SEND, ACTION_DEPLOY, ACTION_FINANCIAL, ACTION_DELETE,
    STATUS_SUCCESS, STATUS_FAILED, STATUS_DRY_RUN, STATUS_BLOCKED, STATUS_TIMEOUT, STATUS_PARTIAL,
)


class TestRateLimit:
    def test_defaults(self):
        rl = RateLimit()
        assert rl.max_per_hour == 60
        assert rl.max_per_day == 1000
        assert rl.concurrent_max == 3

    def test_to_dict(self):
        rl = RateLimit(max_per_hour=10, max_per_day=100, concurrent_max=2)
        d = rl.to_dict()
        assert d["max_per_hour"] == 10
        assert d["max_per_day"] == 100
        assert d["concurrent_max"] == 2

    def test_from_dict(self):
        rl = RateLimit.from_dict({"max_per_hour": 5, "max_per_day": 50})
        assert rl.max_per_hour == 5
        assert rl.max_per_day == 50

    def test_from_dict_defaults(self):
        rl = RateLimit.from_dict({})
        assert rl.max_per_hour == 60


class TestRetryPolicy:
    def test_defaults(self):
        rp = RetryPolicy()
        assert rp.max_retries == 3
        assert rp.backoff_seconds == 2.0
        assert rp.backoff_multiplier == 2.0

    def test_to_dict(self):
        rp = RetryPolicy(max_retries=5, backoff_seconds=1.0, backoff_multiplier=3.0)
        d = rp.to_dict()
        assert d["max_retries"] == 5
        assert d["backoff_seconds"] == 1.0

    def test_from_dict(self):
        rp = RetryPolicy.from_dict({"max_retries": 2, "backoff_seconds": 0.5})
        assert rp.max_retries == 2
        assert rp.backoff_seconds == 0.5

    def test_from_dict_defaults(self):
        rp = RetryPolicy.from_dict({})
        assert rp.max_retries == 3


class TestActionDefinition:
    def test_new_basic(self):
        a = ActionDefinition.new("send_email", "gmail")
        assert a.name == "send_email"
        assert a.provider == "gmail"
        assert a.action_id.startswith("rwa_")
        assert a.enabled is True

    def test_new_derives_risk_from_type(self):
        a = ActionDefinition.new("do_thing", "test", action_type=ACTION_SEND)
        assert a.risk_level == RISK_HIGH
        assert a.requires_approval is True

    def test_new_low_risk_no_approval(self):
        a = ActionDefinition.new("read_thing", "test", action_type=ACTION_READ)
        assert a.risk_level == RISK_LOW
        assert a.requires_approval is False

    def test_new_deploy_critical(self):
        a = ActionDefinition.new("deploy", "gh", action_type=ACTION_DEPLOY)
        assert a.risk_level == RISK_CRITICAL
        assert a.requires_approval is True

    def test_new_explicit_risk(self):
        a = ActionDefinition.new("custom", "test", action_type=ACTION_READ, risk_level=RISK_HIGH)
        assert a.risk_level == RISK_HIGH
        assert a.requires_approval is True

    def test_is_critical(self):
        assert ActionDefinition.new("x", "t", action_type=ACTION_DELETE).is_critical is True
        assert ActionDefinition.new("x", "t", action_type=ACTION_READ).is_critical is False

    def test_is_risky(self):
        assert ActionDefinition.new("x", "t", action_type=ACTION_SEND).is_risky is True
        assert ActionDefinition.new("x", "t", action_type=ACTION_READ).is_risky is False

    def test_to_dict(self):
        a = ActionDefinition.new("send_email", "gmail", action_type=ACTION_SEND, description="Email")
        d = a.to_dict()
        assert d["name"] == "send_email"
        assert d["provider"] == "gmail"
        assert d["action_type"] == ACTION_SEND
        assert "rate_limit" in d
        assert "retry_policy" in d

    def test_from_dict_roundtrip(self):
        a1 = ActionDefinition.new("send_email", "gmail", action_type=ACTION_SEND)
        a2 = ActionDefinition.from_dict(a1.to_dict())
        assert a2.action_id == a1.action_id
        assert a2.name == a1.name
        assert a2.risk_level == a1.risk_level

    def test_from_dict_minimal(self):
        a = ActionDefinition.from_dict({"action_id": "rwa_test", "name": "test", "provider": "mock"})
        assert a.action_id == "rwa_test"
        assert a.name == "test"
        assert a.enabled is True

    def test_timeout_and_retry_defaults(self):
        a = ActionDefinition.new("x", "t")
        assert a.timeout_seconds == 30
        assert a.retry_policy.max_retries == 3

    def test_custom_timeout(self):
        a = ActionDefinition.new("x", "t", timeout_seconds=60, max_retries=5)
        assert a.timeout_seconds == 60
        assert a.retry_policy.max_retries == 5

    def test_input_output_schema(self):
        a = ActionDefinition.new("x", "t", input_schema={"type": "object"}, output_schema={"type": "object"})
        assert a.input_schema == {"type": "object"}
        assert a.output_schema == {"type": "object"}


class TestActionRequest:
    def test_new_basic(self):
        r = ActionRequest.new("rwa_test")
        assert r.request_id.startswith("rwq_")
        assert r.action_id == "rwa_test"
        assert r.dry_run is True

    def test_new_with_params(self):
        r = ActionRequest.new("rwa_test", params={"to": "a@b.com"}, dry_run=False, mission_id="m1", step_id="s1")
        assert r.params == {"to": "a@b.com"}
        assert r.dry_run is False
        assert r.mission_id == "m1"
        assert r.step_id == "s1"

    def test_to_dict(self):
        r = ActionRequest.new("rwa_test", params={"x": 1})
        d = r.to_dict()
        assert d["action_id"] == "rwa_test"
        assert d["params"] == {"x": 1}
        assert d["dry_run"] is True

    def test_from_dict_roundtrip(self):
        r1 = ActionRequest.new("rwa_test", params={"a": 1}, dry_run=False, mission_id="m", step_id="s")
        r2 = ActionRequest.from_dict(r1.to_dict())
        assert r2.request_id == r1.request_id
        assert r2.params == r1.params
        assert r2.dry_run == r1.dry_run
        assert r2.mission_id == r1.mission_id

    def test_from_dict_minimal(self):
        r = ActionRequest.from_dict({"request_id": "rwq_x", "action_id": "rwa_y"})
        assert r.request_id == "rwq_x"
        assert r.action_id == "rwa_y"
        assert r.dry_run is True

    def test_approved_by_tracks_who_approved(self):
        r = ActionRequest.new("rwa_test")
        r.approved_by = "lucas"
        assert r.approved_by == "lucas"


class TestActionResult:
    def test_new_basic(self):
        r = ActionResult.new("rwq_test")
        assert r.result_id.startswith("rwr_")
        assert r.request_id == "rwq_test"
        assert r.status == STATUS_DRY_RUN

    def test_new_success(self):
        r = ActionResult.new("rwq_test", status=STATUS_SUCCESS, output={"ok": True}, latency_ms=150)
        assert r.status == STATUS_SUCCESS
        assert r.output == {"ok": True}
        assert r.latency_ms == 150

    def test_new_failed(self):
        r = ActionResult.new("rwq_test", status=STATUS_FAILED, error="timeout", retry_count=3)
        assert r.status == STATUS_FAILED
        assert r.error == "timeout"
        assert r.retry_count == 3

    def test_is_success(self):
        assert ActionResult.new("x", status=STATUS_SUCCESS).is_success is True
        assert ActionResult.new("x", status=STATUS_FAILED).is_success is False
        assert ActionResult.new("x", status=STATUS_DRY_RUN).is_success is False

    def test_is_terminal(self):
        assert ActionResult.new("x", status=STATUS_SUCCESS).is_terminal is True
        assert ActionResult.new("x", status=STATUS_FAILED).is_terminal is True
        assert ActionResult.new("x", status=STATUS_TIMEOUT).is_terminal is True
        assert ActionResult.new("x", status=STATUS_DRY_RUN).is_terminal is False

    def test_to_dict(self):
        r = ActionResult.new("rwq_x", status=STATUS_SUCCESS, output={"id": 1})
        d = r.to_dict()
        assert d["status"] == STATUS_SUCCESS
        assert d["output"] == {"id": 1}

    def test_from_dict_roundtrip(self):
        r1 = ActionResult.new("rwq_x", status=STATUS_SUCCESS, output={"k": "v"}, latency_ms=42, retry_count=1)
        r2 = ActionResult.from_dict(r1.to_dict())
        assert r2.result_id == r1.result_id
        assert r2.status == r1.status
        assert r2.output == r1.output
        assert r2.latency_ms == r1.latency_ms

    def test_from_dict_minimal(self):
        r = ActionResult.from_dict({"result_id": "rwr_x", "request_id": "rwq_y"})
        assert r.result_id == "rwr_x"
        assert r.status == STATUS_DRY_RUN

    def test_audit_event_id_tracking(self):
        r = ActionResult.new("x")
        r.audit_event_id = "evt_abc123"
        assert r.audit_event_id == "evt_abc123"
