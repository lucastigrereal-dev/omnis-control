"""Fixtures compartilhadas para tests/missions/."""
from __future__ import annotations

import pytest

from src.missions.models import (
    MissionContract,
    BudgetCaps,
    AcceptanceCriterion,
    Sector,
)
from src.missions.events import EventEnvelope
from src.missions.repository import JsonlRepository


@pytest.fixture
def sample_contract() -> MissionContract:
    return MissionContract(
        title="Test Mission",
        objective="Verificar que o sistema funciona",
        sector=Sector.RESEARCH,
        user_request="Criar testes para o sistema",
    )


@pytest.fixture
def sample_contract_full() -> MissionContract:
    return MissionContract(
        title="Full Mission",
        objective="Testar budget enforcement e approval flow",
        sector=Sector.SALES,
        user_request="Testar budget enforcement",
        budget=BudgetCaps(max_tokens=1000, max_cost_usd=1.0, max_duration_seconds=300, max_steps=10),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC-001", description="Test passes"),
        ],
        expected_deliverables=["report.md"],
        tags=["test", "critical"],
    )


@pytest.fixture
def mission_created_event(sample_contract) -> EventEnvelope:
    return EventEnvelope(
        mission_id=sample_contract.content_hash(),
        event_type="mission_created",
        sequence=1,
        actor="test",
        actor_detail="pytest",
    )


@pytest.fixture
def tmp_repo(tmp_path) -> JsonlRepository:
    return JsonlRepository(base_dir=str(tmp_path / "missions"))
