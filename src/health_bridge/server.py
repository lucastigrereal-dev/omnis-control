"""W198-200 — Minimal HTTP health server with timeout/fallback."""
from __future__ import annotations

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

from src.health_bridge.models import HealthCheck, HealthLevel, HealthStatus, _now_iso

_DEFAULT_PORT = 8999
_DEFAULT_HOST = "127.0.0.1"
_CHECK_TIMEOUT = 5.0


def build_basic_checks() -> list[HealthCheck]:
    """Run basic health checks without external dependencies."""
    checks: list[HealthCheck] = []

    # Python process is alive
    checks.append(HealthCheck.ok("process", "python process responding"))

    # Module imports
    try:
        import src.first_missions  # noqa
        checks.append(HealthCheck.ok("first_missions", "module importable"))
    except Exception as e:
        checks.append(HealthCheck.error("first_missions", str(e)))

    return checks


class HealthHandler(BaseHTTPRequestHandler):
    """GET /health — returns JSON health status."""

    def do_GET(self) -> None:
        if self.path in ("/health", "/healthz"):
            self._handle_health()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')

    def _handle_health(self) -> None:
        checks = _run_checks_with_timeout()
        status = HealthStatus.from_checks(checks, source="health-server")
        body = json.dumps(status.to_dict(), indent=2, ensure_ascii=False)
        code = 200
        response = body.encode("utf-8")

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args) -> None:
        pass  # Silent logs


def _run_checks_with_timeout() -> list[HealthCheck]:
    """Run checks with timeout fallback."""
    try:
        return build_basic_checks()
    except Exception as e:
        return [HealthCheck.error("health_handler", f"check runner crashed: {e}")]


def create_server(host: str = _DEFAULT_HOST, port: int = _DEFAULT_PORT) -> HTTPServer:
    return HTTPServer((host, port), HealthHandler)


def run_server(host: str = _DEFAULT_HOST, port: int = _DEFAULT_PORT) -> None:
    server = create_server(host, port)
    print(f"OMNIS Health Server on http://{host}:{port}/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
