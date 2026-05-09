"""Tests for campaign_auditor service."""
import json
import pytest
from pathlib import Path

import src.campaign_auditor.service as aud_svc
from src.campaign_auditor.service import audit_campaign, audit_all_campaigns, CampaignNotFoundError


def _make_campaign(root: Path, campaign_id: str, posts: list[dict]) -> Path:
    d = root / campaign_id
    d.mkdir(parents=True, exist_ok=True)
    manifest = {
        "campaign_id": campaign_id,
        "name": f"Campaign {campaign_id}",
        "account_handle": "afamiliatigrereal",
        "post_count": len(posts),
        "status": "draft",
        "posts": posts,
    }
    (d / "campaign_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return d


def _make_package(root: Path, pkg_id: str, status: str = "ready", has_caption: bool = True, has_asset: bool = True) -> Path:
    d = root / pkg_id
    d.mkdir(parents=True, exist_ok=True)
    manifest = {
        "package_id": pkg_id,
        "package_type": "carousel_package",
        "status": status,
        "account_handle": "afamiliatigrereal",
        "asset_id": "mock_001" if has_asset else None,
    }
    (d / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    if has_caption:
        (d / "caption.md").write_text("Test caption content.", encoding="utf-8")
    (d / "publishing_checklist.md").write_text("- [ ] Post\n", encoding="utf-8")
    return d


@pytest.fixture
def patched_roots(tmp_path, monkeypatch):
    campaigns = tmp_path / "campaigns"
    packages = tmp_path / "packages"
    renders = tmp_path / "renders"
    monkeypatch.setattr(aud_svc, "CAMPAIGNS_ROOT", campaigns)
    monkeypatch.setattr(aud_svc, "PACKAGES_ROOT", packages)
    monkeypatch.setattr(aud_svc, "RENDER_ROOT", renders)
    return campaigns, packages, renders


class TestAuditCampaign:
    def test_raises_when_campaign_not_found(self, patched_roots):
        campaigns, _, _ = patched_roots
        with pytest.raises(CampaignNotFoundError):
            audit_campaign("nonexistent_campaign")

    def test_unscored_posts_when_no_packages(self, patched_roots):
        campaigns, _, _ = patched_roots
        _make_campaign(campaigns, "campaign_001", posts=[
            {"post_number": 1, "title": "Post 1", "package_id": None},
            {"post_number": 2, "title": "Post 2", "package_id": None},
        ])
        result = audit_campaign("campaign_001")
        assert result.total_posts == 2
        assert result.scored_posts == 0
        assert result.unscored_posts == 2
        assert result.avg_score is None

    def test_scores_packages_when_present(self, patched_roots):
        campaigns, packages, _ = patched_roots
        pkg = _make_package(packages, "pkg_001")
        _make_campaign(campaigns, "campaign_002", posts=[
            {"post_number": 1, "title": "Post 1", "package_id": "pkg_001"},
        ])
        result = audit_campaign("campaign_002")
        assert result.scored_posts == 1
        assert result.avg_score is not None
        assert 0 <= result.avg_score <= 100

    def test_mixed_posts_scored_and_unscored(self, patched_roots):
        campaigns, packages, _ = patched_roots
        _make_package(packages, "pkg_abc")
        _make_campaign(campaigns, "campaign_003", posts=[
            {"post_number": 1, "title": "Post 1", "package_id": "pkg_abc"},
            {"post_number": 2, "title": "Post 2", "package_id": None},
        ])
        result = audit_campaign("campaign_003")
        assert result.total_posts == 2
        assert result.scored_posts == 1
        assert result.unscored_posts == 1

    def test_result_has_correct_campaign_fields(self, patched_roots):
        campaigns, _, _ = patched_roots
        _make_campaign(campaigns, "campaign_004", posts=[])
        result = audit_campaign("campaign_004")
        assert result.campaign_id == "campaign_004"
        assert result.account_handle == "afamiliatigrereal"

    def test_overall_grade_unscored_when_no_packages(self, patched_roots):
        campaigns, _, _ = patched_roots
        _make_campaign(campaigns, "campaign_005", posts=[])
        result = audit_campaign("campaign_005")
        assert result.overall_grade() == "unscored"

    def test_to_dict_has_required_keys(self, patched_roots):
        campaigns, _, _ = patched_roots
        _make_campaign(campaigns, "campaign_006", posts=[])
        result = audit_campaign("campaign_006")
        d = result.to_dict()
        for key in ("campaign_id", "avg_score", "overall_grade", "entries", "errors"):
            assert key in d

    def test_no_network_calls(self, patched_roots):
        from unittest.mock import patch
        campaigns, _, _ = patched_roots
        _make_campaign(campaigns, "campaign_007", posts=[])
        with patch("requests.post") as mock:
            audit_campaign("campaign_007")
            mock.assert_not_called()


class TestAuditAllCampaigns:
    def test_returns_empty_when_no_campaigns(self, patched_roots):
        assert audit_all_campaigns() == []

    def test_returns_result_per_campaign(self, patched_roots):
        campaigns, _, _ = patched_roots
        _make_campaign(campaigns, "campaign_a", posts=[])
        _make_campaign(campaigns, "campaign_b", posts=[])
        results = audit_all_campaigns()
        assert len(results) == 2

    def test_skips_dirs_without_manifest(self, patched_roots):
        campaigns, _, _ = patched_roots
        _make_campaign(campaigns, "campaign_good", posts=[])
        bad = campaigns / "no_manifest_dir"
        bad.mkdir(parents=True)
        results = audit_all_campaigns()
        assert len(results) == 1
