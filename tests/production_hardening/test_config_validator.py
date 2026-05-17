"""W177 — Tests for ConfigValidator."""
import pytest
from src.production_hardening.config_validator import (
    ConfigSchema,
    ConfigValidationResult,
    ConfigValidator,
    FieldSchema,
    FieldType,
)


def _schema(*fields: FieldSchema) -> ConfigSchema:
    s = ConfigSchema(name="test")
    for f in fields:
        s.add_field(f)
    return s


def _str(name: str, required: bool = True, default=None, allowed=None) -> FieldSchema:
    return FieldSchema(name=name, field_type=FieldType.STRING, required=required, default=default, allowed_values=allowed)


def _int(name: str, min_val=None, max_val=None, required: bool = True) -> FieldSchema:
    return FieldSchema(name=name, field_type=FieldType.INT, required=required, min_val=min_val, max_val=max_val)


def _float(name: str, min_val=None, max_val=None) -> FieldSchema:
    return FieldSchema(name=name, field_type=FieldType.FLOAT, min_val=min_val, max_val=max_val)


def _bool(name: str) -> FieldSchema:
    return FieldSchema(name=name, field_type=FieldType.BOOL)


# ---------------------------------------------------------------------------
# FieldSchema
# ---------------------------------------------------------------------------

def test_field_schema_round_trip():
    f = FieldSchema(name="x", field_type=FieldType.INT, min_val=0, max_val=100)
    f2 = FieldSchema.from_dict(f.to_dict())
    assert f2.name == "x"
    assert f2.field_type == FieldType.INT
    assert f2.min_val == 0


# ---------------------------------------------------------------------------
# ConfigSchema
# ---------------------------------------------------------------------------

def test_schema_add_field():
    s = _schema(_str("name"))
    assert len(s.fields) == 1


def test_schema_to_dict():
    s = _schema(_str("x"))
    d = s.to_dict()
    assert d["name"] == "test"
    assert len(d["fields"]) == 1


# ---------------------------------------------------------------------------
# Valid configs
# ---------------------------------------------------------------------------

def test_valid_string():
    v = ConfigValidator(_schema(_str("env")))
    r = v.validate({"env": "prod"})
    assert r.ok
    assert r.applied["env"] == "prod"


def test_valid_int():
    v = ConfigValidator(_schema(_int("port", min_val=1024, max_val=65535)))
    r = v.validate({"port": 8080})
    assert r.ok


def test_valid_float():
    v = ConfigValidator(_schema(_float("threshold", min_val=0.0, max_val=1.0)))
    r = v.validate({"threshold": 0.5})
    assert r.ok


def test_valid_bool():
    v = ConfigValidator(_schema(_bool("dry_run")))
    r = v.validate({"dry_run": True})
    assert r.ok


def test_valid_list():
    f = FieldSchema(name="modules", field_type=FieldType.LIST)
    v = ConfigValidator(_schema(f))
    r = v.validate({"modules": ["a", "b"]})
    assert r.ok


def test_valid_dict():
    f = FieldSchema(name="settings", field_type=FieldType.DICT)
    v = ConfigValidator(_schema(f))
    r = v.validate({"settings": {"k": "v"}})
    assert r.ok


# ---------------------------------------------------------------------------
# Missing required field
# ---------------------------------------------------------------------------

def test_missing_required_fails():
    v = ConfigValidator(_schema(_str("env")))
    r = v.validate({})
    assert not r.ok
    assert any("missing_required_field" in e for e in r.errors)


def test_missing_optional_with_default_applied():
    v = ConfigValidator(_schema(_str("mode", required=False, default="dry")))
    r = v.validate({})
    assert r.ok
    assert r.applied.get("mode") == "dry"
    assert any("default_applied" in w for w in r.warnings)


def test_missing_optional_no_default_ok():
    f = FieldSchema(name="opt", field_type=FieldType.STRING, required=False)
    v = ConfigValidator(_schema(f))
    r = v.validate({})
    assert r.ok


# ---------------------------------------------------------------------------
# Type errors
# ---------------------------------------------------------------------------

def test_string_given_int_fails():
    v = ConfigValidator(_schema(_str("env")))
    r = v.validate({"env": 123})
    assert not r.ok
    assert any("type_error" in e for e in r.errors)


def test_int_given_float_fails():
    v = ConfigValidator(_schema(_int("count")))
    r = v.validate({"count": 1.5})
    assert not r.ok


def test_bool_given_int_fails():
    v = ConfigValidator(_schema(_bool("flag")))
    r = v.validate({"flag": 1})
    assert not r.ok
    assert any("type_error" in e for e in r.errors)


def test_int_given_bool_fails():
    v = ConfigValidator(_schema(_int("count")))
    r = v.validate({"count": True})
    assert not r.ok


def test_float_given_int_ok():
    v = ConfigValidator(_schema(_float("ratio")))
    r = v.validate({"ratio": 1})   # int is ok for float
    assert r.ok


# ---------------------------------------------------------------------------
# Range errors
# ---------------------------------------------------------------------------

def test_int_below_min_fails():
    v = ConfigValidator(_schema(_int("port", min_val=1024)))
    r = v.validate({"port": 80})
    assert not r.ok
    assert any("range_error" in e for e in r.errors)


def test_int_above_max_fails():
    v = ConfigValidator(_schema(_int("workers", max_val=10)))
    r = v.validate({"workers": 99})
    assert not r.ok


def test_float_in_range_ok():
    v = ConfigValidator(_schema(_float("ratio", min_val=0.0, max_val=1.0)))
    r = v.validate({"ratio": 0.0})
    assert r.ok
    r2 = v.validate({"ratio": 1.0})
    assert r2.ok


# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------

def test_allowed_values_valid():
    v = ConfigValidator(_schema(_str("env", allowed=["dev", "staging", "prod"])))
    r = v.validate({"env": "prod"})
    assert r.ok


def test_allowed_values_invalid():
    v = ConfigValidator(_schema(_str("env", allowed=["dev", "prod"])))
    r = v.validate({"env": "unknown"})
    assert not r.ok
    assert any("invalid_value" in e for e in r.errors)


# ---------------------------------------------------------------------------
# Multiple errors collected
# ---------------------------------------------------------------------------

def test_multiple_errors():
    v = ConfigValidator(_schema(_str("a"), _int("b", min_val=10)))
    r = v.validate({"a": 123, "b": 5})
    assert not r.ok
    assert len(r.errors) >= 2


# ---------------------------------------------------------------------------
# validate_many
# ---------------------------------------------------------------------------

def test_validate_many():
    v = ConfigValidator(_schema(_str("env")))
    results = v.validate_many([{"env": "prod"}, {"env": 123}, {}])
    assert results[0].ok
    assert not results[1].ok
    assert not results[2].ok


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

def test_result_to_dict():
    r = ConfigValidationResult(ok=True)
    d = r.to_dict()
    assert d["ok"] is True
    assert "result_id" in d
    assert "errors" in d
