"""Tests for W156 — Remote Control Command Dispatcher."""
import pytest
from src.remote_control.command_dispatcher import (
    CommandDispatcher, DispatchRequest,
    DISPATCH_OK, DISPATCH_BLOCKED, DISPATCH_NO_HANDLER, DISPATCH_DRY_RUN,
)


@pytest.fixture
def dispatcher():
    d = CommandDispatcher()
    d.register("status", lambda req: {"status": "ok"})
    d.register("list_missions", lambda req: {"missions": []})
    return d


def test_dry_run_default(dispatcher):
    req = DispatchRequest.new("status", "CLI")
    result = dispatcher.dispatch(req)
    assert result.status == DISPATCH_DRY_RUN
    assert result.output["simulated"] is True


def test_blocked_command(dispatcher):
    req = DispatchRequest.new("rm_rf", "CLI")
    result = dispatcher.dispatch(req)
    assert result.status == DISPATCH_BLOCKED


def test_no_handler_non_dry_run(dispatcher):
    req = DispatchRequest.new("unknown_cmd", "CLI", dry_run=False)
    result = dispatcher.dispatch(req)
    assert result.status == DISPATCH_NO_HANDLER


def test_dispatch_with_handler(dispatcher):
    req = DispatchRequest.new("status", "CLI", dry_run=False)
    result = dispatcher.dispatch(req)
    assert result.status == DISPATCH_OK
    assert result.output["status"] == "ok"


def test_registered_commands(dispatcher):
    cmds = dispatcher.registered_commands()
    assert "status" in cmds
    assert "list_missions" in cmds


def test_to_dict(dispatcher):
    req = DispatchRequest.new("status", "TELEGRAM")
    result = dispatcher.dispatch(req)
    d = result.to_dict()
    assert "status" in d
    assert "output" in d


def test_request_to_dict():
    req = DispatchRequest.new("ping", "CLI", payload={"msg": "hello"})
    d = req.to_dict()
    assert d["command"] == "ping"
    assert d["payload"]["msg"] == "hello"


def test_high_risk_commands_blocked(dispatcher):
    for cmd in ["rm_rf", "reset_hard", "force_push", "drop_db", "shutdown"]:
        req = DispatchRequest.new(cmd, "CLI")
        result = dispatcher.dispatch(req)
        assert result.status == DISPATCH_BLOCKED, f"{cmd} should be blocked"
