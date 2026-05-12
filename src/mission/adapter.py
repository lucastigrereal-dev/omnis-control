"""Mission → Work Order Adapter — transforms Mission entities into P10 Work Orders."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from src.mission_builder.models import MissionPlan
from src.missions.models import MissionContract


def _make_wo_id() -> str:
    return "wo_" + uuid.uuid4().hex[:10]


class MissionToWorkOrderAdapter:
    """Transforma MissionPlan/MissionContract em Work Orders para o P10.

    Gera dicionarios compativeis com WorkOrder.from_dict() do P10,
    escreve-os em disco no formato esperado por OutputWriterService,
    e delega a geracao de outputs ao P10 via orchestrate().
    """

    def __init__(self, work_orders_root: Path | None = None):
        self.work_orders_root = work_orders_root or Path("exports/work_orders")

    def plan_to_work_orders(self, plan: MissionPlan) -> list[dict]:
        """Converte MissionPlan em lista de Work Order dicts.

        Cada step do plano vira um WorkOrder. Se nao houver steps,
        gera estimated_slots WorkOrders a partir da intent/objetivo.
        """
        steps = plan.steps if plan.steps else [
            f"{plan.intent}_{i+1}" for i in range(max(plan.estimated_slots, 1))
        ]

        work_orders = []
        for i, step_label in enumerate(steps):
            wo_id = _make_wo_id()
            wo = {
                "work_order_id": wo_id,
                "graph_step_id": f"step_{i:03d}",
                "graph_run_id": plan.mission_id,
                "role": "mission_adapter",
                "step_label": step_label,
                "status": "draft",
                "contracts": [
                    {
                        "contract_id": f"ctr_{wo_id}_md",
                        "output_type": "markdown",
                        "description": f"Markdown output for {step_label}",
                        "required": True,
                        "min_count": 1,
                        "max_count": 1,
                    },
                    {
                        "contract_id": f"ctr_{wo_id}_json",
                        "output_type": "json",
                        "description": f"JSON output for {step_label}",
                        "required": True,
                        "min_count": 1,
                        "max_count": 1,
                    },
                    {
                        "contract_id": f"ctr_{wo_id}_csv",
                        "output_type": "csv",
                        "description": f"CSV output for {step_label}",
                        "required": True,
                        "min_count": 1,
                        "max_count": 1,
                    },
                ],
                "outputs": [],
                "approval_id": None,
                "created_at": plan.created_at,
                "updated_at": plan.created_at,
                "metadata": {
                    "mission_id": plan.mission_id,
                    "account_handle": plan.account_handle,
                    "intent": plan.intent,
                    "deliverable": plan.deliverable,
                },
            }
            work_orders.append(wo)

        return work_orders

    def contract_to_work_orders(self, contract: MissionContract) -> list[dict]:
        """Converte MissionContract em Work Order dicts.

        Cada expected_deliverable vira um WorkOrder. Se nao houver
        deliverables, gera 1 WorkOrder generica.
        """
        deliverables = contract.expected_deliverables or ["mission_output"]

        work_orders = []
        for i, deliverable in enumerate(deliverables):
            wo_id = _make_wo_id()
            wo = {
                "work_order_id": wo_id,
                "graph_step_id": f"step_{i:03d}",
                "graph_run_id": f"ctr_{contract.content_hash()[:12]}",
                "role": "mission_adapter",
                "step_label": deliverable,
                "status": "draft",
                "contracts": [
                    {
                        "contract_id": f"ctr_{wo_id}_md",
                        "output_type": "markdown",
                        "description": f"Markdown output for {deliverable}",
                        "required": True,
                        "min_count": 1,
                        "max_count": 1,
                    },
                    {
                        "contract_id": f"ctr_{wo_id}_json",
                        "output_type": "json",
                        "description": f"JSON output for {deliverable}",
                        "required": True,
                        "min_count": 1,
                        "max_count": 1,
                    },
                    {
                        "contract_id": f"ctr_{wo_id}_csv",
                        "output_type": "csv",
                        "description": f"CSV output for {deliverable}",
                        "required": True,
                        "min_count": 1,
                        "max_count": 1,
                    },
                ],
                "outputs": [],
                "approval_id": None,
                "created_at": contract.created_at.isoformat() if hasattr(contract.created_at, "isoformat") else str(contract.created_at),
                "updated_at": contract.created_at.isoformat() if hasattr(contract.created_at, "isoformat") else str(contract.created_at),
                "metadata": {
                    "sector": contract.sector.value if hasattr(contract.sector, "value") else str(contract.sector),
                    "risk_level": contract.risk_level.value if hasattr(contract.risk_level, "value") else str(contract.risk_level),
                    "objective": contract.objective,
                },
            }
            work_orders.append(wo)

        return work_orders

    def write_work_orders(self, work_orders: list[dict]) -> list[Path]:
        """Escreve Work Order dicts em disco no formato P10.

        Retorna lista de paths para os diretorios criados.
        """
        paths = []
        for wo in work_orders:
            wo_dir = self.work_orders_root / wo["work_order_id"]
            wo_dir.mkdir(parents=True, exist_ok=True)
            manifest = wo_dir / "work_order.json"
            manifest.write_text(
                json.dumps(wo, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            paths.append(wo_dir)
        return paths

    def execute_work_order(self, work_order_id: str, outputs_root: Path | None = None) -> dict:
        """Delega um WorkOrder ao P10 OutputWriterService.orchestrate().

        Esta e a UNICA chamada ao P10. Nao reimplementa writers internos.
        """
        from src.output_generator.writer_service import OutputWriterService
        from src.output_generator.manifest_registry import ManifestRegistry

        svc = OutputWriterService(
            work_orders_root=self.work_orders_root,
            outputs_root=outputs_root or Path("exports/generated_outputs"),
            manifest_registry=ManifestRegistry(
                registry_path=(outputs_root or Path("exports/generated_outputs")) / "output_registry.jsonl"
            ),
        )
        return svc.orchestrate(work_order_id)
