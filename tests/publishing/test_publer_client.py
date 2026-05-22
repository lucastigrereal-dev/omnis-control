"""Tests for PublerClient — mock-first HTTP client for Publer API."""
from __future__ import annotations

import pytest

from src.publishing.publer_client import (
    PublerClient,
    PublerPost,
    PublerMedia,
    PublerAccount,
    PublishResult,
)


class TestPublerClientMock:
    def test_client_is_mock_by_default(self):
        client = PublerClient()
        assert client.is_mock is True
        assert client.api_key == ""

    def test_client_real_when_api_key_set(self):
        client = PublerClient(api_key="pk_test_123")
        assert client.is_mock is False

    def test_list_accounts_returns_6_accounts(self):
        client = PublerClient()
        accounts = client.list_accounts()
        assert len(accounts) == 6
        assert accounts[0].handle == "lucastigrereal"
        assert accounts[0].provider == "instagram"

    def test_get_account_by_handle_strips_at(self):
        client = PublerClient()
        acc = client.get_account_by_handle("@lucastigrereal")
        assert acc is not None
        assert acc.handle == "lucastigrereal"
        assert acc.account_type == "creator"

    def test_get_account_by_handle_nonexistent(self):
        client = PublerClient()
        acc = client.get_account_by_handle("@nonexistent_user")
        assert acc is None

    def test_upload_media_from_url_mock(self):
        client = PublerClient()
        media = client.upload_media_from_url("https://example.com/photo.jpg")
        assert media.media_id.startswith("med_")
        assert media.url == "https://example.com/photo.jpg"
        assert media.media_type == "image"

    def test_schedule_post_mock(self):
        client = PublerClient()
        result = client.schedule_post(
            caption="Test caption",
            account_id="acc_001",
            scheduled_at="2026-05-25T09:00:00-03:00",
        )
        assert result.post_id.startswith("pub_")
        assert result.status == "scheduled"
        assert result.job_id.startswith("job_")
        assert result.scheduled_at == "2026-05-25T09:00:00-03:00"

    def test_schedule_post_with_media_mock(self):
        client = PublerClient()
        result = client.schedule_post(
            caption="Post with image",
            account_id="acc_001",
            scheduled_at="2026-05-25T09:00:00-03:00",
            media_ids=["med_001", "med_002"],
            post_type="carousel",
        )
        assert result.status == "scheduled"

    def test_get_post_mock(self):
        client = PublerClient()
        client.schedule_post(
            caption="Find me", account_id="acc_001",
            scheduled_at="2026-05-25T09:00:00-03:00",
        )
        # Get by the post_id from the result
        result = client.schedule_post(
            caption="Target", account_id="acc_001",
            scheduled_at="2026-05-25T10:00:00-03:00",
        )
        post = client.get_post(result.post_id)
        assert post is not None
        assert post.caption == "Target"

    def test_get_post_nonexistent(self):
        client = PublerClient()
        post = client.get_post("nonexistent")
        assert post is None

    def test_list_posts_filter_by_state(self):
        client = PublerClient()
        client.schedule_post(caption="A", account_id="acc_001", scheduled_at="2026-05-25T09:00:00-03:00")
        client.schedule_post(caption="B", account_id="acc_001", scheduled_at="2026-05-25T10:00:00-03:00")
        posts = client.list_posts(state="scheduled")
        assert len(posts) == 2

    def test_list_posts_filter_by_account(self):
        client = PublerClient()
        client.schedule_post(caption="A", account_id="acc_001", scheduled_at="2026-05-25T09:00:00-03:00")
        client.schedule_post(caption="B", account_id="acc_002", scheduled_at="2026-05-25T10:00:00-03:00")
        posts = client.list_posts(account_id="acc_001")
        assert len(posts) == 1
        assert posts[0].caption == "A"

    def test_list_posts_respects_limit(self):
        client = PublerClient()
        for i in range(10):
            client.schedule_post(caption=f"C{i}", account_id="acc_001", scheduled_at="2026-05-25T09:00:00-03:00")
        posts = client.list_posts(limit=3)
        assert len(posts) == 3

    def test_get_job_status_mock(self):
        client = PublerClient()
        status = client.get_job_status("job_test")
        assert status["status"] == "complete"
        assert status["job_id"] == "job_test"

    def test_list_workspaces_mock(self):
        client = PublerClient()
        workspaces = client.list_workspaces()
        assert len(workspaces) == 1
        assert workspaces[0]["name"] == "Lucas Tigre Media"

    def test_calls_are_logged(self):
        client = PublerClient()
        client.list_accounts()
        client.schedule_post(caption="X", account_id="acc_001", scheduled_at="2026-05-25T09:00:00-03:00")
        assert len(client.calls) == 2
        assert client.calls[0]["mock"] is True
        assert client.calls[1]["method"] == "POST"


class TestPublerModels:
    def test_publer_account_to_dict(self):
        acc = PublerAccount(account_id="acc_001", handle="test", provider="instagram", account_type="creator")
        d = acc.to_dict()
        assert d["id"] == "acc_001"
        assert d["handle"] == "test"

    def test_publer_media_to_dict(self):
        media = PublerMedia(media_id="med_001", url="http://x.com/1.jpg", media_type="image")
        d = media.to_dict()
        assert d["id"] == "med_001"
        assert d["type"] == "image"

    def test_publer_post_to_dict(self):
        post = PublerPost(
            post_id="pub_001",
            caption="Hello",
            account_id="acc_001",
            state="scheduled",
            job_id="job_001",
        )
        d = post.to_dict()
        assert d["post_id"] == "pub_001"
        assert d["caption"] == "Hello"
        assert d["state"] == "scheduled"

    def test_publish_result_to_dict(self):
        result = PublishResult(
            post_id="pub_001",
            status="scheduled",
            job_id="job_001",
            scheduled_at="2026-05-25T09:00:00-03:00",
        )
        d = result.to_dict()
        assert d["status"] == "scheduled"
        assert d["post_id"] == "pub_001"
