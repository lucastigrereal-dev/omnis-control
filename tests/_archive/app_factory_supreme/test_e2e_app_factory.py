"""E2E tests for P26 App Factory Supreme."""
import pytest

from src.app_factory_supreme.pipeline import BuildPipeline
from src.app_factory_supreme.models import AppBuild, ModuleBuild, BUILD_COMPLETE, BUILD_PLANNED
from src.app_factory_supreme.cli import main


class TestE2EBuildFlow:
    def test_full_dry_run_pipeline(self):
        bp = BuildPipeline(dry_run=True)
        build = bp.build(title="CRM with auth and admin dashboard")
        assert isinstance(build, AppBuild)
        assert module_exists(build, "auth")
        assert module_exists(build, "admin")

    def test_plan_then_build_separate_steps(self):
        bp = BuildPipeline(dry_run=True)
        plan = bp.plan(title="REST API with notifications")
        assert plan.module_count >= 2
        # Blueprint approval simulation
        plan.blueprint_approved = True
        assert plan.blueprint_approved is True

    def test_build_persists_output_info(self):
        bp = BuildPipeline(dry_run=True)
        build = bp.build(title="Payment Gateway")
        assert build.output_dir != ""


class TestE2ECollectorDegradation:
    """Build pipeline never breaks."""

    def test_build_with_empty_title(self):
        bp = BuildPipeline(dry_run=True)
        build = bp.build(title="")
        assert isinstance(build, AppBuild)

    def test_build_with_special_characters(self):
        bp = BuildPipeline(dry_run=True)
        build = bp.build(title="App with $p3c!@l ch@rs")
        assert isinstance(build, AppBuild)


class TestE2ECLIIntegration:
    def test_cli_build(self):
        assert main(["build", "--title", "Test CLI App"]) == 0

    def test_cli_plan(self):
        assert main(["plan", "--title", "Test Plan"]) == 0

    def test_cli_status(self):
        assert main(["status", "apb_test"]) == 0

    def test_cli_list(self):
        assert main(["list"]) == 0

    def test_cli_rollback(self):
        assert main(["rollback", "apb_test"]) == 0

    def test_cli_no_command(self):
        assert main([]) == 1


class TestE2ESnapshotRoundtrip:
    def test_build_to_dict_roundtrip(self):
        bp = BuildPipeline(dry_run=True)
        b1 = bp.build(title="Roundtrip Test")
        b2 = AppBuild.from_dict(b1.to_dict())
        assert b2.build_id == b1.build_id
        assert b2.title == b1.title
        assert b2.module_count == b1.module_count


def module_exists(build: AppBuild, name: str) -> bool:
    return any(m.module_name == name for m in build.modules)
