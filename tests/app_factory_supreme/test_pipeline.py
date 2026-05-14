"""Tests for P26 BuildPipeline."""
import pytest

from src.app_factory_supreme.pipeline import BuildPipeline
from src.app_factory_supreme.models import AppBuild, BUILD_PLANNED, BUILD_COMPLETE
from src.app_factory_supreme.errors import BlueprintNotApprovedError


class TestBuildPipeline:
    @pytest.fixture
    def pipeline(self):
        return BuildPipeline(dry_run=True)

    def test_build_dry_run_returns_build(self, pipeline):
        build = pipeline.build(title="Test App")
        assert isinstance(build, AppBuild)
        assert build.title == "Test App"
        assert build.status == BUILD_PLANNED

    def test_build_dry_run_plans_modules(self, pipeline):
        build = pipeline.build(title="CRM with auth and admin")
        module_names = [m.module_name for m in build.modules]
        assert "core" in module_names
        assert "auth" in module_names
        assert "tests" in module_names

    def test_build_dry_run_has_output_dir(self, pipeline):
        build = pipeline.build(title="Test App")
        assert "generated_apps" in build.output_dir
        assert "dry_run" in build.output_dir

    def test_plan_returns_modules(self, pipeline):
        build = pipeline.plan(title="API with search")
        assert build.module_count >= 2
        assert "search" in [m.module_name for m in build.modules]

    def test_plan_blueprint_not_approved(self, pipeline):
        build = pipeline.plan(title="Test")
        assert build.blueprint_approved is False

    def test_rollback_successful_when_not_terminal(self, pipeline):
        build = pipeline.build(title="Test App")
        result = pipeline.rollback(build)
        assert result is True
        assert build.status == "rolled_back"

    def test_rollback_fails_when_terminal(self, pipeline):
        build = pipeline.build(title="Test App")
        build.status = BUILD_COMPLETE
        result = pipeline.rollback(build)
        assert result is False

    def test_real_build_without_blueprint_approval_raises(self):
        bp = BuildPipeline(dry_run=False)
        build = AppBuild.new(title="Test")
        with pytest.raises(BlueprintNotApprovedError):
            bp._build_real(build, None)

    def test_module_planning_detects_web(self):
        modules = BuildPipeline._plan_modules("Web Dashboard", "A web app")
        assert "web" in modules

    def test_module_planning_detects_api(self):
        modules = BuildPipeline._plan_modules("REST API", "API endpoints")
        assert "api" in modules

    def test_module_planning_detects_payments(self):
        modules = BuildPipeline._plan_modules("Payment System", "Billing and payments")
        assert "payments" in modules
