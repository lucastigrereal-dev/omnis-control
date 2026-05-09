"""Tests for client_delivery service."""
import json
import pytest
from pathlib import Path

from src.client_delivery.errors import DeliveryNotFoundError, DeliverySourceError
from src.client_delivery.models import DeliveryStatus
from src.client_delivery.service import (
    create_delivery_from_package,
    create_delivery_from_campaign,
    list_deliveries,
    get_delivery,
    zip_delivery,
)


class TestCreateFromPackage:
    def test_returns_delivery(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        d = create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root)
        assert d.delivery_id.startswith("delivery_")

    def test_status_ready(self, patched_roots):
        offline_root, _, delivery_root, _ = patched_roots
        d = create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root, offline_root=offline_root)
        assert d.status == DeliveryStatus.READY

    def test_output_dir_created(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        d = create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root)
        assert Path(d.output_dir).is_dir()

    def test_readme_cliente_created(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        d = create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root)
        assert (Path(d.output_dir) / "README_CLIENTE.md").is_file()

    def test_resumo_executivo_created(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        d = create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root)
        assert (Path(d.output_dir) / "RESUMO_EXECUTIVO.md").is_file()

    def test_manifest_created(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        d = create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root)
        manifest_path = Path(d.output_dir) / "delivery_manifest.json"
        assert manifest_path.is_file()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert data["delivery_id"] == d.delivery_id

    def test_raises_when_package_not_found(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        with pytest.raises(DeliverySourceError):
            create_delivery_from_package("nonexistent", delivery_root=delivery_root)

    def test_no_meta_calls(self, patched_roots):
        from unittest.mock import patch
        _, _, delivery_root, _ = patched_roots
        with patch("requests.post") as mock_post:
            create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root)
            mock_post.assert_not_called()

    def test_no_secrets_in_files(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        d = create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root)
        for f in Path(d.output_dir).rglob("*"):
            if f.is_file() and f.suffix in (".md", ".json"):
                content = f.read_text(encoding="utf-8")
                for secret in ["access_token", "META_APP_SECRET", "client_secret"]:
                    assert secret not in content


class TestCreateFromCampaign:
    def test_returns_delivery(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        d = create_delivery_from_campaign("campaign_abc12345", delivery_root=delivery_root)
        assert d.delivery_id.startswith("delivery_")

    def test_source_type_is_campaign(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        d = create_delivery_from_campaign("campaign_abc12345", delivery_root=delivery_root)
        from src.client_delivery.models import DeliverySource
        assert d.source_type == DeliverySource.CAMPAIGN

    def test_raises_when_campaign_not_found(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        with pytest.raises(DeliverySourceError):
            create_delivery_from_campaign("nonexistent", delivery_root=delivery_root)


class TestListDeliveries:
    def test_empty_when_none(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        result = list_deliveries(delivery_root=delivery_root)
        assert result == []

    def test_lists_after_create(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root)
        result = list_deliveries(delivery_root=delivery_root)
        assert len(result) == 1

    def test_returns_dicts(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root)
        result = list_deliveries(delivery_root=delivery_root)
        assert isinstance(result[0], dict)
        assert "delivery_id" in result[0]


class TestGetDelivery:
    def test_returns_none_when_not_found(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        result = get_delivery("nonexistent", delivery_root=delivery_root)
        assert result is None

    def test_returns_dict_when_found(self, patched_roots):
        _, _, delivery_root, _ = patched_roots
        d = create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root)
        result = get_delivery(d.delivery_id, delivery_root=delivery_root)
        assert result is not None
        assert result["delivery_id"] == d.delivery_id


class TestZipDelivery:
    def test_zip_created(self, patched_roots):
        _, _, delivery_root, zips_root = patched_roots
        d = create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root)
        result = zip_delivery(d.delivery_id, delivery_root=delivery_root, zips_root=zips_root)
        assert Path(result["zip_path"]).is_file()

    def test_zip_size_positive(self, patched_roots):
        _, _, delivery_root, zips_root = patched_roots
        d = create_delivery_from_package("carousel_0b79aa1c_fake", delivery_root=delivery_root)
        result = zip_delivery(d.delivery_id, delivery_root=delivery_root, zips_root=zips_root)
        assert result["size_kb"] > 0

    def test_raises_when_not_found(self, patched_roots):
        _, _, delivery_root, zips_root = patched_roots
        with pytest.raises(DeliveryNotFoundError):
            zip_delivery("nonexistent", delivery_root=delivery_root, zips_root=zips_root)
