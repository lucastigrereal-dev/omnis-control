"""P27 ActionExecutor — orchestrates action resolution, validation, approval, and execution."""
import time
from typing import Optional

from src.real_world_actions.models import (
    ActionDefinition, ActionRequest, ActionResult,
    STATUS_SUCCESS, STATUS_FAILED, STATUS_DRY_RUN, STATUS_BLOCKED,
    STATUS_TIMEOUT, STATUS_PENDING_APPROVAL,
)
from src.real_world_actions.errors import (
    UnknownActionError, ActionBlockedError, AdapterUnavailableError,
    RateLimitError, ActionDeniedError, ActionTimeoutError,
)
from src.real_world_actions.registry import ActionRegistry
from src.real_world_actions.sandbox import ActionSandbox
from src.real_world_actions.approval_chain import ApprovalChain
from src.real_world_actions.adapters import get_adapter
from src.real_world_actions.adapters.mock_adapter import MockAdapter, register as register_mock

from src.governance.models import VERDICT_APPROVED, VERDICT_DENIED


class ActionExecutor:
    """Main executor: resolve → validate → approve → execute → audit."""

    def __init__(self, dry_run: bool = True,
                 registry: Optional[ActionRegistry] = None,
                 sandbox: Optional[ActionSandbox] = None,
                 approval_chain: Optional[ApprovalChain] = None):
        self.dry_run = dry_run
        self.registry = registry or ActionRegistry()
        if registry is None:
            self.registry.seed_defaults()
            register_mock()
        self.sandbox = sandbox or ActionSandbox(self.registry)
        self.approval = approval_chain or ApprovalChain()
        self._results: list[ActionResult] = []

    def _resolve(self, action_ref: str) -> ActionDefinition:
        """Resolve an action reference: try by ID first, then by name."""
        try:
            return self.registry.get(action_ref)
        except UnknownActionError:
            return self.registry.find(action_ref)

    # ── Execute single action ─────────────────────────────────────

    def execute(self, request: ActionRequest) -> ActionResult:
        """Execute a single action through the full pipeline."""
        try:
            action = self._resolve(request.action_id)
        except UnknownActionError as e:
            return ActionResult.new(request.request_id, status=STATUS_FAILED, error=str(e))

        # Validate
        errors = self.sandbox.validate(action, request.params)
        if errors:
            return ActionResult.new(request.request_id, status=STATUS_BLOCKED,
                                    error="; ".join(errors),
                                    output={"validation_errors": errors})

        if not self.sandbox.is_allowed(action):
            return ActionResult.new(request.request_id, status=STATUS_BLOCKED,
                                    error=f"Action '{action.name}' is disabled")

        if not self.sandbox.check_rate(action):
            return ActionResult.new(request.request_id, status=STATUS_BLOCKED,
                                    error=f"Rate limit exceeded for {action.provider}/{action.name}")

        # Dry-run: return preview
        if self.dry_run or request.dry_run:
            preview = self.sandbox.preview(action, request.params)
            result = ActionResult.new(request.request_id, status=STATUS_DRY_RUN, output=preview)
            self._results.append(result)
            return result

        # Approval gate
        if action.requires_approval:
            decision = self.approval.request_approval(action, request.params,
                                                      request.request_id, request.mission_id)
            if decision.verdict == VERDICT_DENIED:
                result = ActionResult.new(request.request_id, status=STATUS_FAILED,
                                          error=f"Action denied: {decision.reason}",
                                          output={"decision_id": decision.decision_id})
                if decision.audit_event_id:
                    result.audit_event_id = decision.audit_event_id
                self._results.append(result)
                return result
            if decision.verdict != VERDICT_APPROVED:
                result = ActionResult.new(request.request_id, status=STATUS_PENDING_APPROVAL,
                                          output={"decision_id": decision.decision_id,
                                                  "message": "Awaiting operator approval"})
                if decision.audit_event_id:
                    result.audit_event_id = decision.audit_event_id
                self._results.append(result)
                return result

        # Execute via adapter
        return self._execute_real(action, request)

    def _execute_real(self, action: ActionDefinition, request: ActionRequest) -> ActionResult:
        """Actually execute the action via the provider adapter."""
        adapter = get_adapter(action.provider)
        if adapter is None:
            return ActionResult.new(request.request_id, status=STATUS_FAILED,
                                    error=f"No adapter for provider: {action.provider}")

        if not adapter.health_check():
            return ActionResult.new(request.request_id, status=STATUS_FAILED,
                                    error=f"Provider '{action.provider}' is unhealthy")

        self.sandbox.rate_limiter.record(action.provider, action.name)

        # Retry loop
        last_error = ""
        for attempt in range(action.retry_policy.max_retries + 1):
            start = time.perf_counter()
            try:
                output = adapter.execute(action.name, request.params)
                latency_ms = int((time.perf_counter() - start) * 1000)
                result = ActionResult.new(request.request_id, status=STATUS_SUCCESS,
                                          output=output, latency_ms=latency_ms, retry_count=attempt)
                self._results.append(result)
                return result
            except Exception as e:
                last_error = str(e)
                if attempt < action.retry_policy.max_retries:
                    backoff = action.retry_policy.backoff_seconds * (action.retry_policy.backoff_multiplier ** attempt)
                    time.sleep(backoff)

        result = ActionResult.new(request.request_id, status=STATUS_FAILED,
                                  error=last_error, retry_count=action.retry_policy.max_retries)
        self._results.append(result)
        return result

    # ── Batch execution ───────────────────────────────────────────

    def execute_batch(self, requests: list[ActionRequest]) -> list[ActionResult]:
        return [self.execute(r) for r in requests]

    # ── Query ─────────────────────────────────────────────────────

    def get_results(self) -> list[ActionResult]:
        return list(self._results)

    @property
    def executed_count(self) -> int:
        return len(self._results)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self._results if r.status == STATUS_SUCCESS)

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self._results if r.status == STATUS_FAILED)
