"""P27 EmailAdapter — sends emails via SMTP (Gmail). Dry-run safe."""
from src.real_world_actions.adapters import ActionAdapter, register_adapter


class EmailAdapter(ActionAdapter):
    """Thin wrapper around SMTP for sending emails. Always dry-run safe."""

    @property
    def provider(self) -> str:
        return "gmail"

    @property
    def supported_actions(self) -> list[str]:
        return ["send_email"]

    def execute(self, action_name: str, params: dict) -> dict:
        if action_name != "send_email":
            return {"error": f"Unsupported action: {action_name}"}
        return {
            "status": "dry_run",
            "to": params.get("to", ""),
            "subject": params.get("subject", ""),
            "body": params.get("body", ""),
            "message": "[DRY-RUN] Email would be sent via Gmail SMTP",
        }

    def health_check(self) -> bool:
        return True

    def validate_params(self, action_name: str, params: dict) -> list[str]:
        errors = []
        if "to" not in params:
            errors.append("Missing required field: to")
        return errors


def register() -> None:
    register_adapter(EmailAdapter())
