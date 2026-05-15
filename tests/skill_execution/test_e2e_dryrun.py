"""W050 — Skill Execution E2E dry-run test."""
from src.skill_execution.request import SkillExecutionRequest, SkillExecutionRisk
from src.skill_execution.result import SkillExecutionResult, ExecutionStatus
from src.skill_execution.boundaries import BoundaryChecker
from src.skill_execution.permission_gate import PermissionGate
from src.skill_execution.dryrun_executor import DryRunExecutor
from src.skill_execution.events import SkillEventBus, SkillExecutionEvent, SkillEventType
from src.skill_execution.artifacts import ArtifactRegistry, SkillArtifact
from src.skill_execution.service import SkillExecutionService
from src.skill_execution.resource_limits import (
    ResourceLimits,
    ResourceLimitEnforcer,
    LimitViolation,
)
from src.skill_execution.test_harness import (
    SkillTestHarness,
    SkillTestCase,
    SkillTestStatus,
)


class TestSkillExecutionE2E:

    def test_full_pipeline_safe_skill(self):
        service = SkillExecutionService()
        request = SkillExecutionRequest(
            skill_id="generate_seogram_caption",
            intent="create caption for Instagram post about Natal tourism",
            payload={"topic": "turismo em Natal", "posts": 3},
            dry_run=True,
        )
        result = service.execute(request)
        assert result.status == ExecutionStatus.DRY_RUN_OK
        assert result.is_ok is True

    def test_blocked_critical_risk(self):
        request = SkillExecutionRequest(
            skill_id="deploy",
            intent="deploy to production",
            payload={"target": "production"},
            dry_run=False,
            risk_level=SkillExecutionRisk.CRITICAL,
        )
        gate = PermissionGate()
        result = gate.evaluate(request)
        assert result.status == ExecutionStatus.BLOCKED

    def test_needs_approval_high_risk(self):
        request = SkillExecutionRequest(
            skill_id="some_high_risk_skill",
            intent="modify production data",
            payload={"action": "delete"},
            dry_run=False,
            risk_level=SkillExecutionRisk.HIGH,
        )
        gate = PermissionGate()
        result = gate.evaluate(request)
        assert result.status == ExecutionStatus.NEEDS_APPROVAL

    def test_resource_limits_within_bounds(self):
        limits = ResourceLimits.safe_defaults()
        violations = ResourceLimitEnforcer.check_limits(
            limits,
            elapsed_ms=30_000,
            memory_used_mb=100,
            cpu_percent=30,
            disk_used_mb=20,
            network_calls=0,
        )
        assert len(violations) == 0
        assert ResourceLimitEnforcer.is_within_limits(limits,
            elapsed_ms=30_000, memory_used_mb=100, cpu_percent=30, disk_used_mb=20, network_calls=0)

    def test_resource_limits_violations(self):
        limits = ResourceLimits.safe_defaults()
        violations = ResourceLimitEnforcer.check_limits(
            limits,
            elapsed_ms=120_000,
            memory_used_mb=512,
            cpu_percent=95,
            disk_used_mb=200,
            network_calls=5,
        )
        assert len(violations) == 5  # timeout, memory, cpu, disk, network
        assert LimitViolation.TIMEOUT in violations
        assert LimitViolation.MEMORY in violations
        assert ResourceLimitEnforcer.should_kill(limits, violations) is True

    def test_event_bus_full_cycle(self):
        bus = SkillEventBus()

        events_received: list[SkillEventType] = []

        def collector(event: SkillExecutionEvent):
            events_received.append(event.event_type)

        for etype in SkillEventType:
            bus.subscribe(etype, collector)

        bus.emit(SkillExecutionEvent(event_type=SkillEventType.REQUEST_RECEIVED, skill_id="test"))
        bus.emit(SkillExecutionEvent(event_type=SkillEventType.PERMISSION_CHECKED, skill_id="test"))
        bus.emit(SkillExecutionEvent(event_type=SkillEventType.EXECUTION_STARTED, skill_id="test"))
        bus.emit(SkillExecutionEvent(event_type=SkillEventType.EXECUTION_COMPLETED, skill_id="test"))

        assert len(events_received) == 4
        assert events_received[0] == SkillEventType.REQUEST_RECEIVED
        assert events_received[-1] == SkillEventType.EXECUTION_COMPLETED

    def test_test_harness_smoke_suite(self):
        suite = SkillTestHarness.create_smoke_suite("test_skill")
        assert len(suite.cases) == 2

        SkillTestHarness.run_suite(suite)
        summary = suite.summary()

        assert summary["total"] == 2
        assert summary["skill_name"] == "test_skill"
        assert summary["all_passed"] is True

    def test_test_harness_custom_case(self):
        case = SkillTestCase(
            name="custom_test",
            description="validates specific behavior",
            expected_status="DRY_RUN_OK",
            expected_artifacts=["caption.md", "metadata.json"],
            should_pass=True,
        )
        result = SkillTestHarness.run_test(case)
        assert result.status == SkillTestStatus.PASSED
        assert result.case_name == "custom_test"

    def test_full_e2e_with_boundary_check(self):
        # 1. Boundary check
        checker = BoundaryChecker()
        result = checker.check("filesystem_read", zone="src/skills/")
        assert result.passed is True

        result = checker.check("secrets_access", zone=".env")
        assert result.passed is False

        # 2. Permission gate
        gate = PermissionGate()
        request = SkillExecutionRequest(
            skill_id="generate_seogram_caption",
            intent="create caption",
            payload={"topic": "test"},
            dry_run=True,
            risk_level=SkillExecutionRisk.LOW,
        )
        gate_result = gate.evaluate(request)
        assert gate_result.status == ExecutionStatus.DRY_RUN_OK

        # 3. Dry-run execution
        executor = DryRunExecutor()
        exec_result = executor.execute(request)
        assert exec_result.status == ExecutionStatus.DRY_RUN_OK

        # 4. Register artifact
        registry = ArtifactRegistry()
        artifact = SkillArtifact(
            execution_result_id=exec_result.result_id,
            artifact_type="caption",
            data={"topic": "test", "status": "dry_run_ok"},
        )
        registry.register(artifact)
        assert registry.count == 1

    def test_permission_gate_forbidden_actions(self):
        gate = PermissionGate()

        for forbidden_intent in ["read_env", "push_origin", "deploy_production"]:
            request = SkillExecutionRequest(
                skill_id="any_skill",
                intent=forbidden_intent,
            )
            result = gate.evaluate(request)
            assert result.status == ExecutionStatus.BLOCKED

    def test_generous_limits(self):
        limits = ResourceLimits.generous_defaults()
        assert limits.timeout_ms == 600_000
        assert limits.max_memory_mb == 2048
        assert limits.max_network_calls == 10
        assert limits.kill_on_violation is False
