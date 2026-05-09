"""Tests for campaign_package models."""
from src.campaign_package.models import Campaign, CampaignPost, CampaignStatus


class TestCampaignPost:
    def test_to_dict_has_required_keys(self):
        p = CampaignPost(post_number=1, title="Post 01")
        d = p.to_dict()
        assert "post_number" in d
        assert "title" in d
        assert "status" in d
        assert "scheduled_date" in d

    def test_default_status_is_draft(self):
        p = CampaignPost(post_number=1, title="x")
        assert p.status == "draft"


class TestCampaign:
    def test_to_dict_has_required_keys(self):
        c = Campaign(
            campaign_id="c1", name="test", post_count=10,
            status=CampaignStatus.DRAFT, account_handle="afamiliatigrereal",
            created_at="2026-05-09T00:00:00Z", output_dir="/tmp/c1",
        )
        d = c.to_dict()
        assert "campaign_id" in d
        assert "name" in d
        assert "post_count" in d
        assert "status" in d
        assert "posts" in d

    def test_status_value_is_string(self):
        c = Campaign(
            campaign_id="c1", name="test", post_count=5,
            status=CampaignStatus.READY, account_handle="x",
            created_at="2026-05-09T00:00:00Z", output_dir="/tmp",
        )
        d = c.to_dict()
        assert d["status"] == "ready"

    def test_posts_list_in_dict(self):
        c = Campaign(
            campaign_id="c1", name="test", post_count=2,
            status=CampaignStatus.DRAFT, account_handle="x",
            created_at="2026-05-09T00:00:00Z", output_dir="/tmp",
            posts=[CampaignPost(1, "P1"), CampaignPost(2, "P2")],
        )
        d = c.to_dict()
        assert len(d["posts"]) == 2
