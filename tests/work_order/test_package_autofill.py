"""Tests for P9.5 — Mission Package Auto-Fill."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.work_order.models import (
    OutputContract,
    OutputEntry,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    make_output_id,
    make_work_order_id,
)
from src.work_order.package_autofill import (
    AutoFillEntry,
    AutoFillResult,
    auto_fill_from_orchestrator_run,
    auto_fill_mission_package,
)


@pytest.fixture
def tmp_exports():
    d = tempfile.mkdtemp(prefix="p9_af_exports_")
    yield Path(d)
    import shutil
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def tmp_packages():
    d = tempfile.mkdtemp(prefix="p9_af_packages_")
    yield Path(d)
    import shutil
    shutil.rmtree(d, ignore_errors=True)


def make_work_order_with_outputs(
    exports_root: Path,
    *,
    graph_run_id: str = "grun_test01",
    role: str = "copywriter",
    outputs_count: int = 2,
) -> WorkOrder:
    wo = WorkOrder(
        work_order_id=make_work_order_id(),
        graph_step_id="step_01",
        graph_run_id=graph_run_id,
        role=role,
        step_label="Criar legenda",
        status=WorkOrderStatus.OUTPUT_SUBMITTED,
        contracts=[
            OutputContract("contract_00", OutputType.MARKDOWN, "Texto final", True),
            OutputContract("contract_01", OutputType.JSON, "Metadados", True),
        ],
    )

    wo_dir = exports_root / wo.work_order_id
    wo_dir.mkdir(parents=True, exist_ok=True)

    for i in range(outputs_count):
        contract_id = f"contract_{i:02d}"
        ext = "md" if i == 0 else "json"
        file_name = f"output_{i:02d}_{contract_id}.{ext}"
        disk_path = wo_dir / file_name

        content = f"# Output {i}" if ext == "md" else json.dumps({"index": i})
        disk_path.write_text(content, encoding="utf-8")

        entry = OutputEntry(
            output_id=make_output_id(),
            output_type=OutputType.MARKDOWN if i == 0 else OutputType.JSON,
            contract_id=contract_id,
            file_path=file_name,
            status="validated",
        )
        wo.outputs.append(entry)

    manifest = wo_dir / "work_order.json"
    manifest.write_text(
        json.dumps(wo.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return wo


def make_mission_package(
    packages_root: Path,
    mission_id: str = "mb_test01",
) -> Path:
    pkg_dir = packages_root / mission_id
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "04_outputs").mkdir(exist_ok=True)

    manifest_data = {
        "mission_id": mission_id,
        "request_text": "Test mission",
        "intent": "carousel",
        "deliverable": "carousel_package",
        "account_handle": "test_account",
        "package_dir": str(pkg_dir),
        "files": ["01_mission_brief.md", "04_outputs/"],
        "dry_run": True,
        "created_at": "2026-05-09T00:00:00Z",
    }
    manifest_path = pkg_dir / "mission_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return pkg_dir


class TestAutoFillResult:
    def test_all_copied_true(self):
        result = AutoFillResult(
            mission_id="m1",
            graph_run_id="g1",
            work_order_count=1,
            output_count=2,
            filled_count=2,
            skipped_count=0,
            entries=[],
        )
        assert result.all_copied is True

    def test_all_copied_false_when_skipped(self):
        result = AutoFillResult(
            mission_id="m1",
            graph_run_id="g1",
            work_order_count=1,
            output_count=2,
            filled_count=1,
            skipped_count=1,
            entries=[],
        )
        assert result.all_copied is False

    def test_all_copied_false_when_none_filled(self):
        result = AutoFillResult(
            mission_id="m1",
            graph_run_id="g1",
            work_order_count=0,
            output_count=0,
            filled_count=0,
            skipped_count=0,
            entries=[],
        )
        assert result.all_copied is False

    def test_to_dict_roundtrip(self):
        result = AutoFillResult(
            mission_id="m1",
            graph_run_id="g1",
            work_order_count=1,
            output_count=1,
            filled_count=1,
            skipped_count=0,
            entries=[
                AutoFillEntry(
                    output_id="out_01",
                    work_order_id="wo_01",
                    contract_id="c01",
                    source_path="/src/a.md",
                    target_path="/tgt/a.md",
                    copied=True,
                )
            ],
        )
        d = result.to_dict()
        assert d["mission_id"] == "m1"
        assert len(d["entries"]) == 1


class TestAutoFillMissionPackage:
    def test_fills_outputs_into_package(self, tmp_exports, tmp_packages):
        make_work_order_with_outputs(tmp_exports, graph_run_id="grun_fill01")
        make_mission_package(tmp_packages, "mb_fill01")

        result = auto_fill_mission_package(
            "mb_fill01", "grun_fill01",
            exports_root=tmp_exports, packages_root=tmp_packages,
        )
        assert result.work_order_count == 1
        assert result.output_count == 2
        assert result.filled_count == 2
        assert result.all_copied is True

    def test_copies_files_to_role_subdir(self, tmp_exports, tmp_packages):
        wo = make_work_order_with_outputs(tmp_exports, graph_run_id="grun_role01", role="designer")
        make_mission_package(tmp_packages, "mb_role01")

        result = auto_fill_mission_package(
            "mb_role01", "grun_role01",
            exports_root=tmp_exports, packages_root=tmp_packages,
        )
        assert result.filled_count == 2

        role_dir = tmp_packages / "mb_role01" / "04_outputs" / "designer"
        assert role_dir.exists()
        copied_files = list(role_dir.iterdir())
        assert len(copied_files) == 2

    def test_dry_run_does_not_copy(self, tmp_exports, tmp_packages):
        make_work_order_with_outputs(tmp_exports, graph_run_id="grun_dry01")
        make_mission_package(tmp_packages, "mb_dry01")

        result = auto_fill_mission_package(
            "mb_dry01", "grun_dry01",
            exports_root=tmp_exports, packages_root=tmp_packages,
            dry_run=True,
        )
        assert result.filled_count == 2
        role_dir = tmp_packages / "mb_dry01" / "04_outputs" / "copywriter"
        assert not role_dir.exists()

    def test_updates_manifest(self, tmp_exports, tmp_packages):
        make_work_order_with_outputs(tmp_exports, graph_run_id="grun_manifest01")
        make_mission_package(tmp_packages, "mb_manifest01")

        auto_fill_mission_package(
            "mb_manifest01", "grun_manifest01",
            exports_root=tmp_exports, packages_root=tmp_packages,
        )

        manifest_path = tmp_packages / "mb_manifest01" / "mission_manifest.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert "auto_fill" in data
        assert data["auto_fill"]["graph_run_id"] == "grun_manifest01"
        assert data["auto_fill"]["work_order_count"] == 1

    def test_handles_missing_source(self, tmp_exports, tmp_packages):
        wo = make_work_order_with_outputs(tmp_exports, graph_run_id="grun_missing")
        # delete a source file after creating the work order
        wo_dir = tmp_exports / wo.work_order_id
        for f in wo_dir.glob("output_*.md"):
            f.unlink()

        make_mission_package(tmp_packages, "mb_missing01")

        result = auto_fill_mission_package(
            "mb_missing01", "grun_missing",
            exports_root=tmp_exports, packages_root=tmp_packages,
        )
        assert result.skipped_count > 0
        assert result.all_copied is False

    def test_no_work_orders_is_ok(self, tmp_exports, tmp_packages):
        make_mission_package(tmp_packages, "mb_empty01")

        result = auto_fill_mission_package(
            "mb_empty01", "nonexistent_run",
            exports_root=tmp_exports, packages_root=tmp_packages,
        )
        assert result.work_order_count == 0
        assert result.output_count == 0

    def test_multiple_work_orders(self, tmp_exports, tmp_packages):
        make_work_order_with_outputs(tmp_exports, graph_run_id="grun_multi", role="copywriter")
        make_work_order_with_outputs(tmp_exports, graph_run_id="grun_multi", role="designer")
        make_mission_package(tmp_packages, "mb_multi01")

        result = auto_fill_mission_package(
            "mb_multi01", "grun_multi",
            exports_root=tmp_exports, packages_root=tmp_packages,
        )
        assert result.work_order_count == 2
        assert result.output_count == 4
        assert result.filled_count == 4

    def test_idempotent_refill(self, tmp_exports, tmp_packages):
        make_work_order_with_outputs(tmp_exports, graph_run_id="grun_idem01")
        make_mission_package(tmp_packages, "mb_idem01")

        r1 = auto_fill_mission_package(
            "mb_idem01", "grun_idem01",
            exports_root=tmp_exports, packages_root=tmp_packages,
        )
        r2 = auto_fill_mission_package(
            "mb_idem01", "grun_idem01",
            exports_root=tmp_exports, packages_root=tmp_packages,
        )
        assert r1.filled_count == r2.filled_count


class TestAutoFillFromOrchestratorRun:
    def test_extracts_ids(self, tmp_exports, tmp_packages):
        make_work_order_with_outputs(tmp_exports, graph_run_id="grun_och01")
        make_mission_package(tmp_packages, "mb_och01")

        class FakeOrchRun:
            mission_id = "mb_och01"
            run_id = "run_fallback"
            graph_run_id = "grun_och01"

        result = auto_fill_from_orchestrator_run(
            FakeOrchRun(),
            exports_root=tmp_exports, packages_root=tmp_packages,
        )
        assert result.mission_id == "mb_och01"
        assert result.filled_count == 2

    def test_falls_back_to_run_id(self, tmp_exports, tmp_packages):
        make_work_order_with_outputs(tmp_exports, graph_run_id="grun_fb01")
        make_mission_package(tmp_packages, "run_fb")

        class FakeOrchRun:
            mission_id = None
            run_id = "run_fb"
            graph_run_id = "grun_fb01"

        result = auto_fill_from_orchestrator_run(
            FakeOrchRun(),
            exports_root=tmp_exports, packages_root=tmp_packages,
        )
        assert result.mission_id == "run_fb"

    def test_raises_without_graph_run_id(self, tmp_exports, tmp_packages):
        class FakeOrchRun:
            mission_id = "mb_no_graph"
            run_id = "run_no_graph"
            graph_run_id = None

        with pytest.raises(ValueError, match="has no graph_run_id"):
            auto_fill_from_orchestrator_run(
                FakeOrchRun(),
                exports_root=tmp_exports, packages_root=tmp_packages,
            )

    def test_handles_missing_package_dir(self, tmp_exports, tmp_packages):
        make_work_order_with_outputs(tmp_exports, graph_run_id="grun_nopkg")

        class FakeOrchRun:
            mission_id = "mb_nonexistent"
            run_id = "run_nopkg"
            graph_run_id = "grun_nopkg"

        result = auto_fill_from_orchestrator_run(
            FakeOrchRun(),
            exports_root=tmp_exports, packages_root=tmp_packages,
        )
        assert result.work_order_count == 1
        assert result.filled_count == 2
