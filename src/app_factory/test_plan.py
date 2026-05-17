"""Test plan generator for W136."""
from __future__ import annotations

from dataclasses import dataclass

from src.app_factory.api_contract import APIContract
from src.app_factory.frontend_plan import FrontendPlan
from src.app_factory.schema_planner import SchemaPlan


@dataclass(frozen=True)
class AppTestPlan:
    blueprint_id: str
    unit_tests: list[str]
    integration_tests: list[str]
    contract_tests: list[str]
    e2e_smoke: list[str]
    edge_cases: list[str]
    fixtures: list[str]
    acceptance_criteria: list[str]
    dry_run: bool = True

    def to_dict(self) -> dict:
        return self.__dict__


def build_test_plan(
    schema_plan: SchemaPlan,
    api_contract: APIContract,
    frontend_plan: FrontendPlan,
    dry_run: bool = True,
) -> AppTestPlan:
    tables = [table.name for table in schema_plan.tables]
    endpoint_names = [f"{ep.method} {ep.path}" for ep in api_contract.endpoints]
    route_names = [route["path"] for route in frontend_plan.routes]
    return AppTestPlan(
        blueprint_id=schema_plan.blueprint_id,
        unit_tests=[f"validate {table} model fields" for table in tables],
        integration_tests=[f"persist and retrieve {table}" for table in tables],
        contract_tests=[f"contract for {endpoint}" for endpoint in endpoint_names],
        e2e_smoke=[f"open route {route}" for route in route_names],
        edge_cases=["empty payload", "missing id", "duplicate unique field", "unicode input"],
        fixtures=[f"{table}_fixture" for table in tables],
        acceptance_criteria=[
            "all generated plans are deterministic",
            "no external API calls are required",
            "dry_run remains true by default",
        ],
        dry_run=dry_run,
    )
