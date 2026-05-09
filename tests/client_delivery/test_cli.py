"""Tests for delivery CLI commands."""
import json
import pytest
from typer.testing import CliRunner
from unittest.mock import patch

import src.cli_commands.delivery_cmd as delivery_cmd_mod
from src.cli_commands.delivery_cmd import delivery_app
from src.client_delivery.models import Delivery, DeliverySource, DeliveryStatus
from src.client_delivery.errors import DeliveryNotFoundError, DeliverySourceError


runner = CliRunner()


def _fake_delivery():
    return Delivery(
        delivery_id="delivery_abc12345",
        source_type=DeliverySource.PACKAGE,
        source_id="carousel_0b79aa1c_fake",
        status=DeliveryStatus.READY,
        output_dir="/tmp/delivery_abc12345",
        created_at="2026-05-09T00:00:00Z",
        files_generated=["README_CLIENTE.md", "delivery_manifest.json"],
    )


class TestDeliveryCreateCmd:
    def test_from_package_success(self):
        with patch.object(delivery_cmd_mod, "delivery_svc") as mock_svc:
            mock_svc.create_delivery_from_package.return_value = _fake_delivery()
            result = runner.invoke(delivery_app, ["create", "--from-package", "carousel_0b79aa1c"])
        assert result.exit_code == 0
        assert "delivery_abc12345" in result.output

    def test_from_campaign_success(self):
        with patch.object(delivery_cmd_mod, "delivery_svc") as mock_svc:
            mock_svc.create_delivery_from_campaign.return_value = _fake_delivery()
            result = runner.invoke(delivery_app, ["create", "--from-campaign", "campaign_abc"])
        assert result.exit_code == 0

    def test_no_source_exits_nonzero(self):
        result = runner.invoke(delivery_app, ["create"])
        assert result.exit_code != 0

    def test_source_error_exits_nonzero(self):
        with patch.object(delivery_cmd_mod, "delivery_svc") as mock_svc:
            mock_svc.create_delivery_from_package.side_effect = DeliverySourceError("not found")
            result = runner.invoke(delivery_app, ["create", "--from-package", "bad_id"])
        assert result.exit_code != 0


class TestDeliveryListCmd:
    def test_empty_message_when_none(self):
        with patch.object(delivery_cmd_mod, "delivery_svc") as mock_svc:
            mock_svc.list_deliveries.return_value = []
            result = runner.invoke(delivery_app, ["list"])
        assert "Nenhuma" in result.output

    def test_shows_delivery_ids(self):
        with patch.object(delivery_cmd_mod, "delivery_svc") as mock_svc:
            mock_svc.list_deliveries.return_value = [_fake_delivery().to_dict()]
            result = runner.invoke(delivery_app, ["list"])
        assert "delivery_abc12345" in result.output


class TestDeliveryShowCmd:
    def test_not_found_exits_nonzero(self):
        with patch.object(delivery_cmd_mod, "delivery_svc") as mock_svc:
            mock_svc.get_delivery.return_value = None
            result = runner.invoke(delivery_app, ["show", "bad_id"])
        assert result.exit_code != 0

    def test_shows_json_when_found(self):
        with patch.object(delivery_cmd_mod, "delivery_svc") as mock_svc:
            mock_svc.get_delivery.return_value = _fake_delivery().to_dict()
            result = runner.invoke(delivery_app, ["show", "delivery_abc"])
        data = json.loads(result.output)
        assert data["delivery_id"] == "delivery_abc12345"


class TestDeliveryZipCmd:
    def test_zip_success(self):
        with patch.object(delivery_cmd_mod, "delivery_svc") as mock_svc:
            mock_svc.zip_delivery.return_value = {"delivery_id": "d1", "zip_path": "/tmp/d1.zip", "size_kb": 3.1}
            result = runner.invoke(delivery_app, ["zip", "delivery_abc"])
        assert result.exit_code == 0
        assert "ZIP" in result.output

    def test_not_found_exits_nonzero(self):
        with patch.object(delivery_cmd_mod, "delivery_svc") as mock_svc:
            mock_svc.zip_delivery.side_effect = DeliveryNotFoundError("not found")
            result = runner.invoke(delivery_app, ["zip", "bad_id"])
        assert result.exit_code != 0
