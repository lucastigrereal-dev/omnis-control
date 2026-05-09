"""Tests for client_delivery models."""
from src.client_delivery.models import Delivery, DeliverySource, DeliveryStatus


class TestDelivery:
    def test_to_dict_has_required_keys(self):
        d = Delivery(
            delivery_id="d1", source_type=DeliverySource.PACKAGE,
            source_id="pkg1", status=DeliveryStatus.DRAFT,
            output_dir="/tmp/d1", created_at="2026-05-09T00:00:00Z",
        )
        data = d.to_dict()
        assert "delivery_id" in data
        assert "source_type" in data
        assert "source_id" in data
        assert "status" in data
        assert "files_generated" in data

    def test_status_value_is_string(self):
        d = Delivery(
            delivery_id="d1", source_type=DeliverySource.CAMPAIGN,
            source_id="c1", status=DeliveryStatus.READY,
            output_dir="/tmp", created_at="2026-05-09T00:00:00Z",
        )
        assert d.to_dict()["status"] == "ready"

    def test_source_type_value_is_string(self):
        d = Delivery(
            delivery_id="d1", source_type=DeliverySource.PACKAGE,
            source_id="p1", status=DeliveryStatus.DRAFT,
            output_dir="/tmp", created_at="2026-05-09T00:00:00Z",
        )
        assert d.to_dict()["source_type"] == "package"
