"""API contract builder for W134."""
from __future__ import annotations

from dataclasses import dataclass

from src.app_factory.models import AppBlueprint
from src.app_factory.schema_planner import SchemaPlan


@dataclass(frozen=True)
class APIEndpointContract:
    method: str
    path: str
    description: str
    request: dict
    response: dict
    errors: list[dict]


@dataclass(frozen=True)
class APIContract:
    blueprint_id: str
    endpoints: list[APIEndpointContract]
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "blueprint_id": self.blueprint_id,
            "dry_run": self.dry_run,
            "endpoints": [endpoint.__dict__ for endpoint in self.endpoints],
        }


def build_api_contract(
    blueprint: AppBlueprint,
    schema_plan: SchemaPlan,
    dry_run: bool = True,
) -> APIContract:
    table_names = {table.name for table in schema_plan.tables}
    endpoints: list[APIEndpointContract] = []

    for endpoint in blueprint.api_endpoints:
        entity = _entity_from_path(endpoint["path"])
        response_model = entity if f"{entity}s" in table_names else "resource"
        endpoints.append(
            APIEndpointContract(
                method=endpoint["method"],
                path=endpoint["path"],
                description=endpoint["description"],
                request=_request_for(endpoint["method"], response_model),
                response={"status": _status_for(endpoint["method"]), "model": response_model},
                errors=[
                    {"status": 400, "code": "validation_error"},
                    {"status": 404, "code": "not_found"},
                    {"status": 500, "code": "internal_error"},
                ],
            )
        )

    return APIContract(blueprint_id=blueprint.blueprint_id, endpoints=endpoints, dry_run=dry_run)


def _entity_from_path(path: str) -> str:
    parts = [part for part in path.split("/") if part and not part.startswith("{")]
    if len(parts) >= 2 and parts[0] == "api":
        return parts[1].removesuffix("s")
    return "resource"


def _request_for(method: str, model: str) -> dict:
    if method in {"POST", "PUT", "PATCH"}:
        return {"body": model, "content_type": "application/json"}
    return {"params": {}}


def _status_for(method: str) -> int:
    return {"POST": 201, "DELETE": 204}.get(method, 200)
