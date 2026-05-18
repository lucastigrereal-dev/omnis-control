"""Tests for obsidian_check checker."""
from __future__ import annotations

import pytest
import os


class TestObsidianCheck:
    def test_check_vault_not_found(self, monkeypatch):
        """Returns vault_found=False when directory doesn't exist."""
        monkeypatch.setattr("os.path.isdir", lambda p: False)

        from src.checkers.obsidian_check import check

        result = check()
        assert result["vault_found"] is False
        assert "error" in result

    def test_check_vault_found_with_md_files(self, monkeypatch, tmp_path):
        """Returns vault_found=True with md file count."""
        # Create a temp vault with some .md files
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "note1.md").write_text("# Note 1")
        (vault / "note2.md").write_text("# Note 2")
        (vault / "readme.txt").write_text("not a markdown file")
        subdir = vault / "subdir"
        subdir.mkdir()
        (subdir / "nested.md").write_text("# Nested")

        # Monkeypatch OBSIDIAN_VAULT to point to our temp vault
        monkeypatch.setattr("src.checkers.obsidian_check.OBSIDIAN_VAULT", str(vault))

        from src.checkers.obsidian_check import check

        result = check()
        assert result["vault_found"] is True
        assert result["md_file_count"] == 3
        assert "subdir" in result["top_folders"]

    def test_check_vault_found_returns_path(self, monkeypatch, tmp_path):
        vault = tmp_path / "empty_vault"
        vault.mkdir()

        monkeypatch.setattr("src.checkers.obsidian_check.OBSIDIAN_VAULT", str(vault))

        from src.checkers.obsidian_check import check

        result = check()
        assert result["vault_found"] is True
        assert result["vault_path"] == str(vault)
        assert result["md_file_count"] == 0
