"""PublerClient — HTTP client for Publer API (mock-first, real when API key set)."""
from __future__ import annotations

import json
import uuid
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


# ── Models ──────────────────────────────────────────────────────────────────

@dataclass
class PublerMedia:
    media_id: str = ""
    url: str = ""
    media_type: str = "image"  # image | video
    status: str = "ready"

    def to_dict(self) -> dict:
        return {"id": self.media_id, "url": self.url, "type": self.media_type, "status": self.status}


@dataclass
class PublerPost:
    post_id: str = ""
    caption: str = ""
    media: list[PublerMedia] = field(default_factory=list)
    account_id: str = ""
    scheduled_at: str | None = None
    state: str = "draft"  # draft | scheduled | published | failed
    networks: dict = field(default_factory=lambda: {"instagram": {"type": "photo"}})
    job_id: str = ""
    created_at: str = field(default_factory=_now_iso)
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "post_id": self.post_id,
            "caption": self.caption,
            "media": [m.to_dict() for m in self.media],
            "account_id": self.account_id,
            "scheduled_at": self.scheduled_at,
            "state": self.state,
            "networks": self.networks,
            "job_id": self.job_id,
            "created_at": self.created_at,
            "error": self.error,
        }


@dataclass
class PublerAccount:
    account_id: str = ""
    handle: str = ""
    provider: str = "instagram"
    account_type: str = "creator"
    status: str = "connected"

    def to_dict(self) -> dict:
        return {
            "id": self.account_id,
            "handle": self.handle,
            "provider": self.provider,
            "type": self.account_type,
            "status": self.status,
        }


@dataclass
class PublishResult:
    post_id: str = ""
    status: str = ""
    job_id: str = ""
    scheduled_at: str | None = None
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "post_id": self.post_id,
            "status": self.status,
            "job_id": self.job_id,
            "scheduled_at": self.scheduled_at,
            "error": self.error,
        }


# ── PublerClient ────────────────────────────────────────────────────────────

class PublerClient:
    """HTTP client for Publer API v1.

    Mock mode (api_key=""): returns realistic fake responses, logs all calls.
    Real mode (api_key set): calls https://app.publer.com/api/v1.
    """

    BASE_URL = "https://app.publer.com/api/v1"

    def __init__(self, api_key: str = "", workspace_id: str = ""):
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.calls: list[dict] = []
        self._mock_accounts: list[PublerAccount] = []
        self._mock_posts: dict[str, PublerPost] = {}
        self._mock_media: dict[str, PublerMedia] = {}

    @property
    def is_mock(self) -> bool:
        return not self.api_key

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer-API {self.api_key}",
            "Publer-Workspace-Id": self.workspace_id,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        """Single HTTP request with logging."""
        url = f"{self.BASE_URL}{path}"
        self.calls.append({"method": method, "url": url, "body": body, "mock": self.is_mock})

        if self.is_mock:
            return {"status": "ok"}

        data = json.dumps(body).encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"status": "error", "error": f"HTTP {e.code}: {e.reason}"}

    # ── Accounts ───────────────────────────────────────────────────────

    def _log_call(self, method: str, path: str, body: dict | None = None) -> None:
        self.calls.append({"method": method, "url": f"{self.BASE_URL}{path}", "body": body, "mock": self.is_mock})

    def list_accounts(self) -> list[PublerAccount]:
        self._log_call("GET", "/accounts")
        if self.is_mock:
            if not self._mock_accounts:
                self._mock_accounts = [
                    PublerAccount(account_id="acc_001", handle="lucastigrereal", provider="instagram", account_type="creator"),
                    PublerAccount(account_id="acc_002", handle="afamiliatigrereal", provider="instagram", account_type="creator"),
                    PublerAccount(account_id="acc_003", handle="oinatalrn", provider="instagram", account_type="business"),
                    PublerAccount(account_id="acc_004", handle="agenteviajabrasil", provider="instagram", account_type="business"),
                    PublerAccount(account_id="acc_005", handle="oquecomernatalrn", provider="instagram", account_type="creator"),
                    PublerAccount(account_id="acc_006", handle="natalaivoueu", provider="instagram", account_type="business"),
                ]
            return self._mock_accounts

        resp = self._request("GET", "/accounts")
        return [PublerAccount(**a) for a in resp.get("accounts", [])]

    def get_account_by_handle(self, handle: str) -> PublerAccount | None:
        handle_clean = handle.lstrip("@")
        for acc in self.list_accounts():
            if acc.handle == handle_clean:
                return acc
        return None

    # ── Media ──────────────────────────────────────────────────────────

    def upload_media_from_url(self, url: str, media_type: str = "image") -> PublerMedia:
        self._log_call("POST", "/media/from-url", {"url": url, "type": media_type})
        if self.is_mock:
            media = PublerMedia(media_id=_new_id("med_"), url=url, media_type=media_type)
            self._mock_media[media.media_id] = media
            return media

        resp = self._request("POST", "/media/from-url", {"url": url, "type": media_type})
        job_id = resp.get("job_id", "")
        if job_id:
            self._poll_job(job_id)
        media_id = resp.get("media_id", resp.get("id", ""))
        return PublerMedia(media_id=media_id, url=url, media_type=media_type)

    # ── Posts ──────────────────────────────────────────────────────────

    def schedule_post(
        self,
        caption: str,
        account_id: str,
        scheduled_at: str,
        media_ids: list[str] | None = None,
        post_type: str = "photo",
        state: str = "scheduled",
    ) -> PublishResult:
        """Create and schedule a post on Instagram via Publer."""
        media_payload = []
        if media_ids:
            media_payload = [{"id": mid, "type": "image"} for mid in media_ids]

        body = {
            "bulk": {
                "state": state,
                "posts": [{
                    "networks": {
                        "instagram": {
                            "type": post_type,
                            "text": caption,
                            "media": media_payload,
                        }
                    },
                    "accounts": [{
                        "id": account_id,
                        "scheduled_at": scheduled_at,
                    }],
                }],
            }
        }

        self._log_call("POST", "/posts/schedule", body)
        if self.is_mock:
            post_id = _new_id("pub_")
            job_id = _new_id("job_")
            post = PublerPost(
                post_id=post_id,
                caption=caption,
                media=[PublerMedia(media_id=mid) for mid in (media_ids or [])],
                account_id=account_id,
                scheduled_at=scheduled_at,
                state=state,
                job_id=job_id,
            )
            self._mock_posts[post_id] = post
            return PublishResult(post_id=post_id, status="scheduled", job_id=job_id, scheduled_at=scheduled_at)

        resp = self._request("POST", "/posts/schedule", body)
        job_id = resp.get("job_id", "")
        post_id = resp.get("post_id", resp.get("id", _new_id("pub_")))
        if job_id:
            job_status = self._poll_job(job_id)
            if job_status.get("status") == "failed":
                return PublishResult(status="failed", error=job_status.get("error", "unknown"))
        return PublishResult(post_id=post_id, status=state, job_id=job_id, scheduled_at=scheduled_at)

    def get_post(self, post_id: str) -> PublerPost | None:
        self._log_call("GET", f"/posts/{post_id}")
        if self.is_mock:
            return self._mock_posts.get(post_id)

        resp = self._request("GET", f"/posts/{post_id}")
        return PublerPost(**resp) if resp.get("post_id") else None

    def list_posts(self, state: str = "", account_id: str = "", limit: int = 20) -> list[PublerPost]:
        self._log_call("GET", "/posts")
        if self.is_mock:
            posts = list(self._mock_posts.values())
            if state:
                posts = [p for p in posts if p.state == state]
            if account_id:
                posts = [p for p in posts if p.account_id == account_id]
            return posts[:limit]

        params = []
        if state:
            params.append(f"state={state}")
        if account_id:
            params.append(f"account_ids[]={account_id}")
        params.append(f"page=1")
        path = f"/posts?{'&'.join(params)}"
        resp = self._request("GET", path)
        return [PublerPost(**p) for p in resp.get("posts", [])]

    # ── Jobs ───────────────────────────────────────────────────────────

    def get_job_status(self, job_id: str) -> dict:
        self._log_call("GET", f"/job_status/{job_id}")
        if self.is_mock:
            return {"job_id": job_id, "status": "complete"}

        return self._request("GET", f"/job_status/{job_id}")

    def _poll_job(self, job_id: str, max_attempts: int = 10, interval: float = 2.0) -> dict:
        import time
        for _ in range(max_attempts):
            status = self.get_job_status(job_id)
            if status.get("status") in ("complete", "failed", "cancelled"):
                return status
            time.sleep(interval)
        return {"job_id": job_id, "status": "timeout"}

    # ── Workspaces ─────────────────────────────────────────────────────

    def list_workspaces(self) -> list[dict]:
        self._log_call("GET", "/workspaces")
        if self.is_mock:
            return [{"id": "ws_001", "name": "Lucas Tigre Media"}]

        resp = self._request("GET", "/workspaces")
        return resp.get("workspaces", [])
