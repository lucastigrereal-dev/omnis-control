"""Tests for campaign_package service."""
import json
import pytest
from pathlib import Path

from src.campaign_package.errors import CampaignNotFoundError, CampaignValidationError
from src.campaign_package.models import CampaignStatus
from src.campaign_package.service import (
    create_campaign, list_campaigns, get_campaign, validate_campaign, zip_campaign
)


class TestCreateCampaign:
    def test_returns_campaign(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("test_camp", count=10, campaigns_root=root)
        assert c.campaign_id.startswith("campaign_")

    def test_status_is_ready(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("test_camp", count=10, campaigns_root=root)
        assert c.status == CampaignStatus.READY

    def test_correct_post_count(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("test_camp", count=10, campaigns_root=root)
        assert c.post_count == 10
        assert len(c.posts) == 10

    def test_custom_count(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("test", count=5, campaigns_root=root)
        assert c.post_count == 5

    def test_output_dir_created(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("test_camp", count=10, campaigns_root=root)
        assert Path(c.output_dir).is_dir()

    def test_manifest_json_on_disk(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("test_camp", count=10, campaigns_root=root)
        manifest_path = Path(c.output_dir) / "campaign_manifest.json"
        assert manifest_path.is_file()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert data["post_count"] == 10

    def test_calendar_csv_on_disk(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("test_camp", count=10, campaigns_root=root)
        assert (Path(c.output_dir) / "calendar.csv").is_file()

    def test_readme_on_disk(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("test_camp", count=10, campaigns_root=root)
        assert (Path(c.output_dir) / "README.md").is_file()

    def test_posts_dirs_created(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("test_camp", count=3, campaigns_root=root)
        posts_dir = Path(c.output_dir) / "posts"
        assert posts_dir.is_dir()
        assert (posts_dir / "post_01").is_dir()
        assert (posts_dir / "post_03").is_dir()

    def test_raises_when_count_zero(self, patched_campaign_root):
        root, _ = patched_campaign_root
        with pytest.raises(CampaignValidationError):
            create_campaign("test", count=0, campaigns_root=root)

    def test_raises_when_count_too_large(self, patched_campaign_root):
        root, _ = patched_campaign_root
        with pytest.raises(CampaignValidationError):
            create_campaign("test", count=51, campaigns_root=root)

    def test_no_meta_calls(self, patched_campaign_root):
        from unittest.mock import patch
        root, _ = patched_campaign_root
        with patch("requests.post") as mock_post:
            create_campaign("test_camp", count=10, campaigns_root=root)
            mock_post.assert_not_called()

    def test_no_secret_in_files(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("test_camp", count=10, campaigns_root=root)
        for f in Path(c.output_dir).rglob("*"):
            if f.is_file() and f.suffix in (".json", ".md", ".csv"):
                content = f.read_text(encoding="utf-8")
                for secret in ["access_token", "META_APP_SECRET", "client_secret"]:
                    assert secret not in content


class TestListCampaigns:
    def test_empty_when_no_campaigns(self, patched_campaign_root):
        root, _ = patched_campaign_root
        result = list_campaigns(campaigns_root=root)
        assert result == []

    def test_lists_created_campaigns(self, patched_campaign_root):
        root, _ = patched_campaign_root
        create_campaign("camp1", count=5, campaigns_root=root)
        create_campaign("camp2", count=3, campaigns_root=root)
        result = list_campaigns(campaigns_root=root)
        assert len(result) == 2

    def test_returns_dicts(self, patched_campaign_root):
        root, _ = patched_campaign_root
        create_campaign("camp1", count=5, campaigns_root=root)
        result = list_campaigns(campaigns_root=root)
        assert isinstance(result[0], dict)
        assert "campaign_id" in result[0]


class TestGetCampaign:
    def test_returns_none_when_not_found(self, patched_campaign_root):
        root, _ = patched_campaign_root
        assert get_campaign("nonexistent", campaigns_root=root) is None

    def test_returns_dict_when_found(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("camp1", count=5, campaigns_root=root)
        result = get_campaign(c.campaign_id, campaigns_root=root)
        assert result is not None
        assert result["campaign_id"] == c.campaign_id


class TestValidateCampaign:
    def test_valid_campaign_passes(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("camp1", count=5, campaigns_root=root)
        result = validate_campaign(c.campaign_id, campaigns_root=root)
        assert result["is_valid"] is True

    def test_raises_when_not_found(self, patched_campaign_root):
        root, _ = patched_campaign_root
        with pytest.raises(CampaignNotFoundError):
            validate_campaign("nonexistent", campaigns_root=root)

    def test_checks_passed_not_empty(self, patched_campaign_root):
        root, _ = patched_campaign_root
        c = create_campaign("camp1", count=5, campaigns_root=root)
        result = validate_campaign(c.campaign_id, campaigns_root=root)
        assert len(result["checks_passed"]) > 0


class TestZipCampaign:
    def test_zip_created(self, patched_campaign_root):
        root, zips_root = patched_campaign_root
        c = create_campaign("camp1", count=5, campaigns_root=root)
        result = zip_campaign(c.campaign_id, campaigns_root=root, zips_root=zips_root)
        assert Path(result["zip_path"]).is_file()

    def test_zip_has_size(self, patched_campaign_root):
        root, zips_root = patched_campaign_root
        c = create_campaign("camp1", count=5, campaigns_root=root)
        result = zip_campaign(c.campaign_id, campaigns_root=root, zips_root=zips_root)
        assert result["size_kb"] > 0

    def test_raises_when_not_found(self, patched_campaign_root):
        root, zips_root = patched_campaign_root
        with pytest.raises(CampaignNotFoundError):
            zip_campaign("nonexistent", campaigns_root=root, zips_root=zips_root)
