"""W156 — Remote Control Command Dispatcher (routes commands to handlers, dry-run)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from .models import _new_id, _now_iso, CommandRisk, CommandStatus


DISPATCH_OK = "dispatched"
DISPATCH_BLOCKED = "blocked"
DISPATCH_NO_HANDLER = "no_handler"
DISPATCH_DRY_RUN = "dry_run"

HIGH_RISK_COMMANDS = {"rm_rf", "reset_hard", "force_push", "drop_db", "shutdown"}


@dataclass
class DispatchRequest:
    request_id: str
    command: str
    source: str
    payload: dict = field(default_factory=dict)
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, command: str, source: str, payload: Optional[dict] = None, dry_run: bool = True) -> "DispatchRequest":
        return cls(
            request_id=_new_id("dreq"),
            command=command,
            source=source,
            payload=payload or {},
            dry_run=dry_run,
        )

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "command": self.command,
            "source": self.source,
            "payload": self.payload,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }


@dataclass
class DispatchResult:
    result_id: str
    request_id: str
    status: str
    output: dict = field(default_factory=dict)
    error: str = ""
    completed_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "request_id": self.request_id,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "completed_at": self.completed_at,
        }


HandlerFn = Callable[[DispatchRequest], dict]


class CommandDispatcher:
    """Routes remote commands to registered handlers with safety checks."""

    def __init__(self) -> None:
        self._handlers: dict[str, HandlerFn] = {}

    def register(self, command: str, handler: HandlerFn) -> None:
        self._handlers[command] = handler

    def dispatch(self, request: DispatchRequest) -> DispatchResult:
        result_id = _new_id("dres")

        if request.command in HIGH_RISK_COMMANDS:
            return DispatchResult(
                result_id=result_id,
                request_id=request.request_id,
                status=DISPATCH_BLOCKED,
                error=f"Command '{request.command}' is blocked by safety policy",
            )

        if request.dry_run:
            return DispatchResult(
                result_id=result_id,
                request_id=request.request_id,
                status=DISPATCH_DRY_RUN,
                output={"simulated": True, "command": request.command, "payload": request.payload},
            )

        handler = self._handlers.get(request.command)
        if handler is None:
            return DispatchResult(
                result_id=result_id,
                request_id=request.request_id,
                status=DISPATCH_NO_HANDLER,
                error=f"No handler registered for command '{request.command}'",
            )

        output = handler(request)
        return DispatchResult(
            result_id=result_id,
            request_id=request.request_id,
            status=DISPATCH_OK,
            output=output,
        )

    def registered_commands(self) -> list[str]:
        return list(self._handlers.keys())
