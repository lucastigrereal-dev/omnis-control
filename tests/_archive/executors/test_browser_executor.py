"""Tests for BrowserExecutor — mock-first, no Playwright required."""
from __future__ import annotations

import pytest
from pathlib import Path

from src.executors.browser_executor import (
    BrowserExecutor,
    BrowserAction,
    BrowserResult,
    MockBrowser,
    MockPage,
)


class TestMockBrowser:
    def test_mock_browser_creates_page(self):
        browser = MockBrowser()
        page = browser.new_page()
        assert isinstance(page, MockPage)
        assert not browser._closed

    def test_mock_page_goto(self):
        browser = MockBrowser()
        page = browser.new_page()
        page.goto("https://example.com")
        assert page.url == "https://example.com"
        assert "https://example.com" in browser._pages

    def test_mock_page_fill(self):
        browser = MockBrowser()
        page = browser.new_page()
        page.fill("#email", "test@example.com")
        assert browser._forms["#email"] == "test@example.com"

    def test_mock_page_click(self):
        browser = MockBrowser()
        page = browser.new_page()
        page.click("#submit")  # no error

    def test_mock_page_screenshot(self, tmp_path: Path):
        browser = MockBrowser()
        page = browser.new_page()
        path = tmp_path / "shot.png"
        page.screenshot(str(path))
        assert path.exists()
        assert path.read_bytes() == b"mock-screenshot-png-data"

    def test_mock_page_inner_text(self):
        browser = MockBrowser()
        page = browser.new_page()
        text = page.inner_text("h1")
        assert "Mock text" in text

    def test_mock_browser_close(self):
        browser = MockBrowser()
        browser.close()
        assert browser._closed


class TestBrowserExecutorDryRun:
    def test_dry_run_open_page(self):
        exe = BrowserExecutor(dry_run=True)
        result = exe.open_page("https://example.com")
        assert result.success is True
        assert "dry-run" in result.data
        assert "example.com" in result.data
        assert len(exe.action_log) == 1
        assert exe.action_log[0].action == "open"

    def test_dry_run_fill_form(self):
        exe = BrowserExecutor(dry_run=True)
        result = exe.fill_form("#email", "test@example.com")
        assert result.success is True
        assert "dry-run" in result.data
        assert "#email" in result.data

    def test_dry_run_click(self):
        exe = BrowserExecutor(dry_run=True)
        result = exe.click("#submit")
        assert result.success is True
        assert "dry-run" in result.data

    def test_dry_run_screenshot(self):
        exe = BrowserExecutor(dry_run=True)
        result = exe.screenshot("/tmp/shot.png")
        assert result.success is True
        assert "dry-run" in result.data

    def test_dry_run_get_text(self):
        exe = BrowserExecutor(dry_run=True)
        result = exe.get_text("h1")
        assert result.success is True
        assert "dry-run" in result.data

    def test_dry_run_close(self):
        exe = BrowserExecutor(dry_run=True)
        result = exe.close()
        assert result.success is True
        assert "dry-run" in result.data

    def test_all_succeeded_true_in_dry_run(self):
        exe = BrowserExecutor(dry_run=True)
        exe.open_page("https://example.com")
        exe.fill_form("#email", "x")
        exe.close()
        assert exe.all_succeeded is True


class TestBrowserExecutorMockMode:
    def test_mock_mode_when_playwright_missing(self):
        exe = BrowserExecutor(dry_run=False)
        # If playwright is installed, this test may need adjustment
        # but in CI/test env without playwright it runs mock
        if not exe._pw_available:
            assert exe.is_mock is True

    def test_mock_open_page(self):
        exe = BrowserExecutor(dry_run=False)
        if not exe._pw_available:
            result = exe.open_page("https://example.com")
            assert result.success is True
            assert "Mock:" in result.data

    def test_mock_fill_form(self):
        exe = BrowserExecutor(dry_run=False)
        if not exe._pw_available:
            exe.open_page("https://example.com")
            result = exe.fill_form("#name", "Lucas")
            assert result.success is True

    def test_mock_screenshot(self, tmp_path: Path):
        exe = BrowserExecutor(dry_run=False)
        if not exe._pw_available:
            exe.open_page("https://example.com")
            path = tmp_path / "shot.png"
            result = exe.screenshot(str(path))
            assert result.success is True
            assert result.screenshot_path == str(path)

    def test_mock_get_text(self):
        exe = BrowserExecutor(dry_run=False)
        if not exe._pw_available:
            exe.open_page("https://example.com")
            result = exe.get_text("h1")
            assert result.success is True
            assert "Mock text" in result.data

    def test_mock_close(self):
        exe = BrowserExecutor(dry_run=False)
        if not exe._pw_available:
            result = exe.close()
            assert result.success is True


class TestBrowserExecutorSequence:
    def test_run_sequence_dry_run(self):
        exe = BrowserExecutor(dry_run=True)
        steps = [
            {"action": "open", "url": "https://example.com"},
            {"action": "fill", "selector": "#email", "value": "test@test.com"},
            {"action": "click", "selector": "#submit"},
            {"action": "close"},
        ]
        results = exe.run_sequence(steps)
        assert len(results) == 4
        assert all(r.success for r in results)
        assert len(exe.action_log) == 4

    def test_run_sequence_unknown_action_ignored(self):
        exe = BrowserExecutor(dry_run=True)
        steps = [{"action": "unknown"}]
        results = exe.run_sequence(steps)
        assert len(results) == 0


class TestBrowserResult:
    def test_to_dict(self):
        r = BrowserResult(success=True, action="open", data="Google")
        d = r.to_dict()
        assert d["success"] is True
        assert d["action"] == "open"
        assert d["data"] == "Google"


class TestBrowserAction:
    def test_to_dict(self):
        a = BrowserAction(action="open", url="https://example.com")
        d = a.to_dict()
        assert d["action"] == "open"
        assert d["url"] == "https://example.com"
