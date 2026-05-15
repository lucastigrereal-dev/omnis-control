from src.remote_control.models import RemoteCommand, CommandSource, CommandRisk
from src.remote_control.event_log import RemoteEventLog, RemoteEventType, RemoteEvent


class TestRemoteEvent:
    def test_defaults(self):
        e = RemoteEvent()
        assert e.event_id.startswith("re_")
        assert e.event_type == RemoteEventType.COMMAND_RECEIVED

    def test_to_dict(self):
        e = RemoteEvent(
            event_type=RemoteEventType.EXECUTED,
            command_id="rc_abc", source="TELEGRAM", detail={"ok": True},
        )
        d = e.to_dict()
        assert d["event_type"] == "EXECUTED"
        assert d["detail"]["ok"] is True


class TestRemoteEventLog:
    def test_record_event(self):
        log = RemoteEventLog()
        cmd = RemoteCommand(source=CommandSource.TELEGRAM, command="status")
        log.record(RemoteEventType.COMMAND_RECEIVED, cmd)
        assert log.event_count == 1

    def test_query_by_command_id(self):
        log = RemoteEventLog()
        cmd1 = RemoteCommand(command="a")
        cmd2 = RemoteCommand(command="b")
        log.record(RemoteEventType.COMMAND_RECEIVED, cmd1)
        log.record(RemoteEventType.EXECUTED, cmd2)
        assert len(log.query(command_id=cmd1.command_id)) == 1

    def test_query_by_event_type(self):
        log = RemoteEventLog()
        cmd = RemoteCommand()
        log.record(RemoteEventType.COMMAND_RECEIVED, cmd)
        log.record(RemoteEventType.BLOCKED, cmd)
        assert len(log.query(event_type="BLOCKED")) == 1

    def test_query_by_source(self):
        log = RemoteEventLog()
        tg = RemoteCommand(source=CommandSource.TELEGRAM)
        wa = RemoteCommand(source=CommandSource.WHATSAPP)
        log.record(RemoteEventType.COMMAND_RECEIVED, tg)
        log.record(RemoteEventType.COMMAND_RECEIVED, wa)
        assert len(log.query(source="TELEGRAM")) == 1

    def test_command_timeline(self):
        log = RemoteEventLog()
        cmd = RemoteCommand()
        log.record(RemoteEventType.COMMAND_RECEIVED, cmd)
        log.record(RemoteEventType.SECURITY_CHECKED, cmd, {"passed": True})
        log.record(RemoteEventType.EXECUTED, cmd)
        timeline = log.command_timeline(cmd.command_id)
        assert len(timeline) == 3
        assert timeline[1]["detail"]["passed"] is True

    def test_last_event(self):
        log = RemoteEventLog()
        log.record(RemoteEventType.COMMAND_RECEIVED, RemoteCommand())
        log.record(RemoteEventType.EXECUTED, RemoteCommand())
        assert log.last_event is not None
        assert log.last_event.event_type == RemoteEventType.EXECUTED

    def test_last_event_empty(self):
        log = RemoteEventLog()
        assert log.last_event is None
