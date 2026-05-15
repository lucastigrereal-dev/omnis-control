COMMAND_REGISTRY = {}


def _register(name: str):
    def decorator(fn):
        COMMAND_REGISTRY[name] = fn
        return fn
    return decorator


@_register("status")
def cmd_status(args: dict) -> dict:
    return {
        "command": "status",
        "ok": True,
        "health": "HEALTHY",
        "modules": 9,
        "dry_run": True,
    }


@_register("briefing")
def cmd_briefing(args: dict) -> dict:
    return {
        "command": "briefing",
        "ok": True,
        "summary": "All systems operational. Dry-run mode active.",
    }


@_register("approve")
def cmd_approve(args: dict) -> dict:
    request_id = args.get("request_id", "")
    if not request_id:
        return {"command": "approve", "ok": False, "error": "Missing request_id"}
    return {
        "command": "approve",
        "ok": True,
        "request_id": request_id,
        "action": "APPROVED",
        "note": "Dry-run: approval simulated",
    }


@_register("reject")
def cmd_reject(args: dict) -> dict:
    request_id = args.get("request_id", "")
    reason = args.get("reason", "No reason provided")
    if not request_id:
        return {"command": "reject", "ok": False, "error": "Missing request_id"}
    return {
        "command": "reject",
        "ok": True,
        "request_id": request_id,
        "reason": reason,
        "action": "REJECTED",
        "note": "Dry-run: rejection simulated",
    }


@_register("pending")
def cmd_pending(args: dict) -> dict:
    return {
        "command": "pending",
        "ok": True,
        "pending_count": 0,
        "items": [],
    }


@_register("run")
def cmd_run(args: dict) -> dict:
    skill = args.get("skill", "")
    if not skill:
        return {"command": "run", "ok": False, "error": "Missing skill name"}
    return {
        "command": "run",
        "ok": True,
        "skill": skill,
        "status": "DRY_RUN_OK",
        "note": "Dry-run: no real execution",
    }


def run_command(command: str, args: dict | None = None) -> dict:
    args = args or {}
    handler = COMMAND_REGISTRY.get(command)
    if not handler:
        return {"ok": False, "error": f"Unknown command: {command}"}
    return handler(args)


def list_commands() -> list[str]:
    return sorted(COMMAND_REGISTRY.keys())
