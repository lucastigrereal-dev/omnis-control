"""Testes de budget enforcement — contratos e estouro."""
from __future__ import annotations

import pytest

from src.missions.models import MissionContract, BudgetCaps, Sector
from src.missions.events import EventEnvelope
from src.missions.state import project_from_events
from src.missions.state_machine import MissionStatus


class TestBudgetCapsModel:
    """Modelo BudgetCaps — validação e defaults."""

    def test_default_budget(self):
        budget = BudgetCaps()
        assert budget.max_tokens == 50000
        assert budget.max_cost_usd == 2.0
        assert budget.max_duration_seconds == 600
        assert budget.max_steps == 50

    def test_custom_budget(self):
        budget = BudgetCaps(max_tokens=100, max_cost_usd=0.50, max_duration_seconds=30, max_steps=5)
        assert budget.max_tokens == 100

    def test_budget_in_contract(self):
        contract = MissionContract(
            title="Budget Test",
            objective="Verificar budget no contract",
            sector=Sector.FINANCE,
            budget=BudgetCaps(max_tokens=500, max_cost_usd=0.25),
        )
        assert contract.budget.max_tokens == 500
        assert contract.budget.max_cost_usd == 0.25


class TestBudgetExceededProjection:
    """Estouro de budget sempre vai para waiting_approval."""

    def test_budget_exceeded_no_approval_policy(self):
        """Mesmo com approval_policy=none, budget_exceeded trava."""
        contract = MissionContract(
            title="No Approval",
            objective="Test",
            sector=Sector.FINANCE,
        )
        mid = contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="budget_exceeded", sequence=2, actor="system",
                         payload={"limit": "max_cost_usd"}),
        ]
        state = project_from_events(contract, events)
        assert state.status == MissionStatus.WAITING_APPROVAL
        assert state.budget_exceeded is True

    def test_budget_exceeded_with_approval_policy_auto(self):
        """Mesmo com approval_policy=auto, budget_exceeded é trava dura."""
        contract = MissionContract(
            title="Auto Approval",
            objective="Test",
            sector=Sector.FINANCE,
            approval_policy="auto",  # type: ignore
        )
        mid = contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="budget_exceeded", sequence=2, actor="system"),
        ]
        state = project_from_events(contract, events)
        assert state.status == MissionStatus.WAITING_APPROVAL

    def test_budget_not_exceeded_normal_flow(self):
        contract = MissionContract(
            title="Normal Flow",
            objective="Test",
            sector=Sector.FINANCE,
        )
        mid = contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="mission_started", sequence=1, actor="test"),
            EventEnvelope(mission_id=mid, event_type="token_used", sequence=2, actor="test",
                         cumulative_tokens=100, cumulative_cost_usd=0.01),
            EventEnvelope(mission_id=mid, event_type="mission_completed", sequence=3, actor="test"),
        ]
        state = project_from_events(contract, events)
        assert state.status == MissionStatus.COMPLETED
        assert state.budget_exceeded is False
        assert state.cumulative_tokens == 100


class TestBudgetCumulativeTracking:
    """Cumulative tokens/cost tracking via eventos."""

    def test_cumulative_increases(self):
        contract = MissionContract(
            title="Cumulative Test",
            objective="Track cumulative",
            sector=Sector.RESEARCH,
        )
        mid = contract.content_hash()
        events = [
            EventEnvelope(mission_id=mid, event_type="token_used", sequence=1, actor="test",
                         delta_tokens=500, cumulative_tokens=500, cumulative_cost_usd=0.05),
            EventEnvelope(mission_id=mid, event_type="token_used", sequence=2, actor="test",
                         delta_tokens=300, cumulative_tokens=800, cumulative_cost_usd=0.08),
        ]
        state = project_from_events(contract, events)
        assert state.cumulative_tokens == 800
        assert state.cumulative_cost_usd == 0.08
