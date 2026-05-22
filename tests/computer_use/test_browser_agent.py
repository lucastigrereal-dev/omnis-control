"""Tests for BrowserAgent + InstagramScout."""
from __future__ import annotations

import pytest

from src.computer_use.browser_agent import (
    BrowserAgent,
    InstagramScout,
    InstagramPost,
    ProfileData,
    MOCK_INSTAGRAM_POSTS,
)


class TestInstagramPost:
    def test_post_defaults(self):
        post = InstagramPost(handle="@test", caption="Test caption")
        assert post.post_id.startswith("ig_")
        assert post.media_type == "image"
        assert post.likes == 0

    def test_post_engagement_rate(self):
        post = InstagramPost(likes=15000, comments=300)
        assert post.engagement_rate == 15.3

    def test_post_to_dict(self):
        post = InstagramPost(
            handle="@test",
            caption="Test caption",
            likes=1000,
            comments=50,
            hashtags=["viagem", "brasil"],
            media_type="carousel",
        )
        d = post.to_dict()
        assert d["handle"] == "@test"
        assert d["hashtags"] == ["viagem", "brasil"]
        assert d["media_type"] == "carousel"
        assert "engagement_rate" in d

    def test_post_caption_truncated_in_dict(self):
        post = InstagramPost(handle="@test", caption="A" * 300)
        d = post.to_dict()
        assert len(d["caption"]) <= 200


class TestProfileData:
    def test_profile_defaults(self):
        p = ProfileData(handle="@test")
        assert p.handle == "@test"
        assert p.followers == 0
        assert p.recent_posts == []

    def test_profile_to_dict(self):
        p = ProfileData(
            handle="@lucastigrereal",
            full_name="Lucas Tigre",
            followers=690000,
            is_verified=True,
        )
        d = p.to_dict()
        assert d["followers"] == 690000
        assert d["is_verified"] is True


class TestBrowserAgent:
    def test_defaults_to_dry_run(self):
        agent = BrowserAgent()
        assert agent.dry_run is True

    def test_search_instagram_mock(self):
        agent = BrowserAgent(dry_run=True)
        results = agent.search_instagram("viagem")
        assert len(results) > 0
        assert all(isinstance(p, InstagramPost) for p in results)

    def test_search_instagram_respects_limit(self):
        agent = BrowserAgent(dry_run=True)
        results = agent.search_instagram("viagem", limit=2)
        assert len(results) <= 2

    def test_search_instagram_hashtags_match(self):
        agent = BrowserAgent(dry_run=True)
        results = agent.search_instagram("gastronomia")
        assert any("gastronomia" in p.hashtags for p in results)

    def test_search_instagram_natal(self):
        agent = BrowserAgent(dry_run=True)
        results = agent.search_instagram("natal")
        assert any("natal" in p.handle.lower() for p in results)

    def test_search_instagram_fallback_no_match(self):
        agent = BrowserAgent(dry_run=True)
        results = agent.search_instagram("tópico inexistente")
        assert len(results) > 0  # fallback returns generic

    def test_search_logs_history(self):
        agent = BrowserAgent(dry_run=True)
        agent.search_instagram("viagem")
        agent.search_instagram("hotel")
        assert len(agent.search_history) == 2

    def test_scrape_profile_mock_known_handle(self):
        agent = BrowserAgent(dry_run=True)
        profile = agent.scrape_profile("lucastigrereal")
        assert profile.followers == 690000
        assert profile.is_verified is True
        assert len(profile.recent_posts) > 0

    def test_scrape_profile_mock_oinatalrn(self):
        agent = BrowserAgent(dry_run=True)
        profile = agent.scrape_profile("oinatalrn")
        assert profile.followers == 630000
        assert profile.is_verified is True

    def test_scrape_profile_mock_unknown_handle(self):
        agent = BrowserAgent(dry_run=True)
        profile = agent.scrape_profile("random_user_123")
        assert profile.handle == "random_user_123"
        assert profile.followers > 0
        assert profile.is_verified is False

    def test_extract_trending_hooks(self):
        agent = BrowserAgent(dry_run=True)
        hooks = agent.extract_trending_hooks("viagem", top_n=3)
        assert len(hooks) > 0
        for h in hooks:
            assert "hook" in h
            assert "engagement" in h

    def test_extract_trending_hooks_sorted_by_engagement(self):
        agent = BrowserAgent(dry_run=True)
        hooks = agent.extract_trending_hooks("viagem", top_n=5)
        engagements = [h["engagement"] for h in hooks]
        assert engagements == sorted(engagements, reverse=True)

    def test_monitor_competitor(self):
        agent = BrowserAgent(dry_run=True)
        report = agent.monitor_competitor("oinatalrn")
        assert report["handle"] == "oinatalrn"
        assert report["followers"] == 630000
        assert "top_hooks" in report

    def test_is_mock(self):
        agent = BrowserAgent(dry_run=True)
        assert agent.is_mock is True

    def test_known_hashtags(self):
        agent = BrowserAgent()
        assert "viagem" in agent.KNOWN_HASHTAGS
        assert "hotel" in agent.KNOWN_HASHTAGS
        assert "familia" in agent.KNOWN_HASHTAGS

    def test_known_handles_include_omnis_profiles(self):
        agent = BrowserAgent()
        assert "lucastigrereal" in agent.KNOWN_HANDLES
        assert "oinatalrn" in agent.KNOWN_HANDLES
        assert "afamiliatigrereal" in agent.KNOWN_HANDLES


class TestInstagramScout:
    def test_scout_defaults(self):
        scout = InstagramScout(dry_run=True)
        assert scout.browser.dry_run is True

    def test_scout_accepts_custom_browser(self):
        browser = BrowserAgent(dry_run=True)
        scout = InstagramScout(browser=browser)
        assert scout.browser is browser

    def test_scout_niche(self):
        scout = InstagramScout(dry_run=True)
        report = scout.scout_niche("viagem")
        assert report["niche"] == "viagem"
        assert report["posts_analyzed"] > 0
        assert len(report["top_hooks"]) > 0
        assert "trending_hashtags" in report

    def test_scout_niche_returns_hashtags(self):
        scout = InstagramScout(dry_run=True)
        report = scout.scout_niche("viagem")
        assert any("viagem" in h for h in report["trending_hashtags"])

    def test_scout_tracks_reports(self):
        scout = InstagramScout(dry_run=True)
        scout.scout_niche("viagem")
        scout.scout_niche("hotel")
        assert scout.report_count == 2

    def test_research_content_gap(self):
        scout = InstagramScout(dry_run=True)
        gap = scout.research_content_gap("hotel", own_handle="lucastigrereal")
        assert gap["niche"] == "hotel"
        assert gap["own_followers"] == 690000
        assert len(gap["competitor_handles"]) > 0
        assert "recommendation" in gap

    def test_research_content_gap_excludes_own_handle(self):
        scout = InstagramScout(dry_run=True)
        gap = scout.research_content_gap("natal", own_handle="lucastigrereal")
        for handle in gap["competitor_handles"]:
            assert handle.lstrip("@") != "lucastigrereal"


class TestMockData:
    def test_mock_has_all_niches(self):
        assert "viagem" in MOCK_INSTAGRAM_POSTS
        assert "gastronomia" in MOCK_INSTAGRAM_POSTS
        assert "hotel" in MOCK_INSTAGRAM_POSTS
        assert "natal" in MOCK_INSTAGRAM_POSTS
        assert "familia" in MOCK_INSTAGRAM_POSTS

    def test_mock_posts_have_handles(self):
        for niche, posts in MOCK_INSTAGRAM_POSTS.items():
            for post in posts:
                assert post.handle, f"{niche} post missing handle"

    def test_mock_posts_have_hashtags(self):
        for niche, posts in MOCK_INSTAGRAM_POSTS.items():
            for post in posts:
                assert len(post.hashtags) > 0, f"{niche} post has no hashtags"
