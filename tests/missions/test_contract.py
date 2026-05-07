"""Testes de imutabilidade e criação do MissionContract."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.missions.models import (
    MissionContract,
    BudgetCaps,
    AcceptanceCriterion,
    RiskLevel,
    ApprovalPolicy,
    Sector,
)


class TestMissionContractImmutability:
    """MissionContract é frozen — atribuições diretas devem falhar."""

    def test_setattr_raises(self, sample_contract):
        with pytest.raises(ValidationError):
            sample_contract.title = "Novo título"

    def test_setattr_new_field_raises(self, sample_contract):
        """extra='forbid' bloqueia campos novos."""
        with pytest.raises(ValidationError):
            MissionContract(
                title="X",
                objective="Y",
                sector=Sector.RESEARCH,
                campo_inexistente=True,
            )

    def test_budget_caps_immutable(self):
        budget = BudgetCaps(max_tokens=100)
        with pytest.raises(ValidationError):
            budget.max_tokens = 200


class TestMissionContractCreation:
    """Criação com valores padrão e customizados."""

    def test_default_values(self):
        contract = MissionContract(
            title="Test",
            objective="Objective",
            sector=Sector.RESEARCH,
        )
        assert contract.title == "Test"
        assert contract.risk_level == RiskLevel.LOW
        assert contract.approval_policy == ApprovalPolicy.NONE
        assert contract.budget.max_tokens == 50000
        assert contract.budget.max_cost_usd == 2.0
        assert contract.budget.max_duration_seconds == 600
        assert contract.budget.max_steps == 50
        assert contract.parent_mission_id is None
        assert contract.deadline is None
        assert contract.tags == []
        assert contract.acceptance_criteria == []
        assert contract.expected_deliverables == []

    def test_custom_values(self, sample_contract_full):
        assert sample_contract_full.title == "Full Mission"
        assert sample_contract_full.sector == Sector.SALES
        assert sample_contract_full.budget.max_tokens == 1000
        assert len(sample_contract_full.acceptance_criteria) == 1
        assert sample_contract_full.expected_deliverables == ["report.md"]
        assert sample_contract_full.tags == ["test", "critical"]

    def test_user_request_falls_back_to_objective_in_cli(self):
        """CLI trata fallback — no modelo, user_request pode ser vazio."""
        contract = MissionContract(
            title="T",
            objective="Obj",
            sector=Sector.OPERATIONS,
        )
        # user_request stays empty str — CLI é responsável pelo fallback
        assert contract.user_request == ""

    def test_all_sectors_valid(self):
        for s in Sector:
            contract = MissionContract(
                title=f"Mission {s.value}",
                objective="Test all sectors",
                sector=s,
            )
            assert contract.sector == s

    def test_created_at_is_utc(self):
        contract = MissionContract(
            title="T", objective="O", sector=Sector.AUTOMATION,
        )
        assert contract.created_at.tzinfo is not None
