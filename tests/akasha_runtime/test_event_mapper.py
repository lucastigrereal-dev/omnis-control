from src.akasha_runtime.models import AkashaEventMapping
from src.akasha_runtime.event_mapper import AkashaEventMapper


class TestAkashaEventMapper:
    def test_map_known_event(self):
        mapper = AkashaEventMapper()
        mapper.register(AkashaEventMapping(
            event_type="EXECUTION_COMPLETED", target_collection="execution_logs", priority=5,
        ))
        collection, mapping = mapper.map_event("EXECUTION_COMPLETED")
        assert collection == "execution_logs"
        assert mapping is not None
        assert mapping.priority == 5

    def test_map_unknown_event(self):
        mapper = AkashaEventMapper()
        collection, mapping = mapper.map_event("UNKNOWN_TYPE")
        assert collection is None
        assert mapping is None

    def test_register_batch(self):
        mapper = AkashaEventMapper()
        mappings = [
            AkashaEventMapping(event_type="REQUEST_RECEIVED", target_collection="audit"),
            AkashaEventMapping(event_type="EXECUTION_BLOCKED", target_collection="security"),
        ]
        mapper.register_batch(mappings)
        assert mapper.mapping_count == 2
        c1, _ = mapper.map_event("REQUEST_RECEIVED")
        c2, _ = mapper.map_event("EXECUTION_BLOCKED")
        assert c1 == "audit"
        assert c2 == "security"

    def test_map_batch_mixed(self):
        mapper = AkashaEventMapper()
        mapper.register(AkashaEventMapping(
            event_type="REQUEST_RECEIVED", target_collection="audit",
        ))
        events = [
            {"event_type": "REQUEST_RECEIVED"},
            {"event_type": "UNKNOWN"},
        ]
        results = mapper.map_batch(events)
        assert results[0]["mapped"] is True
        assert results[1]["mapped"] is False
        assert results[1]["target_collection"] is None

    def test_mapped_count_increments(self):
        mapper = AkashaEventMapper()
        mapper.register(AkashaEventMapping(
            event_type="REQUEST_RECEIVED", target_collection="audit",
        ))
        mapper.map_event("REQUEST_RECEIVED")
        mapper.map_event("REQUEST_RECEIVED")
        mapper.map_event("UNKNOWN")
        assert mapper.mapped_count == 2

    def test_get_mapping(self):
        mapper = AkashaEventMapper()
        m = AkashaEventMapping(event_type="EXECUTION_COMPLETED", target_collection="logs")
        mapper.register(m)
        assert mapper.get_mapping("EXECUTION_COMPLETED") is m
        assert mapper.get_mapping("NONEXISTENT") is None

    def test_unregister(self):
        mapper = AkashaEventMapper()
        mapper.register(AkashaEventMapping(event_type="REQUEST_RECEIVED", target_collection="audit"))
        assert mapper.mapping_count == 1
        assert mapper.unregister("REQUEST_RECEIVED") is True
        assert mapper.mapping_count == 0
        assert mapper.unregister("NONEXISTENT") is False

    def test_approval_flag_from_mapping(self):
        mapper = AkashaEventMapper()
        mapper.register(AkashaEventMapping(
            event_type="EXECUTION_COMPLETED", target_collection="logs",
            require_approval=True, transform_hint="sanitize",
        ))
        _, mapping = mapper.map_event("EXECUTION_COMPLETED")
        assert mapping.require_approval is True
        assert mapping.transform_hint == "sanitize"
