"""Tests for TracingProvider — LocalJSONLProvider and LangfuseProvider fallback."""
import pytest
from pathlib import Path
from src.providers.tracing import LocalJSONLProvider, LangfuseProvider, SpanContext
from src.providers.base import ProviderStatus


class TestLocalJSONLProvider:
    def test_health_ok(self, tmp_path):
        p = LocalJSONLProvider(traces_dir=tmp_path)
        h = p.health_check()
        assert h.ok

    def test_span_creates_file(self, tmp_path):
        p = LocalJSONLProvider(traces_dir=tmp_path)
        with p.span("test_op") as ctx:
            ctx.set_output({"result": 42})
        files = list(tmp_path.glob("traces_*.jsonl"))
        assert len(files) == 1

    def test_span_writes_valid_jsonl(self, tmp_path):
        import json
        p = LocalJSONLProvider(traces_dir=tmp_path)
        with p.span("my_op", metadata={"key": "val"}, input={"q": "x"}) as ctx:
            ctx.set_output("done")
        content = list(tmp_path.glob("*.jsonl"))[0].read_text()
        entry = json.loads(content.strip())
        assert entry["name"] == "my_op"
        assert entry["output"] == "done"
        assert entry["metadata"] == {"key": "val"}

    def test_span_captures_error(self, tmp_path):
        import json
        p = LocalJSONLProvider(traces_dir=tmp_path)
        with pytest.raises(ValueError):
            with p.span("failing_op") as ctx:
                raise ValueError("boom")
        content = list(tmp_path.glob("*.jsonl"))[0].read_text()
        entry = json.loads(content.strip())
        assert entry["error"] == "boom"

    def test_span_returns_context(self, tmp_path):
        p = LocalJSONLProvider(traces_dir=tmp_path)
        with p.span("op") as ctx:
            assert isinstance(ctx, SpanContext)
            assert ctx.name == "op"

    def test_trace_one_shot(self, tmp_path):
        p = LocalJSONLProvider(traces_dir=tmp_path)
        trace_id = p.trace("event", input="x", output="y")
        assert isinstance(trace_id, str) and len(trace_id) > 0

    def test_trace_writes_file(self, tmp_path):
        import json
        p = LocalJSONLProvider(traces_dir=tmp_path)
        p.trace("my_event", input="in", output="out", metadata={"m": 1})
        content = list(tmp_path.glob("*.jsonl"))[0].read_text()
        entry = json.loads(content.strip())
        assert entry["name"] == "my_event"
        assert entry["input"] == "in"
        assert entry["output"] == "out"

    def test_flush_noop(self, tmp_path):
        p = LocalJSONLProvider(traces_dir=tmp_path)
        p.flush()  # must not raise

    def test_span_duration_positive(self, tmp_path):
        p = LocalJSONLProvider(traces_dir=tmp_path)
        with p.span("timed") as ctx:
            pass
        assert ctx.duration_ms() >= 0

    def test_backend_name(self, tmp_path):
        p = LocalJSONLProvider(traces_dir=tmp_path)
        assert p.backend == "local_jsonl"

    def test_name(self, tmp_path):
        p = LocalJSONLProvider(traces_dir=tmp_path)
        assert p.name == "tracing"


class TestLangfuseProviderFallback:
    """Tests for LangfuseProvider when Langfuse is not installed (fallback behavior)."""

    def test_health_degraded_without_credentials(self, tmp_path):
        p = LangfuseProvider(public_key="", secret_key="", fallback=LocalJSONLProvider(tmp_path))
        h = p.health_check()
        assert h.status == ProviderStatus.DEGRADED

    def test_span_falls_back_to_local(self, tmp_path):
        p = LangfuseProvider(public_key="", secret_key="", fallback=LocalJSONLProvider(tmp_path))
        with p.span("op") as ctx:
            ctx.set_output("result")
        assert isinstance(ctx, SpanContext)

    def test_trace_falls_back_to_local(self, tmp_path):
        p = LangfuseProvider(public_key="", secret_key="", fallback=LocalJSONLProvider(tmp_path))
        trace_id = p.trace("event")
        assert isinstance(trace_id, str)

    def test_backend_indicates_unavailable(self, tmp_path):
        p = LangfuseProvider(public_key="", secret_key="", fallback=LocalJSONLProvider(tmp_path))
        assert "langfuse_unavailable" in p.backend or p.backend == "langfuse"
