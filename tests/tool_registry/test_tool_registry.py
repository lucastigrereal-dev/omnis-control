"""Testes do ToolRegistry storage — P0.8."""
from __future__ import annotations

import pytest

from src.tool_registry.models import ToolRecord, ToolStatus, ToolCategory
from src.tool_registry.registry import ToolRegistry
from src.tool_registry.errors import DuplicateToolError


@pytest.fixture
def tmp_registry(tmp_path):
    return ToolRegistry(base_dir=str(tmp_path / "tool_registry"))


@pytest.fixture
def sample_tool():
    return ToolRecord(
        tool_id="test_tool",
        name="Test Tool",
        category=ToolCategory.RESEARCH,
        status=ToolStatus.MANUAL,
    )


class TestAddAndGet:
    """add_tool + get_tool."""

    def test_add_tool(self, tmp_registry, sample_tool):
        added = tmp_registry.add_tool(sample_tool)
        assert added.tool_id == sample_tool.tool_id

    def test_get_tool_exists(self, tmp_registry, sample_tool):
        tmp_registry.add_tool(sample_tool)
        found = tmp_registry.get_tool("test_tool")
        assert found is not None
        assert found.name == "Test Tool"

    def test_get_tool_not_exists(self, tmp_registry):
        assert tmp_registry.get_tool("nonexistent") is None

    def test_duplicate_blocked(self, tmp_registry, sample_tool):
        tmp_registry.add_tool(sample_tool)
        with pytest.raises(DuplicateToolError):
            tmp_registry.add_tool(sample_tool)


class TestListTools:
    """list_tools com filtros."""

    def test_list_all_empty(self, tmp_registry):
        assert tmp_registry.list_tools() == []

    def test_list_all(self, tmp_registry, sample_tool):
        tmp_registry.add_tool(sample_tool)
        tools = tmp_registry.list_tools()
        assert len(tools) == 1

    def test_list_by_status(self, tmp_registry):
        t1 = ToolRecord(tool_id="tt1", name="T1", category=ToolCategory.LLM, status=ToolStatus.READ_ONLY)
        t2 = ToolRecord(tool_id="tt2", name="T2", category=ToolCategory.LLM, status=ToolStatus.BLOCKED)
        tmp_registry.add_tool(t1)
        tmp_registry.add_tool(t2)
        assert len(tmp_registry.list_tools(status=ToolStatus.BLOCKED)) == 1
        assert len(tmp_registry.list_tools(status=ToolStatus.READ_ONLY)) == 1

    def test_list_by_category(self, tmp_registry):
        t1 = ToolRecord(tool_id="tt1", name="T1", category=ToolCategory.DEVELOPMENT, status=ToolStatus.MANUAL)
        t2 = ToolRecord(tool_id="tt2", name="T2", category=ToolCategory.PUBLISHING, status=ToolStatus.MANUAL)
        tmp_registry.add_tool(t1)
        tmp_registry.add_tool(t2)
        assert len(tmp_registry.list_tools(category=ToolCategory.PUBLISHING)) == 1


class TestUpdateStatus:
    """update_status + validation_log."""

    def test_update_status(self, tmp_registry, sample_tool):
        tmp_registry.add_tool(sample_tool)
        updated = tmp_registry.update_status("test_tool", ToolStatus.BLOCKED)
        assert updated is not None
        assert updated.status == ToolStatus.BLOCKED

    def test_update_status_logs(self, tmp_registry, sample_tool):
        tmp_registry.add_tool(sample_tool)
        tmp_registry.update_status("test_tool", ToolStatus.READ_ONLY, validation_status="checked")
        log = tmp_registry.get_validation_log(tool_id="test_tool")
        assert len(log) == 1
        assert log[0]["new_status"] == ToolStatus.READ_ONLY
        assert log[0]["validation_status"] == "checked"


class TestToolsByStatusCategory:
    """tools_by_status + tools_by_category."""

    def test_by_status(self, tmp_registry):
        tmp_registry.add_tool(ToolRecord(tool_id="tt1", name="T1", category=ToolCategory.LLM, status=ToolStatus.READ_ONLY))
        tmp_registry.add_tool(ToolRecord(tool_id="tt2", name="T2", category=ToolCategory.LLM, status=ToolStatus.READ_ONLY))
        tmp_registry.add_tool(ToolRecord(tool_id="tt3", name="T3", category=ToolCategory.DEVELOPMENT, status=ToolStatus.BLOCKED))
        counts = tmp_registry.tools_by_status()
        assert counts.get(ToolStatus.READ_ONLY) == 2
        assert counts.get(ToolStatus.BLOCKED) == 1

    def test_by_category(self, tmp_registry):
        tmp_registry.add_tool(ToolRecord(tool_id="tt1", name="T1", category=ToolCategory.LLM, status=ToolStatus.MANUAL))
        tmp_registry.add_tool(ToolRecord(tool_id="tt2", name="T2", category=ToolCategory.LLM, status=ToolStatus.MANUAL))
        tmp_registry.add_tool(ToolRecord(tool_id="tt3", name="T3", category=ToolCategory.INFRASTRUCTURE, status=ToolStatus.MANUAL))
        counts = tmp_registry.tools_by_category()
        assert counts.get(ToolCategory.LLM) == 2
        assert counts.get(ToolCategory.INFRASTRUCTURE) == 1


class TestMarkValidated:
    """mark_validated — nao altera status operacional."""

    def test_mark_validated_preserves_status(self, tmp_registry, sample_tool):
        tmp_registry.add_tool(sample_tool)
        result = tmp_registry.mark_validated("test_tool", "pass", notes="Tudo ok")
        assert result is not None
        assert result.status == sample_tool.status  # nao mudou
        assert result.validation_status == "pass"
