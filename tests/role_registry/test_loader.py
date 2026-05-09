"""Tests for Role Registry loader."""
import pytest
from pathlib import Path
from src.role_registry.loader import load_roles, DEFAULT_ROLES_PATH
from src.role_registry.errors import InvalidRolesConfigError


def test_load_default_roles():
    roles = load_roles()
    assert len(roles) >= 8
    ids = [r.role_id for r in roles]
    assert "copywriter" in ids
    assert "app_architect" in ids


def test_load_roles_has_required_fields():
    roles = load_roles()
    for r in roles:
        assert r.role_id
        assert r.name
        assert isinstance(r.sectors, list)
        assert isinstance(r.outputs, list)
        assert r.risk_level in ("low", "medium", "high")


def test_load_roles_invalid_path_raises():
    with pytest.raises(InvalidRolesConfigError):
        load_roles(Path("/nonexistent/roles.yaml"))


def test_load_roles_missing_key_raises(tmp_path):
    bad = tmp_path / "roles.yaml"
    bad.write_text("something: {}\n", encoding="utf-8")
    with pytest.raises(InvalidRolesConfigError):
        load_roles(bad)


def test_load_roles_invalid_yaml_raises(tmp_path):
    bad = tmp_path / "roles.yaml"
    bad.write_text("roles: [\nbad yaml", encoding="utf-8")
    with pytest.raises(InvalidRolesConfigError):
        load_roles(bad)
