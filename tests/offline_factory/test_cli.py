"""Tests for offline_factory CLI commands."""
import json
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from src.cli_commands.offline_factory_cmd import offline_app
from src.offline_factory.models import DeliveryPackage, PackageType, PackageStatus
import src.offline_factory.packager as packager_mod

runner = CliRunner()

FAKE_PKG = DeliveryPackage(
    package_id="carousel_0b79aa1c_20260508_120000",
    package_type=PackageType.CAROUSEL,
    title="Carousel — alcance — 0b79aa1c",
    account_handle="afamiliatigrereal",
    source_queue_id="0b79aa1c",
    source_caption_id="1d482d82",
    output_dir="/tmp/offline_factory/carousel_0b79aa1c",
    files=["caption.md", "slides_outline.md", "manifest.json"],
    status=PackageStatus.PARTIAL,
    warnings=["Nenhum asset atribuido"],
    blockers=[],
    next_actions=["Atribuir asset"],
    manifest_path="/tmp/offline_factory/carousel_0b79aa1c/manifest.json",
)

FAKE_PKG_BLOCKED = DeliveryPackage(
    package_id="carousel_nocap_20260508_120000",
    package_type=PackageType.CAROUSEL,
    title="Carousel Package — nocap",
    account_handle="desconhecido",
    source_queue_id="nocap",
    status=PackageStatus.BLOCKED,
    blockers=["Caption ausente"],
    output_dir="/tmp/offline_factory/carousel_nocap",
    manifest_path="/tmp/offline_factory/carousel_nocap/manifest.json",
)

FAKE_REELS_PKG = DeliveryPackage(
    package_id="reels_0b79aa1c_20260508_120000",
    package_type=PackageType.REELS_SCRIPT,
    title="Reels Script — alcance — 0b79aa1c",
    account_handle="afamiliatigrereal",
    source_queue_id="0b79aa1c",
    source_caption_id="1d482d82",
    output_dir="/tmp/offline_factory/reels_0b79aa1c",
    files=["script.md", "shot_list.md", "manifest.json"],
    status=PackageStatus.PARTIAL,
    warnings=["Nenhum asset atribuido"],
    blockers=[],
    manifest_path="/tmp/offline_factory/reels_0b79aa1c/manifest.json",
)


class TestHelpCommand:
    def test_help_exits_zero(self):
        result = runner.invoke(offline_app, ["--help"])
        assert result.exit_code == 0

    def test_help_shows_commands(self):
        result = runner.invoke(offline_app, ["--help"])
        assert "package-carousel" in result.output
        assert "package-reels" in result.output
        assert "list" in result.output
        assert "show" in result.output

    def test_never_mention_publish_in_help(self):
        result = runner.invoke(offline_app, ["--help"])
        assert "publica" not in result.output.lower() or "nunca" in result.output.lower() or "nunca" in result.output.lower()


class TestPackageCarouselCmd:
    def test_runs_successfully(self):
        with patch("src.cli_commands.offline_factory_cmd.create_carousel_package", return_value=FAKE_PKG):
            result = runner.invoke(offline_app, ["package-carousel", "0b79aa1c"])
        assert result.exit_code == 0

    def test_shows_package_id(self):
        with patch("src.cli_commands.offline_factory_cmd.create_carousel_package", return_value=FAKE_PKG):
            result = runner.invoke(offline_app, ["package-carousel", "0b79aa1c"])
        assert "carousel_0b79aa1c" in result.output

    def test_shows_status(self):
        with patch("src.cli_commands.offline_factory_cmd.create_carousel_package", return_value=FAKE_PKG):
            result = runner.invoke(offline_app, ["package-carousel", "0b79aa1c"])
        assert "partial" in result.output

    def test_shows_blockers_when_blocked(self):
        with patch("src.cli_commands.offline_factory_cmd.create_carousel_package", return_value=FAKE_PKG_BLOCKED):
            result = runner.invoke(offline_app, ["package-carousel", "nocap"])
        assert "Caption ausente" in result.output

    def test_json_output(self):
        with patch("src.cli_commands.offline_factory_cmd.create_carousel_package", return_value=FAKE_PKG):
            result = runner.invoke(offline_app, ["package-carousel", "0b79aa1c", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["package_id"] == FAKE_PKG.package_id

    def test_exit_code_1_on_error(self):
        with patch("src.cli_commands.offline_factory_cmd.create_carousel_package", side_effect=RuntimeError("boom")):
            result = runner.invoke(offline_app, ["package-carousel", "bad_id"])
        assert result.exit_code == 1


class TestPackageReelsCmd:
    def test_runs_successfully(self):
        with patch("src.cli_commands.offline_factory_cmd.create_reels_script_package", return_value=FAKE_REELS_PKG):
            result = runner.invoke(offline_app, ["package-reels", "0b79aa1c"])
        assert result.exit_code == 0

    def test_shows_package_id(self):
        with patch("src.cli_commands.offline_factory_cmd.create_reels_script_package", return_value=FAKE_REELS_PKG):
            result = runner.invoke(offline_app, ["package-reels", "0b79aa1c"])
        assert "reels_0b79aa1c" in result.output

    def test_json_output(self):
        with patch("src.cli_commands.offline_factory_cmd.create_reels_script_package", return_value=FAKE_REELS_PKG):
            result = runner.invoke(offline_app, ["package-reels", "0b79aa1c", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["package_type"] == "reels_script_package"


class TestListCmd:
    def test_empty_list(self):
        with patch("src.cli_commands.offline_factory_cmd.list_packages", return_value=[]):
            result = runner.invoke(offline_app, ["list"])
        assert result.exit_code == 0

    def test_shows_packages(self):
        fake_list = [
            {
                "package_id": "carousel_abc_20260508",
                "package_type": "carousel_package",
                "account_handle": "afamiliatigrereal",
                "status": "partial",
                "files": ["a.md", "b.md"],
                "generated_at": "2026-05-08T12:00:00Z",
            }
        ]
        with patch("src.cli_commands.offline_factory_cmd.list_packages", return_value=fake_list):
            result = runner.invoke(offline_app, ["list"])
        assert result.exit_code == 0
        assert "carousel_abc" in result.output

    def test_json_output(self):
        fake_list = [{"package_id": "p1", "status": "partial"}]
        with patch("src.cli_commands.offline_factory_cmd.list_packages", return_value=fake_list):
            result = runner.invoke(offline_app, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["package_id"] == "p1"


class TestShowCmd:
    def test_shows_package_details(self):
        fake_list = [
            {
                "package_id": "carousel_0b79aa1c_20260508",
                "package_type": "carousel_package",
                "title": "Carrossel Natal",
                "account_handle": "afamiliatigrereal",
                "source_queue_id": "0b79aa1c",
                "source_caption_id": "1d482d82",
                "status": "partial",
                "files": [{"name": "caption.md", "size_bytes": 120}],
                "warnings": ["Nenhum asset"],
                "blockers": [],
                "next_actions": ["Atribuir asset"],
                "generated_at": "2026-05-08T12:00:00Z",
            }
        ]
        with patch("src.cli_commands.offline_factory_cmd.list_packages", return_value=fake_list):
            result = runner.invoke(offline_app, ["show", "carousel_0b79aa1c"])
        assert result.exit_code == 0
        assert "afamiliatigrereal" in result.output
        assert "partial" in result.output

    def test_not_found_exit_1(self):
        with patch("src.cli_commands.offline_factory_cmd.list_packages", return_value=[]):
            result = runner.invoke(offline_app, ["show", "doesnotexist"])
        assert result.exit_code == 1

    def test_json_output(self):
        fake_list = [
            {"package_id": "carousel_abc", "status": "partial", "account_handle": "x"}
        ]
        with patch("src.cli_commands.offline_factory_cmd.list_packages", return_value=fake_list):
            result = runner.invoke(offline_app, ["show", "carousel_abc", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "partial"
