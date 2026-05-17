"""Frontend plan generator for W135."""
from __future__ import annotations

from dataclasses import dataclass

from src.app_factory.api_contract import APIContract
from src.app_factory.models import AppBlueprint


@dataclass(frozen=True)
class FrontendPlan:
    blueprint_id: str
    routes: list[dict]
    components: list[dict]
    states: list[dict]
    user_flows: list[dict]
    dry_run: bool = True

    def to_dict(self) -> dict:
        return self.__dict__


def build_frontend_plan(
    blueprint: AppBlueprint,
    api_contract: APIContract,
    dry_run: bool = True,
) -> FrontendPlan:
    routes = [{"path": "/", "screen": "HomeScreen"}]
    components = list(_flatten_components(blueprint.component_tree))
    states = [{"name": "loading", "type": "boolean"}, {"name": "error", "type": "nullable_error"}]
    flows = [{"name": "open_app", "steps": ["/", "load_initial_data"]}]

    entities = sorted({_entity_from_path(endpoint.path) for endpoint in api_contract.endpoints})
    for entity in entities:
        if entity == "resource":
            continue
        title = entity.capitalize()
        routes.extend([
            {"path": f"/{entity}s", "screen": f"{title}ListScreen"},
            {"path": f"/{entity}s/:id", "screen": f"{title}DetailScreen"},
        ])
        components.extend([
            {"name": f"{title}List", "purpose": f"Render {entity} collection"},
            {"name": f"{title}Form", "purpose": f"Create or update {entity}"},
        ])
        states.append({"name": f"{entity}s", "type": "collection"})
        flows.append({"name": f"manage_{entity}", "steps": [f"/{entity}s", "select_or_create", "save"]})

    return FrontendPlan(
        blueprint_id=blueprint.blueprint_id,
        routes=_dedupe_dicts(routes),
        components=_dedupe_dicts(components),
        states=_dedupe_dicts(states),
        user_flows=flows,
        dry_run=dry_run,
    )


def _flatten_components(tree: dict) -> list[dict]:
    found: list[dict] = []
    for item in tree.get("components", []):
        found.append({"name": item["name"], "purpose": "UI component"})
        found.extend(_flatten_components(item))
    for item in tree.get("children", []):
        found.append({"name": item["name"], "purpose": "UI component"})
        found.extend(_flatten_components(item))
    return found


def _entity_from_path(path: str) -> str:
    parts = [part for part in path.split("/") if part and not part.startswith("{")]
    if len(parts) >= 2 and parts[0] == "api":
        return parts[1].removesuffix("s")
    return "resource"


def _dedupe_dicts(items: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    result: list[dict] = []
    for item in items:
        key = tuple(sorted(item.items()))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
