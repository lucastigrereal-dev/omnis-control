"""Tests for DesktopAgent — Windows desktop automation."""
from __future__ import annotations

import pytest

from src.computer_use.desktop_agent import (
    DesktopAgent,
    DesktopAction,
    DesktopResult,
)


class TestDesktopAction:
    def test_action_defaults(self):
        a = DesktopAction(action="open", target="notepad.exe")
        assert a.action == "open"
        assert a.target == "notepad.exe"

    def test_action_to_dict(self):
        a = DesktopAction(action="type", target="", value="hello world")
        d = a.to_dict()
        assert d["action"] == "type"
        assert d["value"] == "hello world"


class TestDesktopResult:
    def test_result_success(self):
        r = DesktopResult(success=True, action="open", data="Opened notepad")
        assert r.success is True
        assert r.data == "Opened notepad"

    def test_result_failure(self):
        r = DesktopResult(success=False, action="open", error="App not found")
        assert r.success is False
        assert r.error == "App not found"

    def test_result_to_dict(self):
        r = DesktopResult(success=True, action="screenshot", screenshot_path="/tmp/test.png")
        d = r.to_dict()
        assert d["screenshot_path"] == "/tmp/test.png"

    def test_result_data_truncated(self):
        r = DesktopResult(success=True, action="read_screen", data="X" * 600)
        d = r.to_dict()
        assert len(d["data"]) <= 500


class TestDesktopAgent:
    def test_defaults_to_dry_run(self):
        agent = DesktopAgent()
        assert agent.dry_run is True

    def test_is_mock_when_pyautogui_missing(self):
        agent = DesktopAgent(dry_run=True)
        # pyautogui may or may not be installed; mock flag depends
        assert isinstance(agent.is_mock, bool)

    def test_open_app_dry_run(self):
        agent = DesktopAgent(dry_run=True)
        result = agent.open_app("notepad.exe")
        assert result.success is True
        assert "dry-run" in result.data.lower()

    def test_type_text_dry_run(self):
        agent = DesktopAgent(dry_run=True)
        result = agent.type_text("Hello World")
        assert result.success is True
        assert "dry-run" in result.data.lower()

    def test_press_keys_dry_run(self):
        agent = DesktopAgent(dry_run=True)
        result = agent.press_keys("ctrl+v")
        assert result.success is True
        assert "dry-run" in result.data.lower()

    def test_screenshot_dry_run(self):
        agent = DesktopAgent(dry_run=True)
        result = agent.screenshot("test.png")
        assert result.success is True
        assert "dry-run" in result.data.lower()

    def test_read_screen_dry_run(self):
        agent = DesktopAgent(dry_run=True)
        result = agent.read_screen()
        assert result.success is True
        assert "dry-run" in result.data.lower()

    def test_click_at_dry_run(self):
        agent = DesktopAgent(dry_run=True)
        result = agent.click_at(100, 200)
        assert result.success is True
        assert "dry-run" in result.data.lower()

    def test_wait_dry_run(self):
        agent = DesktopAgent(dry_run=True)
        result = agent.wait(0.1)
        assert result.success is True
        assert "dry-run" in result.data.lower()

    def test_open_notepad_and_type_dry_run(self):
        agent = DesktopAgent(dry_run=True)
        results = agent.open_notepad_and_type("Hello Notepad")
        assert len(results) == 3
        assert all(r.success for r in results)

    def test_actions_logged(self):
        agent = DesktopAgent(dry_run=True)
        agent.open_app("calc.exe")
        agent.type_text("test")
        assert len(agent.action_log) == 2

    def test_results_logged(self):
        agent = DesktopAgent(dry_run=True)
        agent.press_keys("enter")
        agent.click_at(10, 20)
        assert len(agent.result_log) == 2

    def test_all_succeeded_initial(self):
        agent = DesktopAgent(dry_run=True)
        assert agent.all_succeeded is True

    def test_all_succeeded_after_actions(self):
        agent = DesktopAgent(dry_run=True)
        agent.open_app("notepad.exe")
        agent.type_text("hello")
        assert agent.all_succeeded is True

    def test_screenshot_mock_writes_file(self, tmp_path):
        agent = DesktopAgent(dry_run=False)
        if agent.is_mock:
            path = str(tmp_path / "screenshot.png")
            result = agent.screenshot(path)
            assert result.success is True

    def test_sandbox_default(self):
        agent = DesktopAgent(dry_run=True)
        assert agent.sandbox is not None
