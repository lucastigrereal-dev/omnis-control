"""Tests for campaign_package exporter."""
import json
from pathlib import Path

from src.campaign_package.exporter import export_campaign
from src.campaign_package.models import Campaign, CampaignPost, CampaignStatus


def _make_campaign(tmp_path) -> tuple:
    out_dir = tmp_path / "camp_test"
    posts = [CampaignPost(i, f"Post {i:02d}", scheduled_date=f"2026-06-{i:02d}") for i in range(1, 4)]
    campaign = Campaign(
        campaign_id="campaign_test001",
        name="Campanha Natal",
        post_count=3,
        status=CampaignStatus.DRAFT,
        account_handle="afamiliatigrereal",
        created_at="2026-05-09T00:00:00Z",
        output_dir=str(out_dir),
        posts=posts,
    )
    return campaign, out_dir


class TestExportCampaign:
    def test_creates_output_dir(self, tmp_path):
        c, out_dir = _make_campaign(tmp_path)
        export_campaign(c, out_dir)
        assert out_dir.is_dir()

    def test_manifest_created(self, tmp_path):
        c, out_dir = _make_campaign(tmp_path)
        export_campaign(c, out_dir)
        assert (out_dir / "campaign_manifest.json").is_file()

    def test_manifest_is_valid_json(self, tmp_path):
        c, out_dir = _make_campaign(tmp_path)
        export_campaign(c, out_dir)
        data = json.loads((out_dir / "campaign_manifest.json").read_text(encoding="utf-8"))
        assert data["campaign_id"] == "campaign_test001"

    def test_calendar_csv_created(self, tmp_path):
        c, out_dir = _make_campaign(tmp_path)
        export_campaign(c, out_dir)
        assert (out_dir / "calendar.csv").is_file()

    def test_calendar_has_header(self, tmp_path):
        c, out_dir = _make_campaign(tmp_path)
        export_campaign(c, out_dir)
        content = (out_dir / "calendar.csv").read_text(encoding="utf-8")
        assert "post_number" in content

    def test_readme_created(self, tmp_path):
        c, out_dir = _make_campaign(tmp_path)
        export_campaign(c, out_dir)
        assert (out_dir / "README.md").is_file()

    def test_posts_dirs_created(self, tmp_path):
        c, out_dir = _make_campaign(tmp_path)
        export_campaign(c, out_dir)
        posts_dir = out_dir / "posts"
        assert posts_dir.is_dir()
        assert (posts_dir / "post_01").is_dir()
        assert (posts_dir / "post_03").is_dir()

    def test_checklist_created(self, tmp_path):
        c, out_dir = _make_campaign(tmp_path)
        export_campaign(c, out_dir)
        assert (out_dir / "publishing_checklist.md").is_file()

    def test_returns_list_of_filenames(self, tmp_path):
        c, out_dir = _make_campaign(tmp_path)
        created = export_campaign(c, out_dir)
        assert isinstance(created, list)
        assert len(created) > 0
