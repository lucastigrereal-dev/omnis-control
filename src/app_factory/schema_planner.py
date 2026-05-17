"""Database schema planner for W133."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.app_factory.models import AppBlueprint


@dataclass(frozen=True)
class SchemaField:
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    unique: bool = False
    required: bool = False


@dataclass(frozen=True)
class SchemaTable:
    name: str
    fields: list[SchemaField]
    relationships: list[dict] = field(default_factory=list)
    indexes: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class SchemaPlan:
    blueprint_id: str
    tables: list[SchemaTable]
    migrations_allowed: bool = False
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "blueprint_id": self.blueprint_id,
            "migrations_allowed": self.migrations_allowed,
            "dry_run": self.dry_run,
            "tables": [
                {
                    "name": table.name,
                    "fields": [field.__dict__ for field in table.fields],
                    "relationships": table.relationships,
                    "indexes": table.indexes,
                }
                for table in self.tables
            ],
        }


def build_schema_plan(blueprint: AppBlueprint, dry_run: bool = True) -> SchemaPlan:
    """Build a local deterministic schema plan from blueprint data models."""
    tables: list[SchemaTable] = []
    table_names = {model.get("table", "") for model in blueprint.data_models or []}
    for model in blueprint.data_models or []:
        fields = [
            SchemaField(
                name=field["name"],
                type=_normalize_type(field["type"]),
                nullable=field.get("nullable", True),
                primary_key=field.get("pk", False),
                unique=field.get("unique", False),
                required=not field.get("nullable", True) or field.get("pk", False),
            )
            for field in model.get("fields", [])
        ]
        relationships = list(model.get("relationships", []))
        indexes = []
        for field in fields:
            if field.primary_key or field.unique:
                indexes.append({"name": f"idx_{model['table']}_{field.name}", "fields": [field.name], "unique": field.unique})
            if field.name.endswith("_id") and not field.primary_key:
                target = f"{field.name.removesuffix('_id')}s"
                relation = {
                    "type": "foreign_key",
                    "field": field.name,
                    "references": target if target in table_names else "unknown",
                }
                relationships.append(relation)
                indexes.append({"name": f"idx_{model['table']}_{field.name}", "fields": [field.name], "unique": False})
        tables.append(
            SchemaTable(
                name=model["table"],
                fields=fields,
                relationships=relationships,
                indexes=indexes,
            )
        )

    if not tables:
        tables.append(
            SchemaTable(
                name="resources",
                fields=[
                    SchemaField("id", "uuid", nullable=False, primary_key=True),
                    SchemaField("created_at", "timestamp", nullable=False),
                    SchemaField("updated_at", "timestamp", nullable=False),
                ],
            )
        )

    return SchemaPlan(
        blueprint_id=blueprint.blueprint_id,
        tables=tables,
        migrations_allowed=False,
        dry_run=dry_run,
    )


def _normalize_type(value: str) -> str:
    mapping = {
        "UUID": "uuid",
        "datetime": "timestamp",
        "str": "text",
        "int": "integer",
        "bool": "boolean",
        "list": "jsonb",
        "dict": "jsonb",
        "array": "jsonb",
        "object": "jsonb",
        "json": "jsonb",
    }
    return mapping.get(value, value.lower())
