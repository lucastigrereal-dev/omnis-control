"""Tests for campaign CLI commands."""
import json
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

import src.cli_commands.campaign_cmd as campaign_cmd_mod
from src.cli_commands.campaign_cmd import campaign_app
from src.campaign_package.models import Campaign, CampaignPost, CampaignStatus
from src.campaign_package.errors import CampaignNotFoundError, CampaignValidationError


runner = CliRunner()


def _fake_campaign():
    return Campaign(
        campaign_id="campaign_abc12345",
        name="test_camp",
        post_count=10,
        status=CampaignStatus.READY,
        account_handle="afamiliatigrereal",
        created_at="2026-05-09T00:00:00Z",
        output_dir="/tmp/campaign_abc12345",
        posts=[CampaignPost(i, f"Post {i:02d}") for i in range(1, 11)],
    )


class TestCampaignCreateCmd:
    def test_success_exit_zero(self):
        with patch.object(campaign_cmd_mod, "campaign_svc") as mock_svc:
            mock_svc.create_campaign.return_value = _fake_campaign()
            result = runner.invoke(campaign_app, ["create", "--name", "test_camp"])
        assert result.exit_code == 0

    def test_success_shows_campaign_id(self):
        with patch.object(campaign_cmd_mod, "campaign_svc") as mock_svc:
            mock_svc.create_campaign.return_value = _fake_campaign()
            result = runner.invoke(campaign_app, ["create", "--name", "test_camp"])
        assert "campaign_abc12345" in result.output

    def test_validation_error_exits_nonzero(self):
        with patch.object(campaign_cmd_mod, "campaign_svc") as mock_svc:
            mock_svc.create_campaign.side_effect = CampaignValidationError("bad count")
            result = runner.invoke(campaign_app, ["create", "--count", "0"])
        assert result.exit_code != 0


class TestCampaignListCmd:
    def test_empty_message_when_no_campaigns(self):
        with patch.object(campaign_cmd_mod, "campaign_svc") as mock_svc:
            mock_svc.list_campaigns.return_value = []
            result = runner.invoke(campaign_app, ["list"])
        assert "Nenhuma" in result.output

    def test_shows_campaign_id_when_exists(self):
        with patch.object(campaign_cmd_mod, "campaign_svc") as mock_svc:
            mock_svc.list_campaigns.return_value = [_fake_campaign().to_dict()]
            result = runner.invoke(campaign_app, ["list"])
        assert "campaign_abc12345" in result.output


class TestCampaignShowCmd:
    def test_not_found_exits_nonzero(self):
        with patch.object(campaign_cmd_mod, "campaign_svc") as mock_svc:
            mock_svc.get_campaign.return_value = None
            result = runner.invoke(campaign_app, ["show", "bad_id"])
        assert result.exit_code != 0

    def test_shows_json_when_found(self):
        with patch.object(campaign_cmd_mod, "campaign_svc") as mock_svc:
            mock_svc.get_campaign.return_value = _fake_campaign().to_dict()
            result = runner.invoke(campaign_app, ["show", "campaign_abc"])
        data = json.loads(result.output)
        assert data["campaign_id"] == "campaign_abc12345"


class TestCampaignValidateCmd:
    def test_valid_shows_success(self):
        with patch.object(campaign_cmd_mod, "campaign_svc") as mock_svc:
            mock_svc.validate_campaign.return_value = {
                "campaign_id": "campaign_abc12345",
                "is_valid": True,
                "checks_passed": ["manifest_exists"],
                "checks_failed": [],
                "post_count": 10,
            }
            result = runner.invoke(campaign_app, ["validate", "campaign_abc"])
        assert result.exit_code == 0
        assert "valida" in result.output.lower()

    def test_not_found_exits_nonzero(self):
        with patch.object(campaign_cmd_mod, "campaign_svc") as mock_svc:
            mock_svc.validate_campaign.side_effect = CampaignNotFoundError("not found")
            result = runner.invoke(campaign_app, ["validate", "bad_id"])
        assert result.exit_code != 0


class TestCampaignZipCmd:
    def test_zip_success(self):
        with patch.object(campaign_cmd_mod, "campaign_svc") as mock_svc:
            mock_svc.zip_campaign.return_value = {"campaign_id": "c1", "zip_path": "/tmp/c1.zip", "size_kb": 5.2}
            result = runner.invoke(campaign_app, ["zip", "campaign_abc"])
        assert result.exit_code == 0
        assert "ZIP" in result.output

    def test_not_found_exits_nonzero(self):
        with patch.object(campaign_cmd_mod, "campaign_svc") as mock_svc:
            mock_svc.zip_campaign.side_effect = CampaignNotFoundError("not found")
            result = runner.invoke(campaign_app, ["zip", "bad_id"])
        assert result.exit_code != 0
