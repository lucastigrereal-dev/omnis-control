"""Tests for publisher_check checker."""
from __future__ import annotations

import pytest


class TestPublisherCheck:
    def test_check_port_closed_when_socket_fails(self, monkeypatch):
        """Returns port_closed when socket connection fails."""

        def _mock_create_connection(*args, **kwargs):
            raise ConnectionRefusedError()

        monkeypatch.setattr("socket.create_connection", _mock_create_connection)

        from src.checkers.publisher_check import check

        result = check()
        assert result["status"] == "port_closed"
        assert result["port_open"] is False

    def test_check_port_closed_on_timeout(self, monkeypatch):
        import socket

        def _mock_create_connection(*args, **kwargs):
            raise socket.timeout()

        monkeypatch.setattr("socket.create_connection", _mock_create_connection)

        from src.checkers.publisher_check import check

        result = check()
        assert result["status"] == "port_closed"

    def test_check_port_closed_on_oserror(self, monkeypatch):
        def _mock_create_connection(*args, **kwargs):
            raise OSError("network unreachable")

        monkeypatch.setattr("socket.create_connection", _mock_create_connection)

        from src.checkers.publisher_check import check

        result = check()
        assert result["status"] == "port_closed"

    def test_check_identifies_publisher_via_health(self, monkeypatch):
        """When port is open and /health returns publisher keyword."""

        class MockSocket:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class MockResponse:
            status_code = 200
            headers = {"content-type": "application/json"}

            def __init__(self, text):
                self.text = text

        class MockClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get(self, url, timeout=None):
                return MockResponse('{"status":"ok","publisher":"running"}')

        monkeypatch.setattr("socket.create_connection", lambda *a, **kw: MockSocket())
        monkeypatch.setattr("httpx.Client", MockClient)

        from src.checkers.publisher_check import check

        result = check()
        assert result["port_open"] is True
        assert result["identified"] is True
        assert result["status"] == "ok"

    def test_check_port_open_but_no_response(self, monkeypatch):
        """Port open but all endpoints fail."""

        class MockSocket:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class MockClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def get(self, url, timeout=None):
                from httpx import RequestError
                raise RequestError("connection failed")

        monkeypatch.setattr("socket.create_connection", lambda *a, **kw: MockSocket())
        monkeypatch.setattr("httpx.Client", MockClient)

        from src.checkers.publisher_check import check

        result = check()
        assert result["status"] == "port_open_no_response"
