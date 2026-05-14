"""P27 MockAdapter — safe mock for testing and dry-run."""
from src.real_world_actions.adapters import ActionAdapter, register_adapter


class MockAdapter(ActionAdapter):
    """Mock adapter that returns safe, predictable responses. Used for testing and dry-run previews."""

    @property
    def provider(self) -> str:
        return "mock"

    @property
    def supported_actions(self) -> list[str]:
        return ["health_check", "mock_action", "echo"]

    def execute(self, action_name: str, params: dict) -> dict:
        if action_name == "echo":
            return {"echo": params}
        if action_name == "health_check":
            return {"status": "healthy", "provider": "mock"}
        return {"status": "mock_ok", "action": action_name, "params": params}

    def health_check(self) -> bool:
        return True

    def validate_params(self, action_name: str, params: dict) -> list[str]:
        return []


def register() -> None:
    """Register MockAdapter in the adapter registry."""
    register_adapter(MockAdapter())
