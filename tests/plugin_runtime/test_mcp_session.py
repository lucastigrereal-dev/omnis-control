"""Tests for W153 — MCP Session Manager."""
import pytest
from src.plugin_runtime.mcp_session import McpSessionManager, McpSession, SESSION_ACTIVE, SESSION_CLOSED, SESSION_EXPIRED


@pytest.fixture
def manager():
    return McpSessionManager()


def test_open_session(manager):
    s = manager.open("plugin_01")
    assert isinstance(s, McpSession)
    assert s.status == SESSION_ACTIVE


def test_open_increments_count(manager):
    manager.open("p1")
    manager.open("p2")
    assert manager.count() == 2


def test_close_session(manager):
    s = manager.open("p1")
    result = manager.close(s.session_id)
    assert result is True
    assert s.status == SESSION_CLOSED


def test_close_sets_closed_at(manager):
    s = manager.open("p1")
    manager.close(s.session_id)
    assert s.closed_at is not None


def test_close_unknown_returns_false(manager):
    assert manager.close("bad") is False


def test_expire_session(manager):
    s = manager.open("p1")
    manager.expire(s.session_id)
    assert s.status == SESSION_EXPIRED


def test_record_call_active(manager):
    s = manager.open("p1")
    manager.record_call(s.session_id)
    assert s.call_count == 1


def test_record_call_closed_fails(manager):
    s = manager.open("p1")
    manager.close(s.session_id)
    result = manager.record_call(s.session_id)
    assert result is False
    assert s.call_count == 0


def test_active_sessions_filter(manager):
    s1 = manager.open("p1")
    s2 = manager.open("p2")
    manager.close(s1.session_id)
    active = manager.active_sessions()
    assert len(active) == 1
    assert active[0].session_id == s2.session_id


def test_sessions_for_plugin(manager):
    manager.open("p1")
    manager.open("p1")
    manager.open("p2")
    assert len(manager.sessions_for_plugin("p1")) == 2


def test_to_dict(manager):
    s = manager.open("p1", metadata={"version": "1.0"})
    d = s.to_dict()
    assert d["metadata"]["version"] == "1.0"
    assert d["call_count"] == 0
