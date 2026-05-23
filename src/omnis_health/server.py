"""Minimal HTTP health server — GET /health returns HealthReport JSON."""
from __future__ import annotations

import json
import os
import socket
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from types import ModuleType
from typing import Callable

from src.omnis_health.models import CheckResult, HealthReport, HealthStatus

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


def build_health_report(
    per_check_timeout_s: float = 10.0,
    total_timeout_s: float = 60.0,
) -> HealthReport:
    """Run doctor checks with timeouts and fallback.

    Args:
        per_check_timeout_s: Max seconds per individual check (default 10).
        total_timeout_s: Max seconds for all checks combined (default 60).

    Returns a HealthReport with degraded status on timeouts.
    """
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

    from src.checkers import disk_check, docker_check, publisher_check, memory_check, obsidian_check, skills_check, video_pipeline_check
    check_modules = [
        ("disk", disk_check),
        ("docker", docker_check),
        ("publisher", publisher_check),
        ("memory", memory_check),
        ("obsidian", obsidian_check),
        ("skills", skills_check),
        ("video_pipeline", video_pipeline_check),
    ]

    results: dict[str, CheckResult] = {}
    start_time = time.time()

    def _run_one(name: str, mod: ModuleType) -> CheckResult:
        check_start = time.time()
        try:
            data = mod.check()
            dur = int((time.time() - check_start) * 1000)
            return CheckResult(name=name, status=HealthStatus.OK, data=data, duration_ms=dur)
        except Exception as e:
            dur = int((time.time() - check_start) * 1000)
            return CheckResult(name=name, status=HealthStatus.ERROR, data={}, error=str(e), duration_ms=dur)

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {executor.submit(_run_one, name, mod): name for name, mod in check_modules}

        deadline = start_time + total_timeout_s
        pending = set(future_map.keys())

        for future in pending.copy():
            remaining = max(0.1, deadline - time.time())
            try:
                result = future.result(timeout=min(per_check_timeout_s, remaining))
                results[result.name] = result
                pending.discard(future)
            except FutureTimeoutError:
                name = future_map[future]
                elapsed = int((time.time() - start_time) * 1000)
                results[name] = CheckResult(
                    name=name,
                    status=HealthStatus.ERROR,
                    data={},
                    error=f"timeout after {per_check_timeout_s}s",
                    duration_ms=elapsed,
                )
                pending.discard(future)

    # Any checks that didn't even start (total timeout)
    for future in pending:
        name = future_map[future]
        results[name] = CheckResult(
            name=name,
            status=HealthStatus.ERROR,
            data={},
            error="total timeout exceeded",
            duration_ms=int(total_timeout_s * 1000),
        )

    normalized = [results[name] for name, _ in check_modules]

    error_count = sum(1 for c in normalized if c.status == HealthStatus.ERROR)
    if error_count == len(normalized):
        overall = HealthStatus.CRITICAL
    elif error_count > 0:
        overall = HealthStatus.WARNING
    else:
        overall = HealthStatus.OK

    return HealthReport(
        session_id="health-server",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        overall_status=overall,
        checks=normalized,
        risks=_collect_risks(normalized),
        next_steps=[],
    )


def _fallback_report(error_msg: str) -> HealthReport:
    """Absolute fallback — returns a valid report even when everything fails."""
    return HealthReport(
        session_id="health-server-fallback",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        overall_status=HealthStatus.CRITICAL,
        checks=[CheckResult(name="health-server", status=HealthStatus.CRITICAL, error=error_msg, data={})],
        risks=[error_msg],
        next_steps=["Investigate health server failure"],
    )


def _collect_risks(checks: list[CheckResult]) -> list[str]:
    """Collect risk messages from error checks."""
    risks = []
    for c in checks:
        if c.status == HealthStatus.ERROR:
            risks.append(f"{c.name}: {c.error}")
    return risks


class HealthRequestHandler(BaseHTTPRequestHandler):
    report_builder: Callable[[], HealthReport] = build_health_report

    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')
            return

        try:
            report = self.report_builder()
        except Exception as e:
            report = _fallback_report(str(e))

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

    def log_message(self, format: str, *args: object) -> None:
        pass


class HealthServer:
    """Minimal HTTP server exposing GET /health."""

    def __init__(
        self,
        port: int = 0,
        report_builder: Callable[[], HealthReport] | None = None,
        per_check_timeout_s: float = 10.0,
        total_timeout_s: float = 60.0,
    ):
        self._port = port or _pick_free_port()
        self._httpd: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.per_check_timeout_s = per_check_timeout_s
        self.total_timeout_s = total_timeout_s
        if report_builder:
            self._report_builder = report_builder
        else:
            self._report_builder = lambda: build_health_report(
                per_check_timeout_s=self.per_check_timeout_s,
                total_timeout_s=self.total_timeout_s,
            )

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
