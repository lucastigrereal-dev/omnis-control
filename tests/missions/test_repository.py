"""Testes do JsonlRepository: CRUD, hash, events, sequence, projection."""
from __future__ import annotations

import pytest

from src.missions.events import EventEnvelope
from src.missions.models import MissionContract, Sector
from src.missions.repository import (
    JsonlRepository,
    ContractTamperedError,
    SequenceGapError,
)


class TestSaveAndGetContract:
    """Save + load com hash verification."""

    def test_save_and_get(self, tmp_repo, sample_contract):
        mission_id = tmp_repo.save_contract(sample_contract)
        loaded = tmp_repo.get_contract(mission_id)
        assert loaded.title == sample_contract.title
        assert loaded.objective == sample_contract.objective
        assert loaded.sector == sample_contract.sector
        assert loaded.content_hash() == mission_id

    def test_save_creates_hash_file(self, tmp_repo, sample_contract):
        mission_id = tmp_repo.save_contract(sample_contract)
        hash_path = tmp_repo.contracts_dir / f"{mission_id}.hash"
        assert hash_path.exists()

    def test_save_creates_index(self, tmp_repo, sample_contract):
        tmp_repo.save_contract(sample_contract)
        assert tmp_repo.index_path.exists()

    def test_contract_tampered_detected(self, tmp_repo, sample_contract):
        mission_id = tmp_repo.save_contract(sample_contract)
        contract_path = tmp_repo.contracts_dir / f"{mission_id}.json"
        # Corrompe o arquivo
        contract_path.write_text("corrupted data", encoding="utf-8")
        with pytest.raises(ContractTamperedError):
            tmp_repo.get_contract(mission_id)

    def test_contract_not_found(self, tmp_repo):
        with pytest.raises(FileNotFoundError):
            tmp_repo.get_contract("nonexistent")


class TestAppendEvent:
    """Append de eventos com cálculo cumulative + validação de sequence."""

    def test_append_first_event(self, tmp_repo, sample_contract):
        mission_id = tmp_repo.save_contract(sample_contract)
        event = EventEnvelope(
            mission_id=mission_id,
            event_type="mission_started",
            sequence=0,  # repo calcula
            actor="test",
        )
        appended = tmp_repo.append_event(event)
        assert appended.sequence == 1
        assert appended.cumulative_tokens == 0
        assert appended.cumulative_cost_usd == 0.0

    def test_append_second_event(self, tmp_repo, sample_contract):
        mission_id = tmp_repo.save_contract(sample_contract)
        e1 = tmp_repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_started", sequence=0, actor="test",
        ))
        e2 = tmp_repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_completed", sequence=0, actor="test",
        ))
        assert e2.sequence == 2

    def test_sequence_gap_rejected(self, tmp_repo, sample_contract):
        mission_id = tmp_repo.save_contract(sample_contract)
        tmp_repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_started", sequence=0, actor="test",
        ))
        with pytest.raises(SequenceGapError):
            tmp_repo.append_event(EventEnvelope(
                mission_id=mission_id, event_type="mission_completed", sequence=5, actor="test",
            ))

    def test_cumulative_calculation(self, tmp_repo, sample_contract):
        mission_id = tmp_repo.save_contract(sample_contract)
        e1 = tmp_repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="token_used", sequence=0, actor="test",
            delta_tokens=500, delta_cost_usd=0.05,
        ))
        assert e1.cumulative_tokens == 500
        assert e1.cumulative_cost_usd == 0.05

        e2 = tmp_repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="token_used", sequence=0, actor="test",
            delta_tokens=300, delta_cost_usd=0.03,
        ))
        assert e2.cumulative_tokens == 800
        assert e2.cumulative_cost_usd == 0.08

    def test_index_updated_on_event(self, tmp_repo, sample_contract):
        mission_id = tmp_repo.save_contract(sample_contract)
        tmp_repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_started", sequence=0, actor="test",
        ))
        missions = tmp_repo.list_missions()
        assert any(m.mission_id == mission_id and m.status.value == "running" for m in missions)


class TestGetEvents:
    """Leitura de eventos."""

    def test_empty_events(self, tmp_repo, sample_contract):
        mission_id = tmp_repo.save_contract(sample_contract)
        events = tmp_repo.get_events(mission_id)
        assert events == []

    def test_returns_ordered_events(self, tmp_repo, sample_contract):
        mission_id = tmp_repo.save_contract(sample_contract)
        for i in range(5):
            tmp_repo.append_event(EventEnvelope(
                mission_id=mission_id, event_type="token_used", sequence=0, actor="test",
            ))
        events = tmp_repo.get_events(mission_id)
        assert len(events) == 5
        assert events[0].sequence == 1
        assert events[4].sequence == 5


class TestProject:
    """Projeção via repository."""

    def test_project_draft(self, tmp_repo, sample_contract):
        mission_id = tmp_repo.save_contract(sample_contract)
        state = tmp_repo.project(mission_id)
        assert state.status.value == "draft"

    def test_project_after_events(self, tmp_repo, sample_contract):
        mission_id = tmp_repo.save_contract(sample_contract)
        tmp_repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_started", sequence=0, actor="test",
        ))
        tmp_repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_completed", sequence=0, actor="test",
        ))
        state = tmp_repo.project(mission_id)
        assert state.status.value == "completed"


class TestListMissions:
    """Listagem de missions."""

    def test_empty_list(self, tmp_repo):
        missions = tmp_repo.list_missions()
        assert missions == []

    def test_list_with_missions(self, tmp_repo):
        c1 = MissionContract(title="M1", objective="O1", sector=Sector.RESEARCH)
        c2 = MissionContract(title="M2", objective="O2", sector=Sector.SALES)
        id1 = tmp_repo.save_contract(c1)
        id2 = tmp_repo.save_contract(c2)
        tmp_repo.append_event(EventEnvelope(
            mission_id=id1, event_type="mission_started", sequence=0, actor="test",
        ))
        missions = tmp_repo.list_missions()
        assert len(missions) == 2

    def test_list_filtered_by_status(self, tmp_repo):
        c = MissionContract(title="M", objective="O", sector=Sector.RESEARCH)
        mid = tmp_repo.save_contract(c)
        tmp_repo.append_event(EventEnvelope(
            mission_id=mid, event_type="mission_started", sequence=0, actor="test",
        ))
        running = tmp_repo.list_missions(status="running")
        draft = tmp_repo.list_missions(status="draft")
        assert len(running) == 1
        assert len(draft) == 0
