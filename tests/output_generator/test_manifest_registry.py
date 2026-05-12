"""Tests for manifest registry."""
from __future__ import annotations

import json
from pathlib import Path

from src.output_generator.manifest_registry import ManifestRegistry


class TestManifestRegistry:
    def test_register_adds_entry(self, tmp_path: Path):
        reg = ManifestRegistry(tmp_path / "registry.jsonl")
        reg.register("out_01", "wo_01", "markdown", "/tmp/test.md", "md_gen", "abc123")
        assert reg.count() == 1

    def test_list_returns_registered(self, tmp_path: Path):
        reg = ManifestRegistry(tmp_path / "registry.jsonl")
        reg.register("out_01", "wo_01", "markdown", "/tmp/test.md", "md_gen", "abc123")
        entries = reg.list_all()
        assert len(entries) == 1
        assert entries[0]["output_id"] == "out_01"

    def test_show_finds_entry(self, tmp_path: Path):
        reg = ManifestRegistry(tmp_path / "registry.jsonl")
        reg.register("out_01", "wo_01", "markdown", "/tmp/test.md", "md_gen", "abc123")
        reg.register("out_02", "wo_02", "json", "/tmp/test2.json", "json_gen", "def456")
        entry = reg.show("out_02")
        assert entry is not None
        assert entry["output_type"] == "json"

    def test_show_returns_none_for_missing(self, tmp_path: Path):
        reg = ManifestRegistry(tmp_path / "registry.jsonl")
        assert reg.show("ghost") is None

    def test_list_by_work_order(self, tmp_path: Path):
        reg = ManifestRegistry(tmp_path / "registry.jsonl")
        reg.register("out_01", "wo_A", "markdown", "/tmp/a.md", "md_gen")
        reg.register("out_02", "wo_B", "json", "/tmp/b.json", "json_gen")
        reg.register("out_03", "wo_A", "csv", "/tmp/c.csv", "csv_gen")
        wo_a = reg.list_by_work_order("wo_A")
        assert len(wo_a) == 2
        assert all(e["work_order_id"] == "wo_A" for e in wo_a)

    def test_file_is_valid_jsonl(self, tmp_path: Path):
        reg = ManifestRegistry(tmp_path / "registry.jsonl")
        reg.register("out_01", "wo_01", "markdown", "/tmp/test.md", "md_gen")
        reg.register("out_02", "wo_02", "json", "/tmp/test2.json", "json_gen")

        content = (tmp_path / "registry.jsonl").read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            entry = json.loads(line)
            assert "output_id" in entry

    def test_registry_persists_across_instances(self, tmp_path: Path):
        path = tmp_path / "registry.jsonl"
        reg1 = ManifestRegistry(path)
        reg1.register("out_01", "wo_01", "markdown", "/tmp/test.md", "md_gen")

        reg2 = ManifestRegistry(path)
        assert reg2.count() == 1
        assert reg2.show("out_01") is not None

    def test_empty_registry(self, tmp_path: Path):
        reg = ManifestRegistry(tmp_path / "nonexistent.jsonl")
        assert reg.count() == 0
        assert reg.list_all() == []
