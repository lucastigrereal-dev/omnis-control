from src.remote_control.models import RemoteCommand, CommandSource, CommandRisk
from src.remote_control.security import RemoteSecurityModel, TrustedSource


class TestTrustedSource:
    def test_matches_exact(self):
        ts = TrustedSource(source_type="TELEGRAM", identifier="user123", max_command_risk="LOW")
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="user123", risk=CommandRisk.LOW)
        assert ts.matches(cmd) is True

    def test_not_matches_different_user(self):
        ts = TrustedSource(source_type="TELEGRAM", identifier="user123")
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="user456")
        assert ts.matches(cmd) is False

    def test_not_matches_different_source(self):
        ts = TrustedSource(source_type="TELEGRAM", identifier="user123")
        cmd = RemoteCommand(source=CommandSource.WHATSAPP, source_user_id="user123")
        assert ts.matches(cmd) is False

    def test_not_matches_disabled(self):
        ts = TrustedSource(source_type="TELEGRAM", identifier="user123", enabled=False)
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="user123")
        assert ts.matches(cmd) is False

    def test_wildcard_identifier(self):
        ts = TrustedSource(source_type="TELEGRAM", identifier="")
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="anyone")
        assert ts.matches(cmd) is True


class TestRemoteSecurityModel:
    def test_local_cli_always_allowed(self):
        sm = RemoteSecurityModel()
        cmd = RemoteCommand(source=CommandSource.CLI, command="deploy", risk=CommandRisk.CRITICAL)
        ok, _ = sm.validate_remote(cmd)
        assert ok is True

    def test_remote_untrusted_blocked(self):
        sm = RemoteSecurityModel()
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="unknown")
        ok, msg = sm.validate_remote(cmd)
        assert ok is False
        assert "not trusted" in msg

    def test_remote_trusted_allowed(self):
        sm = RemoteSecurityModel()
        sm.add_trusted(TrustedSource(source_type="TELEGRAM", identifier="user123", max_command_risk="LOW"))
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="user123", risk=CommandRisk.LOW)
        ok, _ = sm.validate_remote(cmd)
        assert ok is True

    def test_remote_risk_exceeds_trust(self):
        sm = RemoteSecurityModel()
        sm.add_trusted(TrustedSource(source_type="TELEGRAM", identifier="user123", max_command_risk="LOW"))
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="user123", risk=CommandRisk.HIGH)
        ok, msg = sm.validate_remote(cmd)
        assert ok is False
        assert "exceeds trust" in msg

    def test_blocked_user(self):
        sm = RemoteSecurityModel()
        sm.add_trusted(TrustedSource(source_type="TELEGRAM", identifier="user123", max_command_risk="LOW"))
        sm.block_user("user123")
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="user123", risk=CommandRisk.LOW)
        ok, msg = sm.validate_remote(cmd)
        assert ok is False
        assert "blocked" in msg

    def test_unblock_user(self):
        sm = RemoteSecurityModel()
        sm.block_user("user123")
        assert sm.blocked_count == 1
        assert sm.unblock_user("user123") is True
        assert sm.blocked_count == 0
        assert sm.unblock_user("nonexistent") is False

    def test_requires_challenge_no_token(self):
        sm = RemoteSecurityModel()
        sm.add_trusted(TrustedSource(
            source_type="TELEGRAM", identifier="user123",
            max_command_risk="HIGH", requires_challenge=True,
        ))
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, source_user_id="user123", risk=CommandRisk.HIGH)
        ok, msg = sm.validate_remote(cmd)
        assert ok is False
        assert "challenge required" in msg

    def test_is_blocked(self):
        sm = RemoteSecurityModel()
        sm.block_user("bad_actor")
        cmd = RemoteCommand(source_user_id="bad_actor")
        assert sm.is_blocked(cmd) is True
        assert sm.is_blocked(RemoteCommand(source_user_id="good_user")) is False
