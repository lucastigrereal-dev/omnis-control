"""E2E tests for P27 Real World Actions."""
import pytest

from src.real_world_actions.registry import ActionRegistry
from src.real_world_actions.executor import ActionExecutor
from src.real_world_actions.models import (
    ActionRequest, ActionDefinition, ActionResult,
    STATUS_SUCCESS, STATUS_FAILED, STATUS_DRY_RUN, STATUS_BLOCKED,
    ACTION_READ, ACTION_SEND, ACTION_DEPLOY,
    RISK_LOW, RISK_HIGH, RISK_CRITICAL,
)
from src.real_world_actions.sandbox import ActionSandbox
from src.real_world_actions.approval_chain import ApprovalChain
from src.real_world_actions.rate_limiter import RateLimiter
from src.real_world_actions.adapters.mock_adapter import register as register_mock
from src.real_world_actions.cli import main as cli_main


class TestE2ERegistryToSandboxToExecute:
    """Full cycle: Registry → Sandbox → Approval → Execute → Audit."""

    @pytest.fixture
    def executor(self):
        return ActionExecutor(dry_run=True)

    def test_full_dry_run_cycle(self, executor):
        a = executor.registry.find("health_check")
        req = ActionRequest.new(a.action_id, params={})
        result = executor.execute(req)
        assert result.status == STATUS_DRY_RUN
        assert result.output["would_execute"] is True
        assert result.output["requires_approval"] is False

    def test_send_action_shows_approval_required(self, executor):
        a = executor.registry.find("send_email")
        req = ActionRequest.new(a.action_id, params={"to": "x@y.com"})
        result = executor.execute(req)
        assert result.output["requires_approval"] is True

    def test_critical_action_has_double_approval_info(self, executor):
        a = executor.registry.find("git_push")
        req = ActionRequest.new(a.action_id, params={"branch": "main"})
        result = executor.execute(req)
        assert result.output["risk_level"] == RISK_CRITICAL

    def test_real_execution_with_mock_produces_success(self):
        executor = ActionExecutor(dry_run=False)
        register_mock()
        a = executor.registry.find("health_check")
        req = ActionRequest.new(a.action_id, dry_run=False)
        result = executor.execute(req)
        assert result.status == STATUS_SUCCESS


class TestE2EApprovalFlow:
    def test_approval_chain_full_flow(self):
        from src.governance.service import ApprovalPolicyEngine
        engine = ApprovalPolicyEngine()
        chain = ApprovalChain(engine)

        a = ActionDefinition.new("send_email", "gmail", ACTION_SEND)
        decision = chain.request_approval(a, {"to": "x@y.com"})
        assert decision.verdict == "requires_approval"

        pending = chain.get_pending()
        assert len(pending) == 1

        approved = chain.approve(pending[0].request_id, approved_by="operator", reason="legit")
        assert approved.verdict == "approved"
        assert chain.pending_count == 0

    def test_approval_deny_flow(self):
        from src.governance.service import ApprovalPolicyEngine
        engine = ApprovalPolicyEngine()
        chain = ApprovalChain(engine)

        a = ActionDefinition.new("call_webhook", "webhook", ACTION_SEND)
        chain.request_approval(a, {"url": "https://x.com"})
        pending = chain.get_pending()

        denied = chain.deny(pending[0].request_id, "not needed")
        assert denied.verdict == "denied"


class TestE2ECLIIntegration:
    def test_cli_list(self):
        assert cli_main(["list"]) == 0

    def test_cli_preview(self):
        assert cli_main(["preview", "health_check"]) == 0

    def test_cli_execute_dry_run(self):
        assert cli_main(["execute", "health_check", "--params", "{}"]) == 0

    def test_cli_providers(self):
        assert cli_main(["providers"]) == 0

    def test_cli_approve_deny(self):
        assert cli_main(["approve", "rwq_test"]) == 0
        assert cli_main(["deny", "rwq_test", "--reason", "test"]) == 0

    def test_cli_no_command(self):
        assert cli_main([]) == 1


class TestE2ESnapshotRoundtrip:
    def test_action_definition_roundtrip(self):
        a1 = ActionDefinition.new("send_email", "gmail", ACTION_SEND, description="Email")
        a2 = ActionDefinition.from_dict(a1.to_dict())
        assert a2.name == a1.name
        assert a2.provider == a1.provider
        assert a2.risk_level == a1.risk_level

    def test_result_roundtrip(self):
        r1 = ActionResult.new("rwq_x", status=STATUS_SUCCESS, output={"ok": True}, latency_ms=100)
        r2 = ActionResult.from_dict(r1.to_dict())
        assert r2.status == r1.status
        assert r2.latency_ms == r1.latency_ms

    def test_registry_roundtrip(self):
        r1 = ActionRegistry()
        r1.seed_defaults()
        r2 = ActionRegistry.from_dict(r1.to_dict())
        assert r2.count == r1.count
        assert r2.action_names() == r1.action_names()


class TestE2EDegradation:
    def test_unknown_action_does_not_crash(self):
        executor = ActionExecutor(dry_run=True)
        req = ActionRequest.new("rwa_nonexistent")
        result = executor.execute(req)
        assert isinstance(result, ActionResult)
        assert result.status != STATUS_SUCCESS  # but never crashes

    def test_missing_adapter_reports_error(self):
        executor = ActionExecutor(dry_run=False)
        a = ActionDefinition.new("custom", "no-adapter", ACTION_READ)
        executor.registry.register(a)
        req = ActionRequest.new(a.action_id, dry_run=False)
        result = executor.execute(req)
        assert result.status == STATUS_FAILED

    def test_empty_params_are_handled(self):
        executor = ActionExecutor(dry_run=True)
        a = executor.registry.find("health_check")
        req = ActionRequest.new(a.action_id)
        result = executor.execute(req)
        assert result.status == STATUS_DRY_RUN
