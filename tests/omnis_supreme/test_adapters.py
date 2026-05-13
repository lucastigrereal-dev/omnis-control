"""Tests for P20 adapter registry — each adapter validated individually."""
from __future__ import annotations

import pytest

from src.omnis_supreme.adapters import ADAPTER_REGISTRY
from src.omnis_supreme.errors import StepAdapterError


class TestAdapterRegistryStructure:
    def test_registry_has_eight_adapters(self):
        assert len(ADAPTER_REGISTRY) == 8

    def test_all_keys_are_tuple_str_str(self):
        for key in ADAPTER_REGISTRY:
            assert isinstance(key, tuple)
            assert len(key) == 2
            assert isinstance(key[0], str)
            assert isinstance(key[1], str)

    def test_all_values_are_callable(self):
        for key, fn in ADAPTER_REGISTRY.items():
            assert callable(fn), f"Adapter {key} is not callable"


class TestBuildCampaignBriefAdapter:
    def test_returns_dict(self):
        fn = ADAPTER_REGISTRY[("P5", "build_campaign_brief")]
        result = fn({"name": "test-brief"}, {})
        assert isinstance(result, dict)

    def test_has_id_field(self):
        fn = ADAPTER_REGISTRY[("P5", "build_campaign_brief")]
        result = fn({"name": "test"}, {})
        assert "id" in result

    def test_has_name_field(self):
        fn = ADAPTER_REGISTRY[("P5", "build_campaign_brief")]
        result = fn({"name": "my-campaign"}, {})
        assert result.get("name") == "my-campaign"

    def test_accepts_dry_run_config(self):
        fn = ADAPTER_REGISTRY[("P5", "build_campaign_brief")]
        result = fn({"name": "dry", "dry_run": True}, {})
        assert isinstance(result, dict)


class TestOrchestrateCampaignAdapter:
    def test_returns_dict(self):
        fn = ADAPTER_REGISTRY[("P19", "orchestrate_campaign")]
        result = fn({"name": "test-campaign"}, {})
        assert isinstance(result, dict)

    def test_has_campaign_id(self):
        fn = ADAPTER_REGISTRY[("P19", "orchestrate_campaign")]
        result = fn({"name": "test"}, {})
        assert "campaign_id" in result

    def test_has_status_field(self):
        fn = ADAPTER_REGISTRY[("P19", "orchestrate_campaign")]
        result = fn({"name": "test"}, {})
        assert "status" in result


class TestAllocateBudgetAdapter:
    def test_returns_dict(self):
        fn = ADAPTER_REGISTRY[("P19", "allocate_budget")]
        result = fn({"name": "bgt", "total_budget_brl": 5000.0}, {})
        assert isinstance(result, dict)

    def test_has_budget_id(self):
        fn = ADAPTER_REGISTRY[("P19", "allocate_budget")]
        result = fn({}, {})
        assert "budget_id" in result or "id" in result

    def test_has_total_allocated(self):
        fn = ADAPTER_REGISTRY[("P19", "allocate_budget")]
        result = fn({}, {})
        assert "allocated_brl" in result


class TestCalculateRoiAdapter:
    def test_returns_dict(self):
        fn = ADAPTER_REGISTRY[("P19", "calculate_roi")]
        result = fn({"name": "roi"}, {})
        assert isinstance(result, dict)

    def test_has_roi_id(self):
        fn = ADAPTER_REGISTRY[("P19", "calculate_roi")]
        result = fn({}, {})
        assert "roi_id" in result


class TestBuildPublishQueuePlanAdapter:
    def test_returns_dict(self):
        fn = ADAPTER_REGISTRY[("P19", "build_publish_queue_plan")]
        result = fn({"name": "pq"}, {})
        assert isinstance(result, dict)

    def test_has_plan_id(self):
        fn = ADAPTER_REGISTRY[("P19", "build_publish_queue_plan")]
        result = fn({}, {})
        assert "plan_id" in result


class TestValidatePublishReadinessAdapter:
    def test_returns_dict(self):
        fn = ADAPTER_REGISTRY[("P8", "validate_publish_readiness")]
        result = fn({"caption": "Test post"}, {})
        assert isinstance(result, dict)

    def test_has_item_id(self):
        fn = ADAPTER_REGISTRY[("P8", "validate_publish_readiness")]
        result = fn({}, {})
        assert "item_id" in result or "check_id" in result or "id" in result

    def test_accepts_custom_caption(self):
        fn = ADAPTER_REGISTRY[("P8", "validate_publish_readiness")]
        result = fn({"caption": "My custom caption"}, {})
        assert isinstance(result, dict)


class TestBuildDeliveryPackageAdapter:
    def test_returns_dict(self):
        fn = ADAPTER_REGISTRY[("P17", "build_delivery_package")]
        result = fn({"lead_id": "lead_test"}, {})
        assert isinstance(result, dict)

    def test_has_package_id(self):
        fn = ADAPTER_REGISTRY[("P17", "build_delivery_package")]
        result = fn({"lead_id": "lead_x"}, {})
        assert "package_id" in result or "id" in result


class TestGenerateManifestAdapter:
    def test_returns_dict(self):
        fn = ADAPTER_REGISTRY[("P19", "generate_manifest")]
        result = fn({"name": "def"}, {})
        assert isinstance(result, dict)

    def test_has_manifest_version(self):
        fn = ADAPTER_REGISTRY[("P19", "generate_manifest")]
        result = fn({}, {})
        assert "manifest_version" in result or "version" in result or "generated_by" in result


class TestAdapterMissing:
    def test_missing_adapter_not_in_registry(self):
        assert ("P99", "nonexistent") not in ADAPTER_REGISTRY
