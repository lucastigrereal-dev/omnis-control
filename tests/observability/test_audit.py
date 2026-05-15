from src.observability.audit import AuditTrail, AuditEntryType


class TestAuditTrail:
    def test_record_entry(self):
        trail = AuditTrail()
        entry = trail.record(
            action="write_report",
            result="SUCCESS",
            source="war_room_bridge",
        )
        assert entry.action == "write_report"
        assert entry.result == "SUCCESS"
        assert trail.entry_count == 1

    def test_query_by_source(self):
        trail = AuditTrail()
        trail.record("a1", "ok", source="s1")
        trail.record("a2", "ok", source="s2")
        trail.record("a3", "ok", source="s1")

        results = trail.query(source="s1")
        assert len(results) == 2

    def test_query_by_type(self):
        trail = AuditTrail()
        trail.record("a", "ok", entry_type=AuditEntryType.DECISION)
        trail.record("b", "ok", entry_type=AuditEntryType.ERROR)
        trail.record("c", "ok", entry_type=AuditEntryType.DECISION)

        results = trail.query(entry_type="DECISION")
        assert len(results) == 2

    def test_last_entry(self):
        trail = AuditTrail()
        assert trail.last_entry is None
        trail.record("first", "ok")
        trail.record("last", "ok")
        assert trail.last_entry.action == "last"

    def test_entry_with_detail(self):
        trail = AuditTrail()
        entry = trail.record("action", "result", detail={"key": "val"})
        assert entry.detail == {"key": "val"}
