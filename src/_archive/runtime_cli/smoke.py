from dataclasses import dataclass, field

from src.runtime_cli.commands import run_command, list_commands


@dataclass
class SmokeResult:
    total: int = 0
    passed: int = 0
    failed: int = 0
    results: list[dict] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return self.total > 0 and self.failed == 0


def run_smoke_tests() -> SmokeResult:
    result = SmokeResult()
    tests = [
        ("status_ok", lambda: _check_ok(run_command("status"))),
        ("briefing_ok", lambda: _check_ok(run_command("briefing"))),
        ("approve_ok", lambda: _check_ok(run_command("approve", {"request_id": "test_1"}))),
        ("approve_missing_id", lambda: not run_command("approve")["ok"]),
        ("reject_ok", lambda: _check_ok(run_command("reject", {"request_id": "test_1", "reason": "test"}))),
        ("pending_ok", lambda: _check_ok(run_command("pending"))),
        ("run_skill_ok", lambda: _check_ok(run_command("run", {"skill": "test-skill"}))),
        ("list_commands", lambda: len(list_commands()) == 6),
        ("unknown_command", lambda: not run_command("nonexistent")["ok"]),
    ]

    for name, fn in tests:
        result.total += 1
        try:
            if fn():
                result.passed += 1
                result.results.append({"test": name, "status": "PASS"})
            else:
                result.failed += 1
                result.results.append({"test": name, "status": "FAIL"})
        except Exception as e:
            result.failed += 1
            result.results.append({"test": name, "status": "ERROR", "error": str(e)})

    return result


def _check_ok(response: dict) -> bool:
    return response.get("ok", False) is True
