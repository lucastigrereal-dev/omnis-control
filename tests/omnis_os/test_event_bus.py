"""Tests for P29 EventBus."""
from src.omnis_os.event_bus import EventBus
from src.omnis_os.models import OmnisEvent


class TestEventBusSubscribe:
    def test_subscribe(self):
        bus = EventBus(dry_run=True)
        def handler(e): pass
        bus.subscribe("module_activated", handler)
        assert bus.subscriber_count("module_activated") == 1

    def test_subscribe_multiple(self):
        bus = EventBus(dry_run=True)
        bus.subscribe("x", lambda e: None)
        bus.subscribe("x", lambda e: None)
        assert bus.subscriber_count("x") == 2

    def test_unsubscribe(self):
        bus = EventBus(dry_run=True)
        def h(e): pass
        bus.subscribe("y", h)
        bus.unsubscribe("y", h)
        assert bus.subscriber_count("y") == 0

    def test_unsubscribe_missing_noop(self):
        bus = EventBus(dry_run=True)
        bus.unsubscribe("nope", lambda e: None)  # no crash

    def test_unsubscribe_all(self):
        bus = EventBus(dry_run=True)
        bus.subscribe("a", lambda e: None)
        bus.subscribe("b", lambda e: None)
        bus.unsubscribe_all()
        assert bus.total_subscribers == 0


class TestEventBusEmit:
    def test_emit_stores_in_history(self):
        bus = EventBus(dry_run=True)
        e = OmnisEvent.new("test_type", "test_module")
        bus.emit(e)
        assert bus.history_size == 1

    def test_emit_new(self):
        bus = EventBus(dry_run=True)
        e = bus.emit_new("boot", "kernel", data={"v": 1})
        assert e.event_type == "boot"
        assert e.source_module == "kernel"
        assert bus.history_size == 1

    def test_emit_triggers_handler_in_non_dry(self):
        bus = EventBus(dry_run=False)
        called = []
        bus.subscribe("ping", lambda e: called.append(e))
        bus.emit(OmnisEvent.new("ping", "src"))
        assert len(called) == 1

    def test_dry_run_suppresses_handlers(self):
        bus = EventBus(dry_run=True)
        called = []
        bus.subscribe("ping", lambda e: called.append(1))
        bus.emit(OmnisEvent.new("ping", "src"))
        assert called == []

    def test_handler_exception_does_not_crash(self):
        bus = EventBus(dry_run=False)
        def boom(e): raise RuntimeError("oh no")
        bus.subscribe("x", boom)
        bus.emit(OmnisEvent.new("x", "src"))  # no crash, swallowed

    def test_handler_exception_does_not_block_others(self):
        bus = EventBus(dry_run=False)
        called = []
        def boom(e): raise RuntimeError("err")
        def ok(e): called.append(1)
        bus.subscribe("z", boom)
        bus.subscribe("z", ok)
        bus.emit(OmnisEvent.new("z", "src"))
        assert len(called) == 1


class TestEventBusHistory:
    def test_history_filtered(self):
        bus = EventBus(dry_run=True)
        bus.emit(OmnisEvent.new("a", "x"))
        bus.emit(OmnisEvent.new("b", "x"))
        assert len(bus.history(event_type="a")) == 1
        assert len(bus.history(event_type="b")) == 1

    def test_history_limit(self):
        bus = EventBus(dry_run=True)
        for _ in range(5):
            bus.emit(OmnisEvent.new("x", "s"))
        assert len(bus.history(limit=3)) == 3

    def test_history_all(self):
        bus = EventBus(dry_run=True)
        bus.emit(OmnisEvent.new("a", "s"))
        bus.emit(OmnisEvent.new("b", "s"))
        assert len(bus.history()) == 2

    def test_history_limit_enforced(self):
        bus = EventBus(dry_run=True)
        bus._history_limit = 3
        for i in range(5):
            bus.emit(OmnisEvent.new("x", "s", data={"i": i}))
        assert bus.history_size == 3


class TestEventBusInfo:
    def test_event_types(self):
        bus = EventBus(dry_run=True)
        bus.subscribe("boot", lambda e: None)
        bus.subscribe("shutdown", lambda e: None)
        assert set(bus.event_types) == {"boot", "shutdown"}

    def test_total_subscribers(self):
        bus = EventBus(dry_run=True)
        bus.subscribe("a", lambda e: None)
        bus.subscribe("a", lambda e: None)
        bus.subscribe("b", lambda e: None)
        assert bus.total_subscribers == 3
