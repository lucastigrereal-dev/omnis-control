"""P27 InstagramAdapter — publishes posts via Instagram Graph API. Dry-run safe."""
from src.real_world_actions.adapters import ActionAdapter, register_adapter


class InstagramAdapter(ActionAdapter):
    """Thin wrapper around Instagram Graph API for posting content."""

    @property
    def provider(self) -> str:
        return "instagram"

    @property
    def supported_actions(self) -> list[str]:
        return ["post_instagram"]

    def execute(self, action_name: str, params: dict) -> dict:
        if action_name != "post_instagram":
            return {"error": f"Unsupported action: {action_name}"}
        return {
            "status": "dry_run",
            "media_url": params.get("media_url", ""),
            "caption": params.get("caption", ""),
            "message": "[DRY-RUN] Post would be published via Instagram Graph API",
        }

    def health_check(self) -> bool:
        return True

    def validate_params(self, action_name: str, params: dict) -> list[str]:
        errors = []
        if "caption" not in params:
            errors.append("Missing required field: caption")
        return errors


def register() -> None:
    register_adapter(InstagramAdapter())
