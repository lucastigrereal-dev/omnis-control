"""Tests for Creative Production V2 models."""
from __future__ import annotations

import pytest

from src.creative_production_v2.models import (
    AssetSpec,
    AssetType,
    CreativeBriefV2,
    CreativeFormat,
    CreativePackage,
    CreativeRequest,
    CreativeReviewPlan,
    CreativeStatus,
    CreativeTask,
    PackageStatus,
    ProductionAssetPlan,
    ProductionBatch,
    ReviewCheckpoint,
    ReviewVerdict,
    TaskStatus,
)


class TestCreativeRequest:
    def test_default_creation(self):
        req = CreativeRequest()
        assert req.request_id
        assert len(req.request_id) == 8
        assert req.format == CreativeFormat.CAROUSEL
        assert req.status == CreativeStatus.DRAFT
        assert req.asset_count == 3
        assert req.deadline_days == 7
        assert isinstance(req.tags, list)
        assert isinstance(req.metadata, dict)

    def test_full_creation(self):
        req = CreativeRequest(
            account_handle="@lucastigrereal",
            format=CreativeFormat.REEL,
            topic="viagem em família para Natal",
            objective="Vender pacote Growth R$990",
            tone="inspirador",
            target_audience="Famílias com filhos",
            key_message="Viajar em família é mais barato do que parece",
            visual_style="praia",
            caption_seed="Família que viaja unida permanece unida",
            asset_count=5,
            deadline_days=3,
            priority=10,
            tags=["familia", "viagem", "natalrn"],
            metadata={"source": "sdr_outbound"},
        )
        assert req.account_handle == "@lucastigrereal"
        assert req.format == CreativeFormat.REEL
        assert req.asset_count == 5
        assert len(req.tags) == 3

    def test_to_dict_serializes_enums(self):
        req = CreativeRequest(
            account_handle="@lucastigrereal",
            format=CreativeFormat.REEL,
        )
        d = req.to_dict()
        assert d["format"] == "reel"
        assert d["status"] == "draft"
        assert isinstance(d["tags"], list)

    def test_from_dict_deserializes_enums(self):
        data = {
            "request_id": "abc12345",
            "account_handle": "@teste",
            "format": "reel",
            "status": "draft",
            "topic": "teste",
            "asset_count": 5,
        }
        req = CreativeRequest.from_dict(data)
        assert req.format == CreativeFormat.REEL
        assert req.status == CreativeStatus.DRAFT
        assert req.asset_count == 5

    def test_from_dict_ignores_unknown_fields(self):
        data = {"request_id": "xyz", "format": "carousel", "extra_field": "ignored"}
        req = CreativeRequest.from_dict(data)
        assert req.request_id == "xyz"


class TestCreativeBriefV2:
    def test_default_creation(self):
        brief = CreativeBriefV2()
        assert brief.brief_id
        assert len(brief.brief_id) == 8
        assert brief.format == CreativeFormat.CAROUSEL
        assert brief.status == CreativeStatus.DRAFT
        assert isinstance(brief.hook_variants, list)
        assert isinstance(brief.warnings, list)

    def test_full_creation(self):
        brief = CreativeBriefV2(
            request_id="req001",
            account_handle="@lucastigrereal",
            format=CreativeFormat.REEL,
            topic="teste",
            objective="vender",
            tone="urgente",
            hook_variants=["hook1", "hook2"],
            warnings=["MISSING_TOPIC"],
        )
        assert brief.hook_variants == ["hook1", "hook2"]
        assert brief.warnings == ["MISSING_TOPIC"]

    def test_to_from_dict_roundtrip(self):
        original = CreativeBriefV2(
            request_id="req001",
            account_handle="@teste",
            format=CreativeFormat.CAROUSEL,
            topic="tema teste",
            objective="objetivo teste",
            hook_variants=["h1", "h2"],
            color_palette=["#FFF", "#000"],
            status=CreativeStatus.PLANNED,
        )
        d = original.to_dict()
        restored = CreativeBriefV2.from_dict(d)
        assert restored.brief_id == original.brief_id
        assert restored.format == original.format
        assert restored.hook_variants == original.hook_variants
        assert restored.color_palette == original.color_palette


class TestAssetSpec:
    def test_default_creation(self):
        spec = AssetSpec()
        assert spec.asset_index == 0
        assert spec.asset_type == AssetType.IMAGE
        assert spec.dimensions == "1080x1080"

    def test_video_spec(self):
        spec = AssetSpec(
            asset_index=1,
            asset_type=AssetType.VIDEO,
            description="Cena principal",
            dimensions="1080x1920",
            duration_seconds=30.0,
        )
        assert spec.duration_seconds == 30.0


class TestProductionAssetPlan:
    def test_default_creation(self):
        plan = ProductionAssetPlan()
        assert plan.plan_id
        assert isinstance(plan.assets, list)
        assert plan.total_estimated_minutes == 0

    def test_with_assets(self):
        assets = [
            AssetSpec(asset_index=0, asset_type=AssetType.IMAGE),
            AssetSpec(asset_index=1, asset_type=AssetType.VIDEO),
        ]
        plan = ProductionAssetPlan(
            brief_id="brief001",
            assets=assets,
            total_estimated_minutes=30,
            tool_assignments={"asset_0": "canva", "asset_1": "capcut"},
        )
        assert len(plan.assets) == 2
        assert plan.tool_assignments["asset_0"] == "canva"

    def test_to_from_dict_roundtrip(self):
        plan = ProductionAssetPlan(
            brief_id="brief001",
            assets=[AssetSpec(asset_index=0, asset_type=AssetType.THUMBNAIL)],
            total_estimated_minutes=15,
            tool_assignments={"asset_0": "canva"},
        )
        d = plan.to_dict()
        restored = ProductionAssetPlan.from_dict(d)
        assert len(restored.assets) == 1
        assert restored.assets[0].asset_type == AssetType.THUMBNAIL


class TestCreativeTask:
    def test_default_creation(self):
        task = CreativeTask()
        assert task.task_id
        assert task.status == TaskStatus.PENDING
        assert task.estimated_minutes == 15

    def test_with_dependencies(self):
        task = CreativeTask(
            batch_id="batch01",
            brief_id="brief01",
            asset_index=2,
            asset_type=AssetType.TEXT_OVERLAY,
            dependencies=["task_0", "task_1"],
            tool_target="canva",
        )
        assert task.dependencies == ["task_0", "task_1"]
        assert task.tool_target == "canva"

    def test_to_from_dict_roundtrip(self):
        task = CreativeTask(
            batch_id="batch01",
            brief_id="brief01",
            asset_index=0,
            asset_type=AssetType.IMAGE,
            dependencies=[],
            status=TaskStatus.IN_PROGRESS,
        )
        d = task.to_dict()
        assert d["status"] == "in_progress"
        restored = CreativeTask.from_dict(d)
        assert restored.status == TaskStatus.IN_PROGRESS


class TestProductionBatch:
    def test_default_creation(self):
        batch = ProductionBatch()
        assert batch.batch_id
        assert isinstance(batch.tasks, list)
        assert batch.status == CreativeStatus.PLANNED

    def test_with_tasks(self):
        tasks = [
            CreativeTask(asset_index=0, asset_type=AssetType.IMAGE),
            CreativeTask(asset_index=1, asset_type=AssetType.VIDEO, dependencies=["task_0"]),
        ]
        batch = ProductionBatch(
            brief_id="brief01",
            plan_id="plan01",
            tasks=tasks,
            estimated_total_minutes=30,
            parallelizable_count=1,
            sequential_count=1,
        )
        assert len(batch.tasks) == 2
        assert batch.parallelizable_count == 1

    def test_to_from_dict_roundtrip(self):
        tasks = [CreativeTask(asset_index=0, asset_type=AssetType.IMAGE)]
        batch = ProductionBatch(
            brief_id="brief01",
            plan_id="plan01",
            tasks=tasks,
            estimated_total_minutes=15,
            parallelizable_count=1,
            sequential_count=0,
        )
        d = batch.to_dict()
        restored = ProductionBatch.from_dict(d)
        assert len(restored.tasks) == 1
        assert restored.estimated_total_minutes == 15


class TestReviewCheckpoint:
    def test_default_creation(self):
        cp = ReviewCheckpoint()
        assert cp.checkpoint_index == 0
        assert cp.required is True
        assert cp.auto_pass is False

    def test_with_criteria(self):
        cp = ReviewCheckpoint(
            checkpoint_index=1,
            label="Brand Safety",
            criteria=["No hate speech", "Tone matches brand"],
        )
        assert len(cp.criteria) == 2


class TestCreativeReviewPlan:
    def test_default_creation(self):
        rp = CreativeReviewPlan()
        assert rp.review_id
        assert rp.verdict == ReviewVerdict.PENDING
        assert rp.reviewer == "operator"

    def test_with_checkpoints(self):
        checkpoints = [
            ReviewCheckpoint(checkpoint_index=0, label="Hook", criteria=["Is it catchy?"]),
            ReviewCheckpoint(checkpoint_index=1, label="CTA", criteria=["Is it clear?"]),
        ]
        rp = CreativeReviewPlan(
            brief_id="brief01",
            checkpoints=checkpoints,
            verdict=ReviewVerdict.APPROVED,
        )
        assert len(rp.checkpoints) == 2
        assert rp.verdict == ReviewVerdict.APPROVED

    def test_to_from_dict_roundtrip(self):
        rp = CreativeReviewPlan(
            brief_id="brief01",
            checkpoints=[ReviewCheckpoint(checkpoint_index=0, label="Hook", criteria=["test"])],
            verdict=ReviewVerdict.CHANGES_REQUESTED,
            notes="Fix CTA text",
        )
        d = rp.to_dict()
        restored = CreativeReviewPlan.from_dict(d)
        assert restored.verdict == ReviewVerdict.CHANGES_REQUESTED
        assert len(restored.checkpoints) == 1


class TestCreativePackage:
    def test_default_creation(self):
        pkg = CreativePackage()
        assert pkg.package_id
        assert pkg.status == PackageStatus.DRAFT
        assert isinstance(pkg.validation_errors, list)
        assert isinstance(pkg.validation_warnings, list)

    def test_full_package(self):
        pkg = CreativePackage(
            brief=CreativeBriefV2(
                request_id="req01",
                account_handle="@teste",
                topic="test",
                objective="test",
            ),
            asset_plan=ProductionAssetPlan(
                brief_id="brief01",
                assets=[AssetSpec(asset_index=0)],
            ),
            batch=ProductionBatch(
                brief_id="brief01",
                tasks=[CreativeTask(asset_index=0)],
            ),
            review_plan=CreativeReviewPlan(brief_id="brief01"),
            status=PackageStatus.VALIDATED,
        )
        assert pkg.brief is not None
        assert pkg.asset_plan is not None
        assert pkg.batch is not None
        assert pkg.review_plan is not None

    def test_to_from_dict_roundtrip(self):
        pkg = CreativePackage(
            brief=CreativeBriefV2(
                request_id="req01",
                account_handle="@teste",
                topic="t",
                objective="o",
            ),
            asset_plan=ProductionAssetPlan(
                brief_id="b01",
                assets=[AssetSpec(asset_index=0)],
            ),
            batch=ProductionBatch(
                brief_id="b01",
                tasks=[CreativeTask(asset_index=0)],
            ),
            review_plan=CreativeReviewPlan(brief_id="b01"),
            status=PackageStatus.READY,
            validation_errors=[],
            validation_warnings=["minor issue"],
        )
        d = pkg.to_dict()
        restored = CreativePackage.from_dict(d)
        assert restored.package_id == pkg.package_id
        assert restored.status == PackageStatus.READY
        assert restored.brief.topic == "t"
        assert len(restored.asset_plan.assets) == 1
        assert len(restored.batch.tasks) == 1
        assert restored.review_plan.brief_id == "b01"
        assert restored.validation_warnings == ["minor issue"]

    def test_package_without_optionals(self):
        pkg = CreativePackage()
        d = pkg.to_dict()
        assert "brief" not in d
        restored = CreativePackage.from_dict(d)
        assert restored.brief is None
        assert restored.asset_plan is None


class TestEnums:
    def test_creative_format_values(self):
        assert CreativeFormat.CAROUSEL.value == "carousel"
        assert CreativeFormat.REEL.value == "reel"
        assert CreativeFormat.STORY.value == "story"
        assert CreativeFormat.MULTI_COPY.value == "multi_copy"

    def test_creative_status_values(self):
        assert CreativeStatus.DRAFT.value == "draft"
        assert CreativeStatus.READY.value == "ready"
        assert CreativeStatus.ARCHIVED.value == "archived"

    def test_asset_type_values(self):
        assert AssetType.IMAGE.value == "image"
        assert AssetType.VIDEO.value == "video"
        assert AssetType.TEXT_OVERLAY.value == "text_overlay"

    def test_task_status_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.BLOCKED.value == "blocked"

    def test_review_verdict_values(self):
        assert ReviewVerdict.APPROVED.value == "approved"
        assert ReviewVerdict.CHANGES_REQUESTED.value == "changes_requested"

    def test_package_status_values(self):
        assert PackageStatus.DRAFT.value == "draft"
        assert PackageStatus.EXPORTED.value == "exported"
