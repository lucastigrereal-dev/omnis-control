"""Tests for memory_check checker."""
from __future__ import annotations

import pytest
import json


class TestMemoryCheck:
    def test_check_returns_dict_with_expected_keys(self, monkeypatch):
        """Memory check returns dict with overall, qdrant, akasha."""

        class MockQdrantResponse:
            status_code = 200

            def json(self):
                return {"result": {"collections": []}}

        def _mock_get(*args, **kwargs):
            return MockQdrantResponse()

        def _mock_subprocess_run(*args, **kwargs):
            return type("_", (), {
                "returncode": 1,
                "stdout": "",
                "stderr": "",
            })()

        monkeypatch.setattr("httpx.get", _mock_get)
        monkeypatch.setattr("subprocess.run", _mock_subprocess_run)

        from src.checkers.memory_check import check

        result = check()
        assert "overall" in result
        assert "qdrant" in result
        assert "akasha" in result

    def test_check_qdrant_accessible_with_collections(self, monkeypatch):
        class MockQdrantResponse:
            status_code = 200

            def json(self):
                return {
                    "result": {
                        "collections": [
                            {"name": "mem0"},
                            {"name": "akasha_docs"},
                        ]
                    }
                }

        monkeypatch.setattr("httpx.get", lambda *a, **kw: MockQdrantResponse())
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: type("_", (), {
                "returncode": 1, "stdout": "", "stderr": ""
            })(),
        )

        from src.checkers.memory_check import check

        result = check()
        assert result["qdrant"]["accessible"] is True
        assert result["qdrant"]["collections_count"] == 2
        assert "mem0" in result["qdrant"]["collections"]

    def test_check_qdrant_not_accessible(self, monkeypatch):
        def _mock_get(*args, **kwargs):
            raise Exception("connection refused")

        monkeypatch.setattr("httpx.get", _mock_get)
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: type("_", (), {
                "returncode": 1, "stdout": "", "stderr": ""
            })(),
        )

        from src.checkers.memory_check import check

        result = check()
        assert result["qdrant"]["accessible"] is False

    def test_check_akasha_container_found_healthy(self, monkeypatch):
        container = {
            "Names": "akasha-postgres",
            "Status": "Up 2 hours (healthy)",
        }

        monkeypatch.setattr("httpx.get", lambda *a, **kw: (_ for _ in ()).throw(Exception("no")))
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: type("_", (), {
                "returncode": 0,
                "stdout": json.dumps(container),
                "stderr": "",
            })(),
        )

        from src.checkers.memory_check import check

        result = check()
        assert result["akasha"]["container_found"] is True
        assert result["akasha"]["healthy"] is True

    def test_check_overall_error_when_both_unavailable(self, monkeypatch):
        monkeypatch.setattr("httpx.get", lambda *a, **kw: (_ for _ in ()).throw(Exception("no")))
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: type("_", (), {
                "returncode": 1, "stdout": "", "stderr": ""
            })(),
        )

        from src.checkers.memory_check import check

        result = check()
        assert result["overall"] == "error"

    def test_check_overall_warning_when_one_unavailable(self, monkeypatch):
        class MockQdrantResponse:
            status_code = 200

            def json(self):
                return {"result": {"collections": [{"name": "test"}]}}

        monkeypatch.setattr("httpx.get", lambda *a, **kw: MockQdrantResponse())
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: type("_", (), {
                "returncode": 1, "stdout": "", "stderr": ""
            })(),
        )

        from src.checkers.memory_check import check

        result = check()
        assert result["overall"] == "warning"
