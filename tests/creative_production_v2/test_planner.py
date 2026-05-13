"""Tests for CreativeProductionPlanner — deterministic, dry-run pipeline."""
from __future__ import annotations

import pytest

from src.creative_production_v2.models import (
    AssetSpec,
    AssetType,
    CreativeBriefV2,
    CreativeFormat,
    CreativePackage,
    CreativeRequest,
    CreativeStatus,
    CreativeTask,
    PackageStatus,
    ProductionAssetPlan,
    ProductionBatch,
    ReviewVerdict,
    TaskStatus,
)
from src.creative_production_v2.planner import CreativeProductionPlanner


@pytest.fixture
def planner():
    return CreativeProductionPlanner()


@pytest.fixture
def valid_request():
    return CreativeRequest(
        account_handle="@lucastigrereal",
        format=CreativeFormat.REEL,
        topic="Viagem em família para Natal RN",
        objective="Vender pacote Growth R$990/mês",
        tone="inspirador",
        target_audience="Famílias com filhos pequenos",
        key_message="Viajar em família custa menos do que parece",
        visual_style="praia",
        caption_seed="Família que viaja unida...",
        asset_count=4,
        priority=8,
    )


class TestBuildCreativeBrief:
    def test_deterministic_output(self, planner, valid_request):
        b1 = planner.build_creative_brief(valid_request)
        b2 = planner.build_creative_brief(valid_request)
        assert b1.hook_variants == b2.hook_variants
        assert b1.shot_list == b2.shot_list
        assert b1.design_notes == b2.design_notes
        assert b1.music_mood == b2.music_mood

    def test_brief_links_request(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        assert brief.request_id == valid_request.request_id
        assert brief.account_handle == valid_request.account_handle
        assert brief.format == valid_request.format
        assert brief.topic == valid_request.topic

    def test_planned_status(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        assert brief.status == CreativeStatus.PLANNED

    def test_hook_variants_generated(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        assert len(brief.hook_variants) == 3
        assert all(isinstance(h, str) for h in brief.hook_variants)
        assert all(valid_request.topic in h for h in brief.hook_variants)

    def test_shot_list_has_correct_count(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        assert len(brief.shot_list) == valid_request.asset_count

    def test_color_palette_detected(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        assert len(brief.color_palette) == 3

    def test_missing_fields_generate_warnings(self, planner):
        req = CreativeRequest(account_handle="", topic="", objective="")
        brief = planner.build_creative_brief(req)
        assert "MISSING_ACCOUNT_HANDLE" in brief.warnings
        assert "MISSING_TOPIC" in brief.warnings
        assert "MISSING_OBJECTIVE" in brief.warnings

    def test_no_warnings_for_valid_request(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        assert not brief.warnings

    def test_empty_topic_generates_placeholder_hook(self, planner):
        req = CreativeRequest(account_handle="@test", topic="")
        brief = planner.build_creative_brief(req)
        assert "placeholder" in brief.hook_variants[0].lower()

    def test_tool_suggestions_match_format(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        assert len(brief.tool_suggestions) > 0

    def test_different_formats_different_outputs(self, planner):
        req_carousel = CreativeRequest(
            account_handle="@test", topic="x", objective="y",
            format=CreativeFormat.CAROUSEL,
        )
        req_reel = CreativeRequest(
            account_handle="@test", topic="x", objective="y",
            format=CreativeFormat.REEL,
        )
        b_c = planner.build_creative_brief(req_carousel)
        b_r = planner.build_creative_brief(req_reel)
        assert b_c.tool_suggestions != b_r.tool_suggestions
        assert b_c.editing_notes != b_r.editing_notes


class TestPlanProductionAssets:
    def test_deterministic_output(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        p1 = planner.plan_production_assets(brief)
        p2 = planner.plan_production_assets(brief)
        assert p1.total_estimated_minutes == p2.total_estimated_minutes
        assert len(p1.assets) == len(p2.assets)

    def test_asset_plan_links_brief(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        assert plan.brief_id == brief.brief_id

    def test_asset_count_matches_target(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        assert len(plan.assets) == brief.asset_count_target

    def test_all_assets_have_types(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        for a in plan.assets:
            assert isinstance(a.asset_type, AssetType)

    def test_tool_assignments_populated(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        assert len(plan.tool_assignments) == brief.asset_count_target
        assert f"asset_0" in plan.tool_assignments

    def test_template_references_populated(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        assert len(plan.template_references) > 0

    def test_estimated_minutes_non_zero(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        assert plan.total_estimated_minutes > 0

    def test_single_asset_minimal_brief(self, planner):
        req = CreativeRequest(
            account_handle="@test", topic="x", objective="y",
            format=CreativeFormat.PHOTO, asset_count=1,
        )
        brief = planner.build_creative_brief(req)
        plan = planner.plan_production_assets(brief)
        assert len(plan.assets) == 1


class TestBuildProductionBatch:
    def test_deterministic_output(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        b1 = planner.build_production_batch(plan, brief)
        b2 = planner.build_production_batch(plan, brief)
        # Different batch_ids (random), but same structure
        assert len(b1.tasks) == len(b2.tasks)
        assert b1.estimated_total_minutes == b2.estimated_total_minutes

    def test_batch_links_plan_and_brief(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        batch = planner.build_production_batch(plan, brief)
        assert batch.brief_id == brief.brief_id
        assert batch.plan_id == plan.plan_id

    def test_task_count_matches_assets(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        batch = planner.build_production_batch(plan, brief)
        assert len(batch.tasks) == len(plan.assets)

    def test_first_task_no_dependencies(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        batch = planner.build_production_batch(plan, brief)
        assert not batch.tasks[0].dependencies

    def test_subsequent_tasks_have_dependencies(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        batch = planner.build_production_batch(plan, brief)
        for i in range(1, len(batch.tasks)):
            assert batch.tasks[i].dependencies

    def test_parallel_sequential_count(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        batch = planner.build_production_batch(plan, brief)
        assert batch.parallelizable_count + batch.sequential_count == len(batch.tasks)
        assert batch.parallelizable_count == 1  # only first task no deps
        assert batch.sequential_count == len(batch.tasks) - 1

    def test_all_tasks_pending(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        batch = planner.build_production_batch(plan, brief)
        assert all(t.status == TaskStatus.PENDING for t in batch.tasks)

    def test_batch_status_planned(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        batch = planner.build_production_batch(plan, brief)
        assert batch.status == CreativeStatus.PLANNED

    def test_task_output_filenames(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        plan = planner.plan_production_assets(brief)
        batch = planner.build_production_batch(plan, brief)
        for t in batch.tasks:
            assert t.output_filename
            assert "." in t.output_filename


class TestPlanCreativeReview:
    def test_deterministic_output(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        r1 = planner.plan_creative_review(brief)
        r2 = planner.plan_creative_review(brief)
        assert len(r1.checkpoints) == len(r2.checkpoints)
        assert r1.verdict == r2.verdict

    def test_links_brief(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        review = planner.plan_creative_review(brief)
        assert review.brief_id == brief.brief_id

    def test_default_verdict_pending(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        review = planner.plan_creative_review(brief)
        assert review.verdict == ReviewVerdict.PENDING

    def test_reviewer_is_operator(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        review = planner.plan_creative_review(brief)
        assert review.reviewer == "operator"

    def test_has_multiple_checkpoints(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        review = planner.plan_creative_review(brief)
        assert len(review.checkpoints) >= 3

    def test_all_checkpoints_required(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        review = planner.plan_creative_review(brief)
        assert all(cp.required for cp in review.checkpoints)

    def test_all_checkpoints_have_criteria(self, planner, valid_request):
        brief = planner.build_creative_brief(valid_request)
        review = planner.plan_creative_review(brief)
        for cp in review.checkpoints:
            assert cp.label
            assert len(cp.criteria) > 0


class TestValidateCreativePackage:
    def test_valid_full_package(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        assert pkg.status == PackageStatus.VALIDATED
        assert not pkg.validation_errors

    def test_empty_package_has_errors(self, planner):
        pkg = CreativePackage()
        result = planner.validate_creative_package(pkg)
        assert len(result.validation_errors) >= 3
        assert any("MISSING_BRIEF" in e for e in result.validation_errors)
        assert any("MISSING_ASSET_PLAN" in e for e in result.validation_errors)
        assert any("MISSING_BATCH" in e for e in result.validation_errors)

    def test_brief_missing_topic(self, planner):
        pkg = CreativePackage(
            brief=CreativeBriefV2(request_id="r", account_handle="@a", topic="", objective=""),
            asset_plan=ProductionAssetPlan(brief_id="b", assets=[AssetSpec(asset_index=0)]),
            batch=ProductionBatch(brief_id="b", tasks=[CreativeTask(asset_index=0)]),
        )
        result = planner.validate_creative_package(pkg)
        assert "BRIEF_MISSING_TOPIC" in result.validation_errors
        assert "BRIEF_MISSING_OBJECTIVE" in result.validation_errors

    def test_empty_asset_plan_warns(self, planner):
        pkg = CreativePackage(
            brief=CreativeBriefV2(request_id="r", account_handle="@a", topic="t", objective="o"),
            asset_plan=ProductionAssetPlan(brief_id="b"),
            batch=ProductionBatch(brief_id="b", tasks=[CreativeTask(asset_index=0)]),
        )
        result = planner.validate_creative_package(pkg)
        assert any("ASSET_PLAN_EMPTY" in w for w in result.validation_warnings)

    def test_missing_review_plan_warns(self, planner):
        pkg = CreativePackage(
            brief=CreativeBriefV2(request_id="r", account_handle="@a", topic="t", objective="o"),
            asset_plan=ProductionAssetPlan(brief_id="b", assets=[AssetSpec(asset_index=0)]),
            batch=ProductionBatch(brief_id="b", tasks=[CreativeTask(asset_index=0)]),
        )
        result = planner.validate_creative_package(pkg)
        assert any("MISSING_REVIEW_PLAN" in w for w in result.validation_warnings)


class TestExportCreativePackageMarkdown:
    def test_returns_non_empty_string(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        md = planner.export_creative_package_markdown(pkg)
        assert isinstance(md, str)
        assert len(md) > 100

    def test_includes_package_id(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        md = planner.export_creative_package_markdown(pkg)
        assert pkg.package_id in md

    def test_includes_brief_section(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        md = planner.export_creative_package_markdown(pkg)
        assert "## Creative Brief V2" in md
        assert pkg.brief.topic in md

    def test_includes_asset_plan_table(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        md = planner.export_creative_package_markdown(pkg)
        assert "## Production Asset Plan" in md

    def test_includes_batch_table(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        md = planner.export_creative_package_markdown(pkg)
        assert "## Production Batch" in md

    def test_includes_review_section(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        md = planner.export_creative_package_markdown(pkg)
        assert "## Creative Review Plan" in md

    def test_includes_validation_section(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        md = planner.export_creative_package_markdown(pkg)
        assert "## Validation" in md

    def test_dry_run_notice_present(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        md = planner.export_creative_package_markdown(pkg)
        assert "Dry-run only" in md

    def test_deterministic_output(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        md1 = planner.export_creative_package_markdown(pkg)
        md2 = planner.export_creative_package_markdown(pkg)
        assert md1 == md2

    def test_empty_package_handles_gracefully(self, planner):
        pkg = CreativePackage()
        pkg = planner.validate_creative_package(pkg)
        md = planner.export_creative_package_markdown(pkg)
        assert len(md) > 0
        assert "## Validation" in md

    def test_includes_checkpoints_with_checkboxes(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        md = planner.export_creative_package_markdown(pkg)
        assert "- [ ]" in md


class TestPlanFromRequest:
    def test_returns_validated_package(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        assert isinstance(pkg, CreativePackage)
        assert pkg.status == PackageStatus.VALIDATED

    def test_deterministic_given_same_request(self, planner, valid_request):
        pkg1 = planner.plan_from_request(valid_request)
        pkg2 = planner.plan_from_request(valid_request)
        assert pkg1.brief.hook_variants == pkg2.brief.hook_variants
        assert pkg1.brief.shot_list == pkg2.brief.shot_list
        assert pkg1.asset_plan.total_estimated_minutes == pkg2.asset_plan.total_estimated_minutes
        assert pkg1.batch.parallelizable_count == pkg2.batch.parallelizable_count

    def test_all_sections_present(self, planner, valid_request):
        pkg = planner.plan_from_request(valid_request)
        assert pkg.brief is not None
        assert pkg.asset_plan is not None
        assert pkg.batch is not None
        assert pkg.review_plan is not None

    def test_minimal_request_works(self, planner):
        req = CreativeRequest(
            account_handle="@test",
            topic="Teste rápido",
            objective="Validar pipeline",
        )
        pkg = planner.plan_from_request(req)
        assert pkg.status == PackageStatus.VALIDATED
        assert pkg.brief.topic == "Teste rápido"

    def test_all_formats_work(self, planner):
        for fmt in CreativeFormat:
            req = CreativeRequest(
                account_handle="@test",
                topic=f"Test {fmt.value}",
                objective="Test all formats",
                format=fmt,
            )
            pkg = planner.plan_from_request(req)
            assert pkg.brief.format == fmt
            assert len(pkg.batch.tasks) > 0

    def test_varying_asset_counts(self, planner):
        for count in [1, 3, 7, 10]:
            req = CreativeRequest(
                account_handle="@test",
                topic="test",
                objective="test",
                asset_count=count,
            )
            pkg = planner.plan_from_request(req)
            assert len(pkg.asset_plan.assets) == count
            assert len(pkg.batch.tasks) == count
