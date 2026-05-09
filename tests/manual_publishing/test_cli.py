"""Tests for manual_publish CLI."""
import json
import pytest
from typer.testing import CliRunner
from unittest.mock import patch

import src.cli_commands.manual_publish_cmd as pub_cmd_mod
from src.cli_commands.manual_publish_cmd import manual_publish_app
from src.manual_publishing.models import PublishRecord
from src.manual_publishing.errors import PublishRecordNotFoundError


runner = CliRunner()

FAKE_RECORD = PublishRecord(
    package_id="carousel_0b79aa1c",
    platform="instagram",
    posted_at="2026-05-09T10:00:00Z",
    posted_by="lucas",
    url="https://www.instagram.com/p/abc123/",
)


class TestMarkCmd:
    def test_success_exit_zero(self):
        with patch.object(pub_cmd_mod, "pub_svc") as mock_svc:
            mock_svc.mark_published.return_value = FAKE_RECORD
            result = runner.invoke(manual_publish_app, ["mark", "carousel_0b79aa1c"])
        assert result.exit_code == 0

    def test_shows_package_id(self):
        with patch.object(pub_cmd_mod, "pub_svc") as mock_svc:
            mock_svc.mark_published.return_value = FAKE_RECORD
            result = runner.invoke(manual_publish_app, ["mark", "carousel_0b79aa1c"])
        assert "carousel_0b79aa1c" in result.output

    def test_platform_option_accepted(self):
        with patch.object(pub_cmd_mod, "pub_svc") as mock_svc:
            mock_svc.mark_published.return_value = FAKE_RECORD
            result = runner.invoke(manual_publish_app, ["mark", "pkg1", "--platform", "tiktok"])
        assert result.exit_code == 0


class TestListCmd:
    def test_empty_message_when_no_records(self):
        with patch.object(pub_cmd_mod, "pub_svc") as mock_svc:
            mock_svc.list_published.return_value = []
            result = runner.invoke(manual_publish_app, ["list"])
        assert "Nenhum" in result.output

    def test_shows_package_ids(self):
        with patch.object(pub_cmd_mod, "pub_svc") as mock_svc:
            mock_svc.list_published.return_value = [FAKE_RECORD.to_dict()]
            result = runner.invoke(manual_publish_app, ["list"])
        assert "carousel_0b79aa1c" in result.output


class TestShowCmd:
    def test_not_found_exits_nonzero(self):
        with patch.object(pub_cmd_mod, "pub_svc") as mock_svc:
            mock_svc.get_published.side_effect = PublishRecordNotFoundError("not found")
            result = runner.invoke(manual_publish_app, ["show", "bad_id"])
        assert result.exit_code != 0

    def test_shows_json_when_found(self):
        with patch.object(pub_cmd_mod, "pub_svc") as mock_svc:
            mock_svc.get_published.return_value = FAKE_RECORD.to_dict()
            result = runner.invoke(manual_publish_app, ["show", "carousel_0b79aa1c"])
        data = json.loads(result.output)
        assert data["package_id"] == "carousel_0b79aa1c"
