"""Minimal HTTP health server — GET /health returns HealthReport JSON."""
from __future__ import annotations

import json
import os
import socket
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable

from src.omnis_health.models import HealthReport, HealthStatus

STATE_FILE = os.path.expanduser("~/.claude/health_server_state.json")


@dataclass
class ServerState:
    pid: int
    port: int
    started_at: str = ""


def save_server_state(state: ServerState) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(asdict(state), f)


def load_server_state() -> ServerState | None:
    if not os.path.isfile(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return ServerState(**data)
    except (json.JSONDecodeError, TypeError, KeyError):
        return None


def clear_server_state() -> None:
    if os.path.isfile(STATE_FILE):
        os.remove(STATE_FILE)


def is_server_alive() -> bool:
    """Check if a health server is running by reading state file and trying to connect."""
    state = load_server_state()
    if state is None:
        return False
    try:
        with socket.create_connection(("127.0.0.1", state.port), timeout=2):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        clear_server_state()
        return False


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def build_health_report() -> HealthReport:
    """Run doctor checks and build a HealthReport. Replaces inline with mocks in tests."""
    from src.checkers import disk_check, docker_check, publisher_check, memory_check, obsidian_check, skills_check, video_pipeline_check

    checks = {}
    errors_list = []

    for name, mod in [
        ("disk", disk_check),
        ("docker", docker_check),
        ("publisher", publisher_check),
        ("memory", memory_check),
        ("obsidian", obsidian_check),
        ("skills", skills_check),
        ("video_pipeline", video_pipeline_check),
    ]:
        try:
            checks[name] = mod.check()
        except Exception as e:
            checks[name] = {"error": str(e)}
            errors_list.append(str(e))

    if errors_list:
        overall = HealthStatus.CRITICAL
    else:
        overall = HealthStatus.OK

    from src.omnis_health.models import CheckResult
    normalized = []
    for name, data in checks.items():
        err = data.get("error") if isinstance(data, dict) else None
        status = HealthStatus.ERROR if err else HealthStatus.OK
        normalized.append(CheckResult(name=name, status=status, data=data, error=err))

    return HealthReport(
        session_id="health-server",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        overall_status=overall,
        checks=normalized,
        risks=[],
        next_steps=[],
    )


class HealthRequestHandler(BaseHTTPRequestHandler):
    report_builder: Callable[[], HealthReport] = build_health_report

    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')
            return

        report = self.report_builder()
        body = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)

        if report.overall_status == HealthStatus.CRITICAL:
            code = 503
        elif report.overall_status == HealthStatus.WARNING:
            code = 200
        else:
            code = 200

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args) -> None:
        pass


class HealthServer:
    """Minimal HTTP server exposing GET /health."""

    def __init__(self, port: int = 0, report_builder: Callable[[], HealthReport] | None = None):
        self._port = port or _pick_free_port()
        self._httpd: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._report_builder = report_builder or build_health_report

    @property
    def port(self) -> int:
        return self._port

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._port}"

    def start(self) -> int:
        handler = type("_Handler", (HealthRequestHandler,), {"report_builder": staticmethod(self._report_builder)})
        self._httpd = HTTPServer(("127.0.0.1", self._port), handler)
        self._port = self._httpd.server_port
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self._port

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def is_running(self) -> bool:
        return self._httpd is not None and self._thread is not None and self._thread.is_alive()
