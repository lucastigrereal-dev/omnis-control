"""DesktopAgent — Windows desktop automation via pyautogui + OCR."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.computer_use.sandbox import SecuritySandbox

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str = "") -> str:
    import uuid
    return f"{prefix}{uuid.uuid4().hex[:8]}"


# ── models ───────────────────────────────────────────────────────────────


@dataclass
class DesktopAction:
    action: str  # open | click | type | screenshot | read_screen | press | wait
    target: str = ""       # app name, selector, key combo
    value: str = ""        # text to type, file path
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "target": self.target,
            "value": self.value,
            "timestamp": self.timestamp,
        }


@dataclass
class DesktopResult:
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
            "data": self.data[:500],
            "screenshot_path": self.screenshot_path,
            "error": self.error,
            "timestamp": self.timestamp,
        }


# ── DesktopAgent ─────────────────────────────────────────────────────────


class DesktopAgent:
    """Windows desktop automation — pyautogui + optional OCR.

    Mock-first: if pyautogui not installed, operates in simulated mode.
    Useful for: opening apps, filling forms, reading screen content.
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.sandbox = SecuritySandbox(strict=True)
        self._actions: list[DesktopAction] = []
        self._results: list[DesktopResult] = []
        self._pyautogui = None
        self._mock = False

        try:
            import pyautogui
            pyautogui.FAILSAFE = True
            self._pyautogui = pyautogui
        except ImportError:
            self._mock = True
            logger.info("pyautogui not installed — using mock desktop")

    def _should_validate(self) -> bool:
        return not self.dry_run and not self._mock

    def open_app(self, app_name: str) -> DesktopResult:
        """Open a Windows application by name."""
        if self._should_validate():
            self.sandbox.validate_action(f"open_app:{app_name}")
        self._actions.append(DesktopAction(action="open", target=app_name))

        if self.dry_run:
            result = DesktopResult(
                success=True, action="open",
                data=f"[dry-run] Would open {app_name}",
            )
        elif self._mock:
            result = DesktopResult(
                success=True, action="open",
                data=f"[mock] Simulated opening {app_name}",
            )
        else:
            try:
                import subprocess
                subprocess.Popen(app_name, shell=True)
                result = DesktopResult(success=True, action="open", data=f"Opened {app_name}")
            except Exception as exc:
                result = DesktopResult(success=False, action="open", error=str(exc))

        self._results.append(result)
        return result

    def type_text(self, text: str, interval: float = 0.05) -> DesktopResult:
        """Type text using pyautogui keyboard."""
        if self._should_validate():
            self.sandbox.validate_action("type_text")
        self._actions.append(DesktopAction(action="type", value=text[:100]))

        if self.dry_run:
            result = DesktopResult(
                success=True, action="type",
                data=f"[dry-run] Would type: {text[:80]}",
            )
        elif self._mock:
            result = DesktopResult(
                success=True, action="type",
                data=f"[mock] Simulated typing: {text[:80]}",
            )
        else:
            try:
                self._pyautogui.typewrite(text, interval=interval)
                result = DesktopResult(success=True, action="type", data=f"Typed {len(text)} chars")
            except Exception as exc:
                result = DesktopResult(success=False, action="type", error=str(exc))

        self._results.append(result)
        return result

    def press_keys(self, keys: str) -> DesktopResult:
        """Press key combination (e.g. 'ctrl+v', 'alt+tab', 'enter')."""
        if self._should_validate():
            self.sandbox.validate_action(f"press_keys:{keys}")
        self._actions.append(DesktopAction(action="press", target=keys))

        if self.dry_run:
            result = DesktopResult(
                success=True, action="press",
                data=f"[dry-run] Would press: {keys}",
            )
        elif self._mock:
            result = DesktopResult(
                success=True, action="press",
                data=f"[mock] Simulated press: {keys}",
            )
        else:
            try:
                self._pyautogui.hotkey(*keys.split("+"))
                result = DesktopResult(success=True, action="press", data=f"Pressed {keys}")
            except Exception as exc:
                result = DesktopResult(success=False, action="press", error=str(exc))

        self._results.append(result)
        return result

    def screenshot(self, path: str = "desktop_screenshot.png") -> DesktopResult:
        """Take a screenshot of the current screen."""
        if self._should_validate():
            self.sandbox.validate_path(path)
        self._actions.append(DesktopAction(action="screenshot", value=path))

        if self.dry_run:
            result = DesktopResult(
                success=True, action="screenshot",
                data=f"[dry-run] Would save screenshot to {path}",
            )
        elif self._mock:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(b"mock-screenshot-data")
            result = DesktopResult(
                success=True, action="screenshot",
                screenshot_path=path,
                data=f"[mock] Mock screenshot saved to {path}",
            )
        else:
            try:
                self._pyautogui.screenshot(path)
                result = DesktopResult(
                    success=True, action="screenshot",
                    screenshot_path=path,
                    data=f"Screenshot saved to {path}",
                )
            except Exception as exc:
                result = DesktopResult(success=False, action="screenshot", error=str(exc))

        self._results.append(result)
        return result

    def read_screen(self) -> DesktopResult:
        """Read text from screen using OCR (pytesseract if available, mock otherwise)."""
        self._actions.append(DesktopAction(action="read_screen"))

        try:
            import pytesseract
            from PIL import Image
            _has_ocr = True
        except ImportError:
            _has_ocr = False

        if self.dry_run:
            result = DesktopResult(
                success=True, action="read_screen",
                data="[dry-run] Would read screen via OCR",
            )
        elif self._mock or not _has_ocr:
            result = DesktopResult(
                success=True, action="read_screen",
                data="[mock] Simulated OCR: tela contém texto de exemplo",
            )
        else:
            try:
                screenshot = self._pyautogui.screenshot()
                text = pytesseract.image_to_string(screenshot)
                result = DesktopResult(success=True, action="read_screen", data=text)
            except Exception as exc:
                result = DesktopResult(success=False, action="read_screen", error=str(exc))

        self._results.append(result)
        return result

    def click_at(self, x: int, y: int) -> DesktopResult:
        """Click at screen coordinates."""
        if self._should_validate():
            self.sandbox.validate_action(f"click_at:{x},{y}")
        self._actions.append(DesktopAction(action="click", target=f"{x},{y}"))

        if self.dry_run:
            result = DesktopResult(
                success=True, action="click",
                data=f"[dry-run] Would click at ({x}, {y})",
            )
        elif self._mock:
            result = DesktopResult(
                success=True, action="click",
                data=f"[mock] Simulated click at ({x}, {y})",
            )
        else:
            try:
                self._pyautogui.click(x, y)
                result = DesktopResult(success=True, action="click", data=f"Clicked ({x}, {y})")
            except Exception as exc:
                result = DesktopResult(success=False, action="click", error=str(exc))

        self._results.append(result)
        return result

    def wait(self, seconds: float) -> DesktopResult:
        """Wait for specified seconds."""
        self._actions.append(DesktopAction(action="wait", value=str(seconds)))

        if self.dry_run:
            result = DesktopResult(
                success=True, action="wait",
                data=f"[dry-run] Would wait {seconds}s",
            )
        else:
            time.sleep(seconds)
            result = DesktopResult(success=True, action="wait", data=f"Waited {seconds}s")

        self._results.append(result)
        return result

    def open_notepad_and_type(self, text: str) -> list[DesktopResult]:
        """Convenience: open Notepad, type text (classic automation test)."""
        results = [
            self.open_app("notepad.exe"),
            self.wait(0.5),
            self.type_text(text),
        ]
        return results

    # ── introspection ─────────────────────────────────────────────────────

    @property
    def action_log(self) -> list[DesktopAction]:
        return list(self._actions)

    @property
    def result_log(self) -> list[DesktopResult]:
        return list(self._results)

    @property
    def is_mock(self) -> bool:
        return self._mock

    @property
    def all_succeeded(self) -> bool:
        return all(r.success for r in self._results) if self._results else True
