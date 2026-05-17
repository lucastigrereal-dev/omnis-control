"""W177 — Config Validator: validates module configs against schemas before applying."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union

from src.remote_control.models import _new_id, _now_iso


class FieldType(str, Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"


# ---------------------------------------------------------------------------
# Schema field
# ---------------------------------------------------------------------------

@dataclass
class FieldSchema:
    name: str
    field_type: FieldType
    required: bool = True
    default: Any = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    allowed_values: Optional[list] = None
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "field_type": self.field_type.value,
            "required": self.required,
            "default": self.default,
            "min_val": self.min_val,
            "max_val": self.max_val,
            "allowed_values": self.allowed_values,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FieldSchema":
        return cls(
            name=d.get("name", ""),
            field_type=FieldType(d.get("field_type", "string")),
            required=d.get("required", True),
            default=d.get("default"),
            min_val=d.get("min_val"),
            max_val=d.get("max_val"),
            allowed_values=d.get("allowed_values"),
            description=d.get("description", ""),
        )


# ---------------------------------------------------------------------------
# Config schema
# ---------------------------------------------------------------------------

@dataclass
class ConfigSchema:
    name: str
    fields: list[FieldSchema] = field(default_factory=list)
    version: str = "1.0"

    def add_field(self, field_schema: FieldSchema) -> "ConfigSchema":
        self.fields.append(field_schema)
        return self

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "fields": [f.to_dict() for f in self.fields],
        }


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

@dataclass
class ConfigValidationResult:
    result_id: str = field(default_factory=lambda: _new_id("cvr"))
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    applied: dict = field(default_factory=dict)
    validated_at: str = field(default_factory=_now_iso)

    def fail(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "applied": self.applied,
            "validated_at": self.validated_at,
        }


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

_TYPE_CHECKERS: dict[FieldType, type] = {
    FieldType.STRING: str,
    FieldType.INT: int,
    FieldType.FLOAT: (int, float),
    FieldType.BOOL: bool,
    FieldType.LIST: list,
    FieldType.DICT: dict,
}


class ConfigValidator:
    """Validates and coerces module config dicts against ConfigSchema."""

    def __init__(self, schema: ConfigSchema) -> None:
        self.schema = schema

    def validate(self, config: dict) -> ConfigValidationResult:
        result = ConfigValidationResult()
        applied = dict(config)

        for field_schema in self.schema.fields:
            name = field_schema.name
            present = name in config

            if not present:
                if field_schema.required and field_schema.default is None:
                    result.fail(f"missing_required_field:{name}")
                    continue
                # Apply default
                val = field_schema.default
                if val is not None:
                    applied[name] = val
                    result.warn(f"default_applied:{name}={val}")
                continue

            val = config[name]

            # Type check (bool must come before int since bool is subclass of int)
            if field_schema.field_type == FieldType.BOOL:
                if not isinstance(val, bool):
                    result.fail(f"type_error:{name} expected bool got {type(val).__name__}")
                    continue
            elif field_schema.field_type == FieldType.INT:
                if isinstance(val, bool) or not isinstance(val, int):
                    result.fail(f"type_error:{name} expected int got {type(val).__name__}")
                    continue
            else:
                expected = _TYPE_CHECKERS.get(field_schema.field_type)
                if expected and not isinstance(val, expected):
                    result.fail(f"type_error:{name} expected {field_schema.field_type.value} got {type(val).__name__}")
                    continue

            # Range check
            if field_schema.min_val is not None and isinstance(val, (int, float)) and val < field_schema.min_val:
                result.fail(f"range_error:{name} value {val} < min {field_schema.min_val}")
                continue
            if field_schema.max_val is not None and isinstance(val, (int, float)) and val > field_schema.max_val:
                result.fail(f"range_error:{name} value {val} > max {field_schema.max_val}")
                continue

            # Allowed values
            if field_schema.allowed_values is not None and val not in field_schema.allowed_values:
                result.fail(f"invalid_value:{name} {val!r} not in {field_schema.allowed_values}")
                continue

            applied[name] = val

        result.applied = applied
        return result

    def validate_many(self, configs: list[dict]) -> list[ConfigValidationResult]:
        return [self.validate(c) for c in configs]
