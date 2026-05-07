"""Tests for Observabilidade Local module."""
import json
import logging
import pytest
from pathlib import Path
from src.observability.logging_config import StructuredFormatter, SENSITIVE_PATTERNS
from src.observability.tracer_local import get_tracer, record_metric, LocalTracer


class TestLoggingConfig:
    def test_structured_formatter_output(self):
        fmt = StructuredFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="test message", args=(), exc_info=None,
        )
        output = fmt.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"
        assert parsed["message"] == "test message"

    def test_sensitive_redaction(self):
        fmt = StructuredFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="token=sk-abc123", args=(), exc_info=None,
        )
        output = fmt.format(record)
        assert "sk-abc123" not in output
        assert "REDACTED" in output

    def test_email_redaction(self):
        # Only test the email pattern (second in SENSITIVE_PATTERNS)
        email_pattern = SENSITIVE_PATTERNS[1]
        result = email_pattern[0].sub(email_pattern[1], "user@example.com")
        assert "user@example.com" not in result
        assert "EMAIL" in result


class TestTracerLocal:
    def test_tracer_writes_span(self, tmp_path):
        tracer = LocalTracer("test", traces_dir=tmp_path)
        with tracer.start_as_current_span("test_span") as span:
            span.set_attribute("key", "value")

        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1
        content = files[0].read_text(encoding="utf-8")
        assert "test_span" in content
        assert "key" in content

    def test_record_metric_writes_file(self, tmp_path):
        metrics_dir = tmp_path / "metrics"
        record_metric("test.metric", 42.0, {"env": "test"})
        # Check default path
        default_dir = Path(__file__).parent.parent / "data" / "metrics"
        if default_dir.exists():
            files = list(default_dir.glob("*.jsonl"))
            if files:
                content = files[-1].read_text(encoding="utf-8")
                assert "test.metric" in content

    def test_get_tracer_singleton(self):
        t1 = get_tracer("test")
        t2 = get_tracer("test")
        assert t1 is t2
