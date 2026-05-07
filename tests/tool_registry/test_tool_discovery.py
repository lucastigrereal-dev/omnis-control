"""Testes do discovery — P0.8."""
from __future__ import annotations

import pytest

from src.tool_registry.models import ToolStatus, ToolCategory
from src.tool_registry.discovery import discover_known_tools


class TestDiscovery:
    """discover_known_tools — lista minima + status honestos."""

    def test_returns_list(self):
        tools = discover_known_tools()
        assert len(tools) >= 15

    def test_instagram_is_blocked(self):
        tools = discover_known_tools()
        ig = [t for t in tools if t.tool_id == "instagram_graph_api"]
        assert len(ig) == 1
        assert ig[0].status == ToolStatus.BLOCKED

    def test_publisher_local_is_dry_run(self):
        tools = discover_known_tools()
        pub = [t for t in tools if t.tool_id == "publisher_local_dry_run"]
        assert len(pub) == 1
        assert pub[0].status == ToolStatus.DRY_RUN

    def test_publer_is_not_configured(self):
        tools = discover_known_tools()
        publer = [t for t in tools if t.tool_id == "publer"]
        assert len(publer) == 1
        assert publer[0].status == ToolStatus.NOT_CONFIGURED

    def test_known_tools_present(self):
        tools = discover_known_tools()
        ids = {t.tool_id for t in tools}
        expected = {
            "instagram_graph_api", "publisher_local_dry_run", "publisher_os_argos",
            "n8n", "akasha_postgres", "qdrant", "obsidian_vault", "github",
            "canva", "publer", "metricool", "gmail", "google_drive",
            "claude_code", "openai_api", "gemini_api", "perplexity",
            "docker", "local_filesystem",
        }
        missing = expected - ids
        assert missing == set(), f"Ferramentas ausentes: {missing}"

    def test_no_secrets_in_credentials(self):
        tools = discover_known_tools()
        for t in tools:
            for cred in t.required_credentials:
                assert len(cred) < 40 or not cred[0].islower(), \
                    f"Possivel secret em {t.tool_id}: {cred[:10]}..."

    def test_all_have_required_fields(self):
        tools = discover_known_tools()
        for t in tools:
            assert t.tool_id != "", f"tool_id vazio"
            assert t.name != "", f"name vazio em {t.tool_id}"
            assert t.category in ToolCategory.ALL, f"categoria invalida em {t.tool_id}"
            assert t.status in ToolStatus.ALL, f"status invalido em {t.tool_id}"
            assert t.risk_level != "", f"risk_level vazio em {t.tool_id}"
