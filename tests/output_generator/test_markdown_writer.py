"""Tests for markdown output writer."""
from __future__ import annotations

import json
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

from src.output_generator.markdown_writer import write_markdown_output
from src.output_generator.models import GeneratedOutputStatus
from src.work_order.models import (
    OutputContract,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    make_work_order_id,
)


def _make_test_wo(**overrides) -> WorkOrder:
    defaults = {
        "work_order_id": make_work_order_id(),
        "graph_step_id": "step_01",
        "graph_run_id": "run_test",
        "role": "copywriter",
        "step_label": "Test Post",
        "status": WorkOrderStatus.APPROVED,
        "contracts": [
            OutputContract("c00", OutputType.MARKDOWN, "Texto do post", True),
        ],
        "metadata": {
            "expected_output": "Post sobre viagem",
            "request": "Criar post para Instagram",
        },
    }
    defaults.update(overrides)
    return WorkOrder(**defaults)


class TestWriteMarkdownOutput:
    def test_generates_markdown_file(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_markdown_output(wo, tmp_path)

        assert result.status == GeneratedOutputStatus.GENERATED
        md_file = Path(result.file_path)
        assert md_file.exists()
        content = md_file.read_text(encoding="utf-8")
        assert "# Output:" in content

    def test_creates_output_directory(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_markdown_output(wo, tmp_path)
        out_dir = Path(result.file_path).parent
        assert out_dir.exists()
        assert out_dir.name.startswith("out_")

    def test_creates_manifest(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_markdown_output(wo, tmp_path)
        out_dir = Path(result.file_path).parent
        manifest_path = out_dir / "output_manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["output_type"] == "markdown"
        assert manifest["work_order_id"] == wo.work_order_id

    def test_fingerprint_is_generated(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_markdown_output(wo, tmp_path)
        assert len(result.fingerprint) == 16  # sha256[:16]

    def test_markdown_contains_work_order_section(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_markdown_output(wo, tmp_path)
        content = Path(result.file_path).read_text(encoding="utf-8")
        assert "## Work Order" in content
        assert wo.work_order_id in content

    def test_markdown_contains_acceptance_criteria(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_markdown_output(wo, tmp_path)
        content = Path(result.file_path).read_text(encoding="utf-8")
        assert "## Acceptance Criteria" in content

    def test_markdown_contains_next_actions(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_markdown_output(wo, tmp_path)
        content = Path(result.file_path).read_text(encoding="utf-8")
        assert "## Next Actions" in content
        assert "Review manually" in content

    def test_manifest_has_no_secrets(self, tmp_path: Path):
        wo = _make_test_wo()
        result = write_markdown_output(wo, tmp_path)
        manifest_path = Path(result.file_path).parent / "output_manifest.json"
        raw = manifest_path.read_text(encoding="utf-8")
        assert "password" not in raw.lower()
        assert "secret" not in raw.lower()
        assert "token" not in raw.lower()
        assert "api_key" not in raw.lower()

    def test_no_markdown_contract_warns(self, tmp_path: Path):
        wo = _make_test_wo(contracts=[
            OutputContract("c00", OutputType.JSON, "JSON output", True),
        ])
        result = write_markdown_output(wo, tmp_path)
        assert result.status == GeneratedOutputStatus.GENERATED  # still generates
        assert any("markdown contract" in w.lower() for w in result.warnings)

    def test_different_fingerprints_for_different_content(self, tmp_path: Path):
        wo1 = _make_test_wo(step_label="A")
        wo2 = _make_test_wo(step_label="B")
        r1 = write_markdown_output(wo1, tmp_path / "a")
        r2 = write_markdown_output(wo2, tmp_path / "b")
        assert r1.fingerprint != r2.fingerprint

    def test_does_not_alter_work_order_status(self, tmp_path: Path):
        wo = _make_test_wo()
        orig = wo.status
        write_markdown_output(wo, tmp_path)
        assert wo.status == orig

    def test_does_not_call_network(self, tmp_path: Path):
        """Verifies writer is pure — no network imports."""
        wo = _make_test_wo()
        result = write_markdown_output(wo, tmp_path)
        assert result.status == GeneratedOutputStatus.GENERATED
        # No httpx, requests, urllib usage in module
        import inspect
        from src.output_generator import markdown_writer as mw
        source = inspect.getsource(mw)
        assert "requests." not in source
        assert "urllib." not in source
        assert "httpx" not in source
