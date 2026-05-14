"""P27 SlackAdapter — posts messages to Slack channels. Dry-run safe."""
from src.real_world_actions.adapters import ActionAdapter, register_adapter


class SlackAdapter(ActionAdapter):
    """Thin wrapper for sending Slack messages via webhook."""

    @property
    def provider(self) -> str:
        return "slack"

    @property
    def supported_actions(self) -> list[str]:
        return ["send_slack_message"]

    def execute(self, action_name: str, params: dict) -> dict:
        if action_name != "send_slack_message":
            return {"error": f"Unsupported action: {action_name}"}
        return {
            "status": "dry_run",
            "channel": params.get("channel", ""),
            "text": params.get("text", ""),
            "message": "[DRY-RUN] Slack message would be sent",
        }

    def health_check(self) -> bool:
        return True

    def validate_params(self, action_name: str, params: dict) -> list[str]:
        errors = []
        if "channel" not in params:
            errors.append("Missing required field: channel")
        if "text" not in params:
            errors.append("Missing required field: text")
        return errors


def register() -> None:
    register_adapter(SlackAdapter())
