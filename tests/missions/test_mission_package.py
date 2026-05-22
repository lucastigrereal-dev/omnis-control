"""M6.9 Tests — Mission Package MVP: schema, lifecycle, events, memory, cost, serialization."""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from src.missions.models import (
    MissionContract,
    BudgetCaps,
    AcceptanceCriterion,
    Priority,
    Sector,
    RiskLevel,
    ApprovalPolicy,
)
from src.missions.events import EventEnvelope, EVENT_TYPES
from src.missions.state_machine import (
    MissionStatus,
    VALID_TRANSITIONS,
    assert_transition,
    InvalidTransitionError,
)
from src.missions.memory_lookup import (
    MemoryContext,
    MemoryLookupAdapter,
    MockMemoryLookup,
)
from src.missions.cost_tracker import (
    CostEstimate,
    CostTracker,
    MockCostTracker,
)
from src.missions.task_decomposition import (
    TaskType,
    TaskStatus,
    MissionTask,
    TaskDecomposition,
)
from src.missions.mission_package import MissionPackage


# ---------------------------------------------------------------------------
# M6.2 — Schema valid/invalid
# ---------------------------------------------------------------------------

class TestMissionContractExtended:
    """MissionContract com campos M6.2."""

    def test_default_priority_is_medium(self):
        c = MissionContract(title="T", objective="O", sector=Sector.RESEARCH)
        assert c.priority == Priority.MEDIUM

    def test_explicit_priority(self):
        c = MissionContract(title="T", objective="O", sector=Sector.RESEARCH, priority=Priority.HIGH)
        assert c.priority == Priority.HIGH

    def test_mission_id_auto_set_to_content_hash(self):
        c = MissionContract(title="T", objective="O", sector=Sector.RESEARCH)
        assert c.mission_id == c.content_hash()
        assert len(c.mission_id) == 64

    def test_mission_id_explicit_preserved(self):
        c = MissionContract(title="T", objective="O", sector=Sector.RESEARCH, mission_id="custom-123")
        assert c.mission_id == "custom-123"

    def test_new_fields_have_defaults(self):
        c = MissionContract(title="T", objective="O", sector=Sector.RESEARCH)
        assert c.intent == ""
        assert c.source == ""
        assert c.owner == ""
        assert c.correlation_id == ""
        assert c.cost_estimate == 0.0
        assert c.memory_context_ids == []
        assert c.tasks == []
        assert c.updated_at is None

    def test_all_new_fields_serializable(self, sample_contract):
        c = MissionContract(
            title="Full",
            objective="Test all fields",
            sector=Sector.OPERATIONS,
            priority=Priority.CRITICAL,
            intent="Execute marketing campaign",
            source="jarvis-router",
            owner="agent-7",
            correlation_id="corr-abc-123",
            cost_estimate=1.50,
            memory_context_ids=["chunk-1", "chunk-2"],
            tasks=[{"id": "task-1", "type": "planning"}],
        )
        d = json.loads(c.model_dump_json())
        assert d["priority"] == "critical"
        assert d["intent"] == "Execute marketing campaign"
        assert d["source"] == "jarvis-router"
        assert d["owner"] == "agent-7"
        assert d["correlation_id"] == "corr-abc-123"
        assert d["cost_estimate"] == 1.50
        assert d["memory_context_ids"] == ["chunk-1", "chunk-2"]
        assert len(d["tasks"]) == 1

    def test_content_hash_excludes_new_ephemeral_fields(self):
        c1 = MissionContract(title="T", objective="O", sector=Sector.RESEARCH, mission_id="custom")
        c2 = MissionContract(title="T", objective="O", sector=Sector.RESEARCH, mission_id="different")
        assert c1.content_hash() == c2.content_hash()

    def test_contract_still_requires_title_objective_sector(self):
        with pytest.raises(ValidationError):
            MissionContract(title="T")

    def test_invalid_priority_raises(self):
        with pytest.raises(ValidationError):
            MissionContract(title="T", objective="O", sector=Sector.RESEARCH, priority="invalid")


# ---------------------------------------------------------------------------
# M6.3 — Lifecycle transitions
# ---------------------------------------------------------------------------

class TestExtendedLifecycle:
    """9 estados com CREATED e PLANNED."""

    def test_all_nine_states_exist(self):
        expected = {"draft", "created", "planned", "running", "waiting_approval", "paused", "completed", "failed", "cancelled"}
        actual = {s.value for s in MissionStatus}
        assert actual == expected

    def test_draft_to_created_valid(self):
        assert_transition(MissionStatus.DRAFT, MissionStatus.CREATED)

    def test_created_to_planned_valid(self):
        assert_transition(MissionStatus.CREATED, MissionStatus.PLANNED)

    def test_planned_to_running_valid(self):
        assert_transition(MissionStatus.PLANNED, MissionStatus.RUNNING)

    def test_draft_to_running_still_valid(self):
        assert_transition(MissionStatus.DRAFT, MissionStatus.RUNNING)

    def test_created_to_cancelled_valid(self):
        assert_transition(MissionStatus.CREATED, MissionStatus.CANCELLED)

    def test_planned_to_cancelled_valid(self):
        assert_transition(MissionStatus.PLANNED, MissionStatus.CANCELLED)

    def test_draft_to_planned_invalid(self):
        with pytest.raises(InvalidTransitionError):
            assert_transition(MissionStatus.DRAFT, MissionStatus.PLANNED)

    def test_created_to_running_invalid(self):
        with pytest.raises(InvalidTransitionError):
            assert_transition(MissionStatus.CREATED, MissionStatus.RUNNING)

    def test_completed_is_terminal(self):
        assert VALID_TRANSITIONS[MissionStatus.COMPLETED] == []

    def test_cancelled_is_terminal(self):
        assert VALID_TRANSITIONS[MissionStatus.CANCELLED] == []

    def test_failed_can_retry(self):
        assert MissionStatus.RUNNING in VALID_TRANSITIONS[MissionStatus.FAILED]


# ---------------------------------------------------------------------------
# M6.4 — Event payloads (including mission_planned)
# ---------------------------------------------------------------------------

class TestEventPayloads:
    """Verifica que mission_planned existe e payloads sao validos."""

    def test_mission_planned_in_event_types(self):
        assert "mission_planned" in EVENT_TYPES

    def test_mission_planned_event_creates(self):
        ev = EventEnvelope(
            mission_id="test-123",
            event_type="mission_planned",
            sequence=1,
            actor="planner",
            payload={"plan_id": "plan-001", "task_count": 5},
        )
        assert ev.event_type == "mission_planned"
        assert ev.payload["plan_id"] == "plan-001"
        assert ev.payload["task_count"] == 5

    def test_all_lifecycle_events_exist(self):
        lifecycle_events = {
            "mission_created", "mission_planned", "mission_started",
            "mission_completed", "mission_failed", "mission_cancelled",
            "mission_paused", "mission_resumed",
        }
        assert lifecycle_events.issubset(set(EVENT_TYPES))

    def test_event_jsonl_roundtrip(self):
        ev = EventEnvelope(
            mission_id="test-123",
            event_type="mission_created",
            sequence=1,
            actor="test",
            delta_tokens=100,
            delta_cost_usd=0.05,
        )
        line = ev.to_jsonl()
        restored = EventEnvelope.from_jsonl(line)
        assert restored.mission_id == ev.mission_id
        assert restored.event_type == ev.event_type
        assert restored.sequence == ev.sequence

    def test_invalid_event_type_raises(self):
        with pytest.raises(ValidationError):
            EventEnvelope(
                mission_id="test",
                event_type="invalid_event",
                sequence=1,
                actor="test",
            )


# ---------------------------------------------------------------------------
# M6.5 — Memory Lookup fallback
# ---------------------------------------------------------------------------

class TestMemoryLookup:
    """MockMemoryLookup sempre retorna UNKNOWN."""

    def test_mock_returns_unknown(self):
        adapter = MockMemoryLookup()
        ctx = adapter.lookup("test intent", limit=5)
        assert ctx.source == "unknown"
        assert ctx.chunks == []
        assert ctx.relevance_score == 0.0
        assert ctx.query == "test intent"

    def test_memory_context_is_frozen(self):
        ctx = MemoryContext(query="q")
        with pytest.raises(ValidationError):
            ctx.source = "modified"

    def test_adapter_is_abstract(self):
        with pytest.raises(TypeError):
            MemoryLookupAdapter()


# ---------------------------------------------------------------------------
# M6.6 — Cost Tracking fallback
# ---------------------------------------------------------------------------

class TestCostTracking:
    """MockCostTracker sempre retorna zero."""

    def test_mock_estimate_returns_zero(self):
        tracker = MockCostTracker()
        est = tracker.estimate("mis-1", task_count=5, estimated_tokens=1000)
        assert est.estimated_cost == 0.0
        assert est.actual_cost == 0.0
        assert est.source == "mock"
        assert est.mission_id == "mis-1"

    def test_mock_actual_returns_zero(self):
        tracker = MockCostTracker()
        est = tracker.actual("mis-2")
        assert est.estimated_cost == 0.0
        assert est.actual_cost == 0.0
        assert est.source == "mock"

    def test_cost_estimate_is_frozen(self):
        est = CostEstimate(mission_id="m1", estimated_cost=5.0)
        with pytest.raises(ValidationError):
            est.estimated_cost = 10.0

    def test_tracker_is_abstract(self):
        with pytest.raises(TypeError):
            CostTracker()


# ---------------------------------------------------------------------------
# M6.7 — Task Decomposition
# ---------------------------------------------------------------------------

class TestTaskDecomposition:
    """MissionTask e TaskDecomposition."""

    def test_create_default_generates_five_tasks(self):
        td = TaskDecomposition.create_default("mis-001")
        assert len(td.tasks) == 5
        types = [t.type for t in td.tasks]
        assert types == [TaskType.PLANNING, TaskType.MEMORY, TaskType.EXECUTION, TaskType.REVIEW, TaskType.REPORT]

    def test_default_dependencies(self):
        td = TaskDecomposition.create_default("mis-001")
        by_id = {t.id: t for t in td.tasks}
        pid = "mis-001-planning"
        mid = "mis-001-memory"
        eid = "mis-001-execution"
        rid = "mis-001-review"
        rpid = "mis-001-report"

        assert by_id[pid].depends_on == []
        assert by_id[mid].depends_on == [pid]
        assert by_id[eid].depends_on == [pid, mid]
        assert by_id[rid].depends_on == [eid]
        assert by_id[rpid].depends_on == [rid]

    def test_mission_task_is_frozen(self):
        t = MissionTask(id="t1", type=TaskType.PLANNING)
        with pytest.raises(ValidationError):
            t.status = TaskStatus.COMPLETED

    def test_mission_task_defaults(self):
        t = MissionTask(id="t1", type=TaskType.EXECUTION)
        assert t.status == TaskStatus.PENDING
        assert t.description == ""
        assert t.assignee == ""
        assert t.depends_on == []
        assert t.artifacts == []
        assert t.estimated_tokens == 0

    def test_task_type_enum_values(self):
        assert {t.value for t in TaskType} == {"planning", "memory", "execution", "review", "report"}

    def test_task_status_enum_values(self):
        assert {s.value for s in TaskStatus} == {"pending", "in_progress", "completed", "failed", "skipped"}


# ---------------------------------------------------------------------------
# Mission Package serialization
# ---------------------------------------------------------------------------

class TestMissionPackage:
    """MissionPackage wrapper round-trip."""

    def test_package_creation(self, sample_contract):
        td = TaskDecomposition.create_default(sample_contract.mission_id)
        mem = MockMemoryLookup().lookup(sample_contract.objective)
        cost = MockCostTracker().estimate(sample_contract.mission_id, len(td.tasks), 0)
        pkg = MissionPackage(contract=sample_contract, plan=td, memory=mem, cost=cost, event_count=3)
        assert pkg.contract == sample_contract
        assert pkg.plan == td
        assert pkg.memory.source == "unknown"
        assert pkg.cost.estimated_cost == 0.0
        assert pkg.event_count == 3

    def test_package_summary(self, sample_contract):
        td = TaskDecomposition.create_default(sample_contract.mission_id)
        mem = MockMemoryLookup().lookup(sample_contract.objective)
        cost = MockCostTracker().estimate(sample_contract.mission_id, len(td.tasks), 0)
        pkg = MissionPackage(contract=sample_contract, plan=td, memory=mem, cost=cost, event_count=1)
        s = pkg.summary()
        assert s["mission_id"] == sample_contract.mission_id
        assert s["title"] == sample_contract.title
        assert s["task_count"] == 5
        assert s["memory_source"] == "unknown"
        assert s["cost_estimate"] == 0.0
        assert s["event_count"] == 1

    def test_package_serialization_roundtrip(self, sample_contract):
        td = TaskDecomposition.create_default(sample_contract.mission_id)
        mem = MockMemoryLookup().lookup(sample_contract.objective)
        cost = MockCostTracker().estimate(sample_contract.mission_id, len(td.tasks), 0)
        pkg = MissionPackage(contract=sample_contract, plan=td, memory=mem, cost=cost)

        data = pkg.model_dump_json()
        restored = MissionPackage.model_validate_json(data)

        assert restored.contract.title == sample_contract.title
        assert restored.contract.mission_id == sample_contract.mission_id
        assert len(restored.plan.tasks) == 5
        assert restored.memory.source == "unknown"
        assert restored.cost.estimated_cost == 0.0

    def test_package_defaults(self, sample_contract):
        pkg = MissionPackage(contract=sample_contract)
        assert pkg.event_count == 0
        assert len(pkg.plan.tasks) == 0
        assert pkg.memory.source == "unknown"


# ---------------------------------------------------------------------------
# Integration smoke test
# ---------------------------------------------------------------------------

class TestEndToEndMissionPackage:
    """Cria mission → package → valida."""

    def test_full_flow(self, tmp_repo, sample_contract_full):
        # 1. Save contract
        c = sample_contract_full
        mid = tmp_repo.save_contract(c)

        # 2. Emit lifecycle events
        events = [
            ("mission_created", {}),
            ("mission_planned", {"plan_id": "plan-1", "task_count": 5}),
            ("mission_started", {}),
            ("mission_completed", {"result": "success"}),
        ]
        for etype, payload in events:
            tmp_repo.append_event(EventEnvelope(
                mission_id=mid, event_type=etype, sequence=0, actor="test", payload=payload,
            ))

        # 3. Project state
        state = tmp_repo.project(mid)
        assert state.status == MissionStatus.COMPLETED

        # 4. Build MissionPackage
        contract = tmp_repo.get_contract(mid)
        td = TaskDecomposition.create_default(mid)
        mem = MockMemoryLookup().lookup(contract.objective)
        cost = MockCostTracker().estimate(mid, len(td.tasks), 0)
        stored_events = tmp_repo.get_events(mid)

        pkg = MissionPackage(contract=contract, plan=td, memory=mem, cost=cost, event_count=len(stored_events))

        # 5. Validate
        assert pkg.contract.title == c.title
        assert pkg.contract.priority == c.priority
        assert len(pkg.plan.tasks) == 5
        assert pkg.memory.source == "unknown"
        assert pkg.cost.estimated_cost == 0.0
        assert pkg.event_count == 4

        # 6. Serialization round-trip
        serialized = pkg.model_dump_json()
        restored = MissionPackage.model_validate_json(serialized)
        assert restored.summary() == pkg.summary()
