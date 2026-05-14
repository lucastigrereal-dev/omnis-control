"""Tests for P27 ActionExecutor."""
import pytest

from src.real_world_actions.executor import ActionExecutor
from src.real_world_actions.models import (
    ActionRequest, ActionResult, ActionDefinition,
    STATUS_SUCCESS, STATUS_FAILED, STATUS_DRY_RUN, STATUS_BLOCKED, STATUS_TIMEOUT,
    ACTION_READ, ACTION_SEND, ACTION_DEPLOY,
)
from src.real_world_actions.registry import ActionRegistry
from src.real_world_actions.adapters.mock_adapter import register as register_mock


class TestActionExecutor:
    @pytest.fixture
    def executor(self):
        return ActionExecutor(dry_run=True)

    @pytest.fixture
    def real_executor(self):
        return ActionExecutor(dry_run=False)

    def test_dry_run_returns_preview(self, executor):
        req = ActionRequest.new(executor.registry.find("health_check").action_id)
        result = executor.execute(req)
        assert result.status == STATUS_DRY_RUN
        assert "would_execute" in result.output

    def test_dry_run_shows_approval_needed_for_send(self, executor):
        req = ActionRequest.new(executor.registry.find("send_email").action_id)
        result = executor.execute(req)
        assert result.status == STATUS_DRY_RUN
        assert result.output["requires_approval"] is True

    def test_unknown_action_fails(self, executor):
        req = ActionRequest.new("rwa_nonexistent")
        result = executor.execute(req)
        assert result.status in (STATUS_FAILED, STATUS_BLOCKED)

    def test_disabled_action_blocked(self, executor):
        a = executor.registry.find("health_check")
        a.enabled = False
        req = ActionRequest.new(a.action_id)
        result = executor.execute(req)
        assert result.status == STATUS_BLOCKED

    def test_validation_errors_block_action(self, executor):
        a = ActionDefinition.new("validated_action", "mock", ACTION_READ,
                                 input_schema={"required": ["to"], "properties": {"to": {"type": "string"}}})
        executor.registry.register(a)
        req = ActionRequest.new(a.action_id, params={})
        result = executor.execute(req)
        assert result.status == STATUS_BLOCKED

    def test_real_executor_with_mock_adapter(self, real_executor):
        a = real_executor.registry.find("health_check")
        req = ActionRequest.new(a.action_id, dry_run=False)
        result = real_executor.execute(req)
        assert result.status == STATUS_SUCCESS
        assert result.output["status"] == "healthy"

    def test_real_executor_rate_limit_blocked(self):
        from src.real_world_actions.rate_limiter import RateLimiter
        from src.real_world_actions.models import RateLimit

        registry = ActionRegistry()
        registry.seed_defaults()
        register_mock()
        rl = RateLimiter()
        # Fill hourly limit for mock health_check
        strict = RateLimit(max_per_hour=0)
        a = registry.find("health_check")
        a.rate_limit = strict

        from src.real_world_actions.sandbox import ActionSandbox
        sandbox = ActionSandbox(registry, rl)

        executor = ActionExecutor(dry_run=False, registry=registry, sandbox=sandbox)
        req = ActionRequest.new(a.action_id, dry_run=False)
        result = executor.execute(req)
        assert result.status == STATUS_BLOCKED

    def test_batch_execution(self, executor):
        a1 = executor.registry.find("health_check")
        a2 = executor.registry.find("send_email")
        results = executor.execute_batch([
            ActionRequest.new(a1.action_id),
            ActionRequest.new(a2.action_id),
        ])
        assert len(results) == 2
        assert all(isinstance(r, ActionResult) for r in results)

    def test_get_results_accumulates(self, executor):
        req = ActionRequest.new(executor.registry.find("health_check").action_id)
        executor.execute(req)
        executor.execute(req)
        assert len(executor.get_results()) == 2

    def test_executed_count(self, executor):
        req = ActionRequest.new(executor.registry.find("health_check").action_id)
        executor.execute(req)
        assert executor.executed_count == 1

    def test_success_and_failure_counts(self, real_executor):
        a = real_executor.registry.find("health_check")
        req = ActionRequest.new(a.action_id, dry_run=False)
        real_executor.execute(req)
        assert real_executor.success_count == 1
        assert real_executor.failure_count == 0

    def test_approval_gate_for_send_action(self, real_executor):
        a = real_executor.registry.find("send_email")
        req = ActionRequest.new(a.action_id, dry_run=False, params={"to": "x@y.com"})
        result = real_executor.execute(req)
        # Should be pending_approval since no one approved yet
        assert result.status in (STATUS_FAILED, "pending_approval")

    def test_dry_run_request_overrides_executor_mode(self, real_executor):
        a = real_executor.registry.find("health_check")
        req = ActionRequest.new(a.action_id, dry_run=True)
        result = real_executor.execute(req)
        assert result.status == STATUS_DRY_RUN

    def test_no_adapter_for_provider_fails(self):
        executor = ActionExecutor(dry_run=False)
        a = ActionDefinition.new("custom_action", "nonexistent_provider", ACTION_READ)
        executor.registry.register(a)
        req = ActionRequest.new(a.action_id, dry_run=False)
        result = executor.execute(req)
        assert result.status == STATUS_FAILED

    def test_execute_handles_retries(self, real_executor):
        a = real_executor.registry.find("health_check")
        a.retry_policy.max_retries = 3
        req = ActionRequest.new(a.action_id, dry_run=False)
        result = real_executor.execute(req)
        assert result.status == STATUS_SUCCESS
        # Should succeed on first attempt with mock adapter
        assert result.retry_count == 0
