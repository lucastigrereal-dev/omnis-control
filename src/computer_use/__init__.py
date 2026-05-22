"""Computer Use — browser + desktop automation for OMNIS Wave 4."""

from src.computer_use.browser_agent import BrowserAgent, InstagramScout, InstagramPost, ProfileData
from src.computer_use.desktop_agent import DesktopAgent, DesktopAction, DesktopResult
from src.computer_use.sandbox import SecuritySandbox, SandboxViolation

__all__ = [
    "BrowserAgent",
    "InstagramScout",
    "InstagramPost",
    "ProfileData",
    "DesktopAgent",
    "DesktopAction",
    "DesktopResult",
    "SecuritySandbox",
    "SandboxViolation",
]
