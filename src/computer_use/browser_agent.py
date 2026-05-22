"""BrowserAgent — Instagram research + web automation via Playwright."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.computer_use.sandbox import SecuritySandbox


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str = "") -> str:
    import uuid
    return f"{prefix}{uuid.uuid4().hex[:8]}"


# ── Instagram-specific models ────────────────────────────────────────────


@dataclass
class InstagramPost:
    post_id: str = field(default_factory=lambda: _new_id("ig_"))
    handle: str = ""
    caption: str = ""
    likes: int = 0
    comments: int = 0
    hashtags: list[str] = field(default_factory=list)
    media_type: str = "image"  # image | video | carousel
    url: str = ""
    scraped_at: str = field(default_factory=_now_iso)

    @property
    def engagement_rate(self) -> float:
        """Fake engagement rate based on likes+comments."""
        return round((self.likes + self.comments) / 1000, 2)

    def to_dict(self) -> dict:
        return {
            "post_id": self.post_id,
            "handle": self.handle,
            "caption": self.caption[:200],
            "likes": self.likes,
            "comments": self.comments,
            "hashtags": self.hashtags,
            "media_type": self.media_type,
            "engagement_rate": self.engagement_rate,
            "scraped_at": self.scraped_at,
        }


@dataclass
class ProfileData:
    handle: str
    full_name: str = ""
    bio: str = ""
    followers: int = 0
    following: int = 0
    posts_count: int = 0
    is_verified: bool = False
    recent_posts: list[InstagramPost] = field(default_factory=list)
    scraped_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "handle": self.handle,
            "full_name": self.full_name,
            "bio": self.bio,
            "followers": self.followers,
            "following": self.following,
            "posts_count": self.posts_count,
            "is_verified": self.is_verified,
            "recent_posts": [p.to_dict() for p in self.recent_posts],
            "scraped_at": self.scraped_at,
        }


# ── Mock Instagram data ──────────────────────────────────────────────────


MOCK_INSTAGRAM_POSTS = {
    "viagem": [
        InstagramPost(
            handle="@viajandocomestilo",
            caption="Esse lugar parece Tailândia mas é Brasil! 🌴 Conhece alguém que precisa ver isso? Marca aqui! #viagem #brasil #paradise",
            likes=15420, comments=342, hashtags=["viagem", "brasil", "paradise"],
        ),
        InstagramPost(
            handle="@mochilaobrasil",
            caption="3 destinos no Brasil que custam MENOS que ir pra Europa. Arrasta pro lado! ✈️ #viagem #dicadeviagem #mochilao",
            likes=28300, comments=891, hashtags=["viagem", "dicadeviagem", "mochilao"],
            media_type="carousel",
        ),
        InstagramPost(
            handle="@nomadesdigitais",
            caption="Trabalhar remoto com essa vista... quem mais trocaria o escritório por isso? 💻🌊 #nomadedigital #viagem #remoto",
            likes=8700, comments=156, hashtags=["nomadedigital", "viagem", "remoto"],
        ),
    ],
    "gastronomia": [
        InstagramPost(
            handle="@comerbem",
            caption="O MELHOR restaurante escondido de SP que ninguém te contou. 10/10! 🍝 #gastronomia #sp #restaurante",
            likes=32100, comments=1204, hashtags=["gastronomia", "sp", "restaurante"],
        ),
        InstagramPost(
            handle="@foodtourbrasil",
            caption="Esse prato de R$ 35 vale mais que muito restaurante caro. CONFIA! 😋 #gastronomia #comida #barato",
            likes=18900, comments=567, hashtags=["gastronomia", "comida", "barato"],
        ),
    ],
    "hotel": [
        InstagramPost(
            handle="@hoteisdecharme",
            caption="Esse hotel fazenda no interior de SP é o refúgio que você precisa! 🏡 #hotel #fazenda #interiorsp",
            likes=12500, comments=298, hashtags=["hotel", "fazenda", "interiorsp"],
        ),
        InstagramPost(
            handle="@resortsbrasil",
            caption="Quarto com vista panorâmica: vale ou não o upgrade? Veja os detalhes! 👀 #hotel #resort #luxo",
            likes=9600, comments=234, hashtags=["hotel", "resort", "luxo"],
            media_type="reel",
        ),
    ],
    "natal": [
        InstagramPost(
            handle="@oinatalrn",
            caption="Natal é daqueles destinos que a gente guarda pra sempre 🌞 Quem mais ama essa cidade? #natal #rn #turismo",
            likes=45000, comments=2300, hashtags=["natal", "rn", "turismo"],
        ),
        InstagramPost(
            handle="@visitnatal",
            caption="5 praias em Natal que você precisa conhecer além de Ponta Negra! 🏖️ #natal #praia #rn",
            likes=22300, comments=876, hashtags=["natal", "praia", "rn"],
            media_type="carousel",
        ),
    ],
    "familia": [
        InstagramPost(
            handle="@afamiliatigrereal",
            caption="Viajar com filhos: o guia definitivo pra não surtar! 😅 #familia #viagem #crianças",
            likes=18700, comments=543, hashtags=["familia", "viagem", "crianças"],
        ),
    ],
}


# ── BrowserAgent ─────────────────────────────────────────────────────────


class BrowserAgent:
    """Instagram research agent — uses Playwright or mock data.

    Builds on BrowserExecutor for low-level browser control.
    Adds Instagram-specific knowledge: selectors, page structure, mock data.
    """

    INSTAGRAM_BASE = "https://www.instagram.com"
    KNOWN_HASHTAGS = list(MOCK_INSTAGRAM_POSTS.keys())
    KNOWN_HANDLES = [
        "lucastigrereal", "oinatalrn", "agenteviajabrasil",
        "afamiliatigrereal", "oquecomernatalrn", "natalaivoueu",
    ]

    def __init__(self, dry_run: bool = True, headless: bool = True):
        self.dry_run = dry_run
        self.headless = headless
        self.sandbox = SecuritySandbox(strict=True)
        self._searches: list[dict] = []
        self._mock = False

        try:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright
            self._pw_available = True
        except ImportError:
            self._playwright = None
            self._pw_available = False
            self._mock = True

    def _log_search(self, query: str, results_count: int) -> None:
        self._searches.append({
            "query": query,
            "results_count": results_count,
            "timestamp": _now_iso(),
        })

    def search_instagram(self, query: str, limit: int = 10) -> list[InstagramPost]:
        """Search Instagram posts by hashtag or keyword."""
        self.sandbox.validate_url(f"{self.INSTAGRAM_BASE}/explore/tags/{query}/")
        self.sandbox.validate_action("search_instagram")

        if self.dry_run or self._mock:
            return self._mock_search(query, limit)

        results: list[InstagramPost] = []
        try:
            pw = self._playwright().start()
            browser = pw.chromium.launch(headless=self.headless)
            page = browser.new_page()
            page.goto(f"{self.INSTAGRAM_BASE}/explore/tags/{query}/")
            time.sleep(2)

            posts = page.query_selector_all("article a")
            for post_el in posts[:limit]:
                href = post_el.get_attribute("href") or ""
                img = post_el.query_selector("img")
                alt = img.get_attribute("alt") if img else ""
                results.append(InstagramPost(
                    url=f"{self.INSTAGRAM_BASE}{href}",
                    caption=alt[:200] if alt else "",
                    hashtags=[query],
                ))

            browser.close()
        except Exception:
            pass

        self._log_search(query, len(results))
        return results if results else self._mock_search(query, limit)

    def _mock_search(self, query: str, limit: int) -> list[InstagramPost]:
        """Keyword-based mock search across MOCK_INSTAGRAM_POSTS."""
        import unicodedata
        def _strip(s: str) -> str:
            return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii').lower()
        q = _strip(query)
        results: list[InstagramPost] = []

        for niche, posts in MOCK_INSTAGRAM_POSTS.items():
            if niche in q or any(word in q for word in niche.split()):
                results.extend(posts)

        if not results:
            for posts in list(MOCK_INSTAGRAM_POSTS.values())[:2]:
                results.extend(posts[:2])

        self._log_search(query, len(results[:limit]))
        return results[:limit]

    def scrape_profile(self, handle: str) -> ProfileData:
        """Scrape public Instagram profile data."""
        handle_clean = handle.lstrip("@")
        self.sandbox.validate_url(f"{self.INSTAGRAM_BASE}/{handle_clean}/")
        self.sandbox.validate_action("scrape_profile")

        if self.dry_run or self._mock:
            return self._mock_profile(handle_clean)

        try:
            pw = self._playwright().start()
            browser = pw.chromium.launch(headless=self.headless)
            page = browser.new_page()
            page.goto(f"{self.INSTAGRAM_BASE}/{handle_clean}/")
            time.sleep(3)

            bio_el = page.query_selector("header section")
            bio = bio_el.inner_text() if bio_el else ""

            browser.close()
            return ProfileData(handle=handle_clean, bio=bio[:500])
        except Exception:
            return self._mock_profile(handle_clean)

    def _mock_profile(self, handle: str) -> ProfileData:
        if handle == "lucastigrereal":
            return ProfileData(
                handle="lucastigrereal",
                full_name="Lucas Tigre",
                bio="Viajante profissional | 690K | Família, viagem, gastronomia",
                followers=690000,
                following=1200,
                posts_count=3400,
                is_verified=True,
                recent_posts=MOCK_INSTAGRAM_POSTS.get("viagem", [])[:2],
            )
        elif handle == "oinatalrn":
            return ProfileData(
                handle="oinatalrn",
                full_name="O Inatal RN",
                bio="O melhor de Natal e RN | 630K seguidores",
                followers=630000,
                following=800,
                posts_count=5200,
                is_verified=True,
                recent_posts=MOCK_INSTAGRAM_POSTS.get("natal", [])[:2],
            )
        else:
            return ProfileData(
                handle=handle,
                full_name=handle.replace("_", " ").title(),
                bio=f"Perfil de {handle}",
                followers=random.randint(1000, 50000),
                following=random.randint(100, 2000),
                posts_count=random.randint(50, 2000),
                is_verified=False,
                recent_posts=[],
            )

    def extract_trending_hooks(self, hashtag: str, top_n: int = 5) -> list[dict]:
        """Search a hashtag and extract trending hooks/patterns from top posts."""
        posts = self.search_instagram(hashtag, limit=top_n * 2)
        hooks: list[dict] = []

        for post in posts:
            if post.caption:
                first_line = post.caption.split("\n")[0].strip()
                hooks.append({
                    "hook": first_line[:150],
                    "likes": post.likes,
                    "comments": post.comments,
                    "engagement": post.engagement_rate,
                    "handle": post.handle,
                })

        hooks.sort(key=lambda h: h["engagement"], reverse=True)
        return hooks[:top_n]

    def monitor_competitor(self, handle: str) -> dict:
        """Monitor a competitor's recent activity."""
        profile = self.scrape_profile(handle)
        posts = profile.recent_posts or self._mock_search(profile.bio[:50], 5)

        top_hooks = []
        for post in posts[:5]:
            if post.caption:
                top_hooks.append({
                    "hook": post.caption.split("\n")[0][:150],
                    "likes": post.likes,
                })

        return {
            "handle": handle,
            "followers": profile.followers,
            "recent_posts_count": len(profile.recent_posts) or len(posts),
            "top_hooks": top_hooks,
            "scraped_at": _now_iso(),
        }

    @property
    def search_history(self) -> list[dict]:
        return list(self._searches)

    @property
    def is_mock(self) -> bool:
        return self._mock or self.dry_run


class InstagramScout:
    """High-level Instagram research coordinator using BrowserAgent.

    Designed for content operations: find trending hooks, analyze competitors,
    extract patterns for the CaptionFactory pipeline.
    """

    def __init__(self, browser: BrowserAgent | None = None, dry_run: bool = True):
        self.browser = browser or BrowserAgent(dry_run=dry_run)
        self.scouting_reports: list[dict] = []

    def scout_niche(self, niche: str) -> dict:
        """Deep-dive research on a niche: hooks, competitors, patterns."""
        posts = self.browser.search_instagram(niche, limit=10)
        hooks = self.browser.extract_trending_hooks(niche, top_n=5)

        hashtags: set[str] = set()
        engagement_total = 0
        for p in posts:
            for h in p.hashtags:
                hashtags.add(h)
            engagement_total += p.likes + p.comments

        report = {
            "niche": niche,
            "posts_analyzed": len(posts),
            "top_hooks": hooks,
            "trending_hashtags": list(hashtags)[:10],
            "avg_engagement": engagement_total // max(len(posts), 1),
            "scouted_at": _now_iso(),
        }
        self.scouting_reports.append(report)
        return report

    def research_content_gap(self, niche: str, own_handle: str = "lucastigrereal") -> dict:
        """Find content gaps: what competitors post that we don't."""
        own_profile = self.browser.scrape_profile(own_handle)
        posts = self.browser.search_instagram(niche, limit=15)

        competitor_hooks = []
        competitor_handles: set[str] = set()
        for p in posts:
            if p.handle.lstrip("@") != own_handle:
                competitor_handles.add(p.handle)
                if p.caption:
                    competitor_hooks.append(p.caption.split("\n")[0][:120])

        return {
            "niche": niche,
            "own_followers": own_profile.followers,
            "competitors_found": len(competitor_handles),
            "competitor_handles": list(competitor_handles)[:10],
            "top_competitor_hooks": competitor_hooks[:5],
            "recommendation": (
                f"Encontrados {len(competitor_handles)} concorrentes no nicho '{niche}'. "
                f"Analise os hooks acima para identificar gaps de conteúdo."
            ),
            "researched_at": _now_iso(),
        }

    @property
    def report_count(self) -> int:
        return len(self.scouting_reports)
