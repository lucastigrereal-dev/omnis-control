"""BrowserExecutor — automação de browser para pesquisa web e formulários.

Mock-first: se Playwright não estiver instalado, opera em modo simulado.
"""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── models ─────────────────────────────────────────────────────────────


@dataclass
class BrowserAction:
    action: str  # open | fill | click | screenshot | get_text | close
    selector: str = ""
    value: str = ""
    url: str = ""
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "selector": self.selector,
            "value": self.value,
            "url": self.url,
            "timestamp": self.timestamp,
        }


@dataclass
class BrowserResult:
    success: bool
    action: str
    data: str = ""
    screenshot_path: str = ""
    error: str = ""
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "action": self.action,
            "data": self.data,
            "screenshot_path": self.screenshot_path,
            "error": self.error,
            "timestamp": self.timestamp,
        }


# ── mock adapter ───────────────────────────────────────────────────────


class MockBrowser:
    """Browser simulado quando Playwright não está disponível."""

    def __init__(self) -> None:
        self._pages: list[str] = []
        self._forms: dict[str, str] = {}
        self._closed = False

    def new_page(self) -> "MockPage":
        return MockPage(self)

    def close(self) -> None:
        self._closed = True


class MockPage:
    """Página simulada."""

    def __init__(self, browser: MockBrowser) -> None:
        self._browser = browser
        self.url = ""
        self._content = ""

    def goto(self, url: str) -> None:
        self.url = url
        self._browser._pages.append(url)
        self._content = f"<html><body>Mock content for {url}</body></html>"
        logger.info("[mock] goto %s", url)

    def fill(self, selector: str, value: str) -> None:
        self._browser._forms[selector] = value
        logger.info("[mock] fill %s = %s", selector, value)

    def click(self, selector: str) -> None:
        logger.info("[mock] click %s", selector)

    def screenshot(self, path: str) -> None:
        Path(path).write_bytes(b"mock-screenshot-png-data")
        logger.info("[mock] screenshot saved to %s", path)

    def inner_text(self, selector: str) -> str:
        return f"Mock text for {selector}"

    def content(self) -> str:
        return self._content

    def close(self) -> None:
        pass


# ── executor ───────────────────────────────────────────────────────────


class BrowserExecutor:
    """Executa ações de browser com Playwright (se disponível) ou mock."""

    def __init__(self, dry_run: bool = True, headless: bool = True) -> None:
        self.dry_run = dry_run
        self.headless = headless
        self._actions: list[BrowserAction] = []
        self._results: list[BrowserResult] = []
        self._page: Optional[object] = None
        self._browser: Optional[object] = None
        self._mock = False

        # Try to import playwright
        try:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright
            self._pw_available = True
        except ImportError:
            self._playwright = None
            self._pw_available = False
            self._mock = True
            logger.warning("Playwright not installed — using mock browser")

    def open_page(self, url: str) -> BrowserResult:
        """Abre uma URL no browser."""
        self._actions.append(BrowserAction(action="open", url=url))

        if self.dry_run:
            return BrowserResult(success=True, action="open", data=f"[dry-run] Would open {url}")

        try:
            if self._pw_available and not self._mock:
                pw = self._playwright().start()
                self._browser = pw.chromium.launch(headless=self.headless)
                self._page = self._browser.new_page()
                self._page.goto(url)
                title = self._page.title()
            else:
                self._browser = MockBrowser()
                self._page = self._browser.new_page()
                self._page.goto(url)
                title = f"Mock: {url}"

            result = BrowserResult(success=True, action="open", data=title)
        except Exception as exc:
            result = BrowserResult(success=False, action="open", error=str(exc))

        self._results.append(result)
        return result

    def fill_form(self, selector: str, value: str) -> BrowserResult:
        """Preenche um campo de formulário."""
        self._actions.append(BrowserAction(action="fill", selector=selector, value=value))

        if self.dry_run:
            return BrowserResult(
                success=True,
                action="fill",
                data=f"[dry-run] Would fill {selector} with {value}",
            )

        try:
            if self._page:
                self._page.fill(selector, value)
            result = BrowserResult(success=True, action="fill")
        except Exception as exc:
            result = BrowserResult(success=False, action="fill", error=str(exc))

        self._results.append(result)
        return result

    def click(self, selector: str) -> BrowserResult:
        """Clica em um elemento."""
        self._actions.append(BrowserAction(action="click", selector=selector))

        if self.dry_run:
            return BrowserResult(
                success=True,
                action="click",
                data=f"[dry-run] Would click {selector}",
            )

        try:
            if self._page:
                self._page.click(selector)
            result = BrowserResult(success=True, action="click")
        except Exception as exc:
            result = BrowserResult(success=False, action="click", error=str(exc))

        self._results.append(result)
        return result

    def screenshot(self, path: str) -> BrowserResult:
        """Tira screenshot da página atual."""
        self._actions.append(BrowserAction(action="screenshot"))

        if self.dry_run:
            return BrowserResult(
                success=True,
                action="screenshot",
                data=f"[dry-run] Would save screenshot to {path}",
            )

        try:
            if self._page:
                self._page.screenshot(path=path)
            result = BrowserResult(success=True, action="screenshot", screenshot_path=path)
        except Exception as exc:
            result = BrowserResult(success=False, action="screenshot", error=str(exc))

        self._results.append(result)
        return result

    def get_text(self, selector: str) -> BrowserResult:
        """Extrai texto de um elemento."""
        self._actions.append(BrowserAction(action="get_text", selector=selector))

        if self.dry_run:
            return BrowserResult(
                success=True,
                action="get_text",
                data=f"[dry-run] Would get text from {selector}",
            )

        try:
            text = ""
            if self._page:
                text = self._page.inner_text(selector)
            result = BrowserResult(success=True, action="get_text", data=text)
        except Exception as exc:
            result = BrowserResult(success=False, action="get_text", error=str(exc))

        self._results.append(result)
        return result

    def close(self) -> BrowserResult:
        """Fecha o browser."""
        self._actions.append(BrowserAction(action="close"))

        if self.dry_run:
            return BrowserResult(success=True, action="close", data="[dry-run] Would close browser")

        try:
            if self._page:
                self._page.close()
            if self._browser:
                self._browser.close()
            result = BrowserResult(success=True, action="close")
        except Exception as exc:
            result = BrowserResult(success=False, action="close", error=str(exc))

        self._results.append(result)
        return result

    # ── batch / workflow helpers ──────────────────────────────────────────

    def run_sequence(self, steps: list[dict]) -> list[BrowserResult]:
        """Executa uma sequência de ações: [{'action': 'open', 'url': '...'}, ...]."""
        results: list[BrowserResult] = []
        for step in steps:
            action = step.get("action", "")
            if action == "open":
                results.append(self.open_page(step.get("url", "")))
            elif action == "fill":
                results.append(self.fill_form(step.get("selector", ""), step.get("value", "")))
            elif action == "click":
                results.append(self.click(step.get("selector", "")))
            elif action == "screenshot":
                results.append(self.screenshot(step.get("path", "screenshot.png")))
            elif action == "get_text":
                results.append(self.get_text(step.get("selector", "")))
            elif action == "close":
                results.append(self.close())
        return results

    # ── introspection ─────────────────────────────────────────────────────

    @property
    def action_log(self) -> list[BrowserAction]:
        return list(self._actions)

    @property
    def result_log(self) -> list[BrowserResult]:
        return list(self._results)

    @property
    def is_mock(self) -> bool:
        return self._mock

    @property
    def all_succeeded(self) -> bool:
        return all(r.success for r in self._results)
