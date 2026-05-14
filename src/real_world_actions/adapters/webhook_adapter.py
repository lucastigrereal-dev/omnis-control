"""P27 WebhookAdapter — calls external webhooks via HTTP POST. Dry-run safe."""
from src.real_world_actions.adapters import ActionAdapter, register_adapter


class WebhookAdapter(ActionAdapter):
    """Thin wrapper for HTTP POST to external webhook URLs."""

    @property
    def provider(self) -> str:
        return "webhook"

    @property
    def supported_actions(self) -> list[str]:
        return ["call_webhook"]

    def execute(self, action_name: str, params: dict) -> dict:
        if action_name != "call_webhook":
            return {"error": f"Unsupported action: {action_name}"}
        return {
            "status": "dry_run",
            "url": params.get("url", ""),
            "payload": params.get("payload", {}),
            "headers": params.get("headers", {}),
            "message": "[DRY-RUN] Webhook would be POSTed to URL",
        }

    def health_check(self) -> bool:
        return True

    def validate_params(self, action_name: str, params: dict) -> list[str]:
        errors = []
        if "url" not in params:
            errors.append("Missing required field: url")
        return errors


def register() -> None:
    register_adapter(WebhookAdapter())
