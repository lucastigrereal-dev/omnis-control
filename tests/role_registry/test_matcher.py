"""Tests for Role Registry matcher."""
import socket
import os
import pytest
from src.role_registry.matcher import (
    match_roles_by_sector,
    match_roles_by_output,
    get_role,
    list_all_roles,
)
from src.role_registry.errors import RoleNotFoundError


def test_match_by_sector_marketing():
    results = match_roles_by_sector("marketing")
    ids = [r.role_id for r in results]
    assert "copywriter" in ids
    assert "marketing_strategist" in ids
    assert "visual_director" in ids


def test_match_by_sector_apps():
    results = match_roles_by_sector("apps")
    ids = [r.role_id for r in results]
    assert "app_architect" in ids
    assert "qa_auditor" in ids


def test_match_by_sector_no_results():
    results = match_roles_by_sector("unknown_sector_xyz")
    assert results == []


def test_match_by_output_video_plan():
    results = match_roles_by_output("video_plan")
    assert any(r.role_id == "video_planner" for r in results)


def test_match_by_output_caption():
    results = match_roles_by_output("caption")
    assert any(r.role_id == "copywriter" for r in results)


def test_get_role_found():
    role = get_role("copywriter")
    assert role.role_id == "copywriter"
    assert "marketing" in role.sectors


def test_get_role_not_found():
    with pytest.raises(RoleNotFoundError):
        get_role("nonexistent_role_xyz")


def test_list_all_roles():
    roles = list_all_roles()
    assert len(roles) >= 8


def test_no_network_calls(monkeypatch):
    def _block(*args, **kwargs):
        raise AssertionError("Network blocked")
    monkeypatch.setattr(socket.socket, "connect", _block)
    match_roles_by_sector("marketing")


def test_no_env_reads(monkeypatch):
    original = os.getenv
    def _guard(key, *args, **kwargs):
        assert not key.startswith("META_") and not key.startswith("INSTAGRAM_")
        return original(key, *args, **kwargs)
    monkeypatch.setattr(os, "getenv", _guard)
    match_roles_by_sector("marketing")
