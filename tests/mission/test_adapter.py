"""Testes do MissionToWorkOrderAdapter."""
from __future__ import annotations

import json
from pathlib import Path

from src.mission.adapter import MissionToWorkOrderAdapter
from src.mission_builder.models import MissionPlan
from src.missions.models import (
    MissionContract,
    Sector,
    RiskLevel,
    BudgetCaps,
    AcceptanceCriterion,
)


class TestAdapterPlanToWorkOrders:
    def test_creates_work_orders_from_steps(self, tmp_path: Path):
        adapter = MissionToWorkOrderAdapter(work_orders_root=tmp_path / "work_orders")
        plan = MissionPlan.new(
            request_text="Criar 3 carrosséis",
            intent="carousel",
            deliverable="carousel_package",
            description="Carrosséis sobre Natal/RN",
            account_handle="@lucastigrereal",
            format="carrossel",
            objective="engajar",
            estimated_slots=3,
            steps=["step_carousel_1", "step_carousel_2", "step_carousel_3"],
        )
        wos = adapter.plan_to_work_orders(plan)
        assert len(wos) == 3
        for wo in wos:
            assert wo["work_order_id"].startswith("wo_")
            assert wo["status"] == "draft"
            assert len(wo["contracts"]) == 3
            assert wo["metadata"]["mission_id"] == plan.mission_id

    def test_creates_work_orders_without_steps(self, tmp_path: Path):
        adapter = MissionToWorkOrderAdapter(work_orders_root=tmp_path / "work_orders")
        plan = MissionPlan.new(
            request_text="Criar reels",
            intent="reels",
            deliverable="reels_package",
            description="Reels viagem",
            account_handle="@lucastigrereal",
            format="reels",
            objective="engajar",
            estimated_slots=5,
        )
        wos = adapter.plan_to_work_orders(plan)
        assert len(wos) == 5

    def test_write_work_orders_writes_files(self, tmp_path: Path):
        adapter = MissionToWorkOrderAdapter(work_orders_root=tmp_path / "work_orders")
        wos = [
            {
                "work_order_id": "wo_test_01",
                "graph_step_id": "step_000",
                "graph_run_id": "run_001",
                "role": "test",
                "step_label": "test_step",
                "status": "draft",
                "contracts": [
                    {
                        "contract_id": "ctr_01",
                        "output_type": "markdown",
                        "description": "MD output",
                        "required": True,
                        "min_count": 1,
                        "max_count": 1,
                    }
                ],
                "outputs": [],
                "approval_id": None,
                "created_at": "2026-05-12T00:00:00Z",
                "updated_at": "2026-05-12T00:00:00Z",
                "metadata": {},
            }
        ]
        paths = adapter.write_work_orders(wos)
        assert len(paths) == 1
        wo_file = tmp_path / "work_orders" / "wo_test_01" / "work_order.json"
        assert wo_file.exists()
        data = json.loads(wo_file.read_text(encoding="utf-8"))
        assert data["work_order_id"] == "wo_test_01"

    def test_execute_work_order_via_p10(self, tmp_path: Path):
        work_root = tmp_path / "work_orders"
        out_root = tmp_path / "outputs"
        adapter = MissionToWorkOrderAdapter(work_orders_root=work_root)

        wo_id = "wo_exec_01"
        wo = {
            "work_order_id": wo_id,
            "graph_step_id": "step_000",
            "graph_run_id": "run_001",
            "role": "test",
            "step_label": "Test Execution",
            "status": "draft",
            "contracts": [
                {
                    "contract_id": f"ctr_{wo_id}_md",
                    "output_type": "markdown",
                    "description": "Markdown output for test",
                    "required": True,
                    "min_count": 1,
                    "max_count": 1,
                },
                {
                    "contract_id": f"ctr_{wo_id}_json",
                    "output_type": "json",
                    "description": "JSON output for test",
                    "required": True,
                    "min_count": 1,
                    "max_count": 1,
                },
                {
                    "contract_id": f"ctr_{wo_id}_csv",
                    "output_type": "csv",
                    "description": "CSV output for test",
                    "required": True,
                    "min_count": 1,
                    "max_count": 1,
                },
            ],
            "outputs": [],
            "approval_id": None,
            "created_at": "2026-05-12T00:00:00Z",
            "updated_at": "2026-05-12T00:00:00Z",
            "metadata": {},
        }
        adapter.write_work_orders([wo])

        result = adapter.execute_work_order(wo_id, outputs_root=out_root)
        assert result["work_order_id"] == wo_id
        assert result["valid"] is True
        assert result["registered"] >= 1


class TestAdapterContractToWorkOrders:
    def test_creates_work_orders_from_contract(self, tmp_path: Path):
        adapter = MissionToWorkOrderAdapter(work_orders_root=tmp_path / "work_orders")
        contract = MissionContract(
            title="Campanha Natal",
            objective="5 carrosséis Natal/RN",
            sector=Sector.MARKETING,
            risk_level=RiskLevel.LOW,
            expected_deliverables=["carrossel_1", "carrossel_2"],
            acceptance_criteria=[
                AcceptanceCriterion(
                    id="ac_1",
                    description="Imagens em 1080x1080",
                    check_type="auto",
                    required=True,
                )
            ],
            budget=BudgetCaps(max_tokens=10000),
        )
        wos = adapter.contract_to_work_orders(contract)
        assert len(wos) == 2
        assert wos[0]["step_label"] == "carrossel_1"
        assert wos[1]["step_label"] == "carrossel_2"
        for wo in wos:
            assert len(wo["contracts"]) == 3

    def test_contract_without_deliverables_generates_one_wo(self, tmp_path: Path):
        adapter = MissionToWorkOrderAdapter(work_orders_root=tmp_path / "work_orders")
        contract = MissionContract(
            title="Test",
            objective="Test",
            sector=Sector.RESEARCH,
        )
        wos = adapter.contract_to_work_orders(contract)
        assert len(wos) == 1
        assert wos[0]["step_label"] == "mission_output"
