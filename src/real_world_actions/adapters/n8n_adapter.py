"""P27 N8nAdapter — triggers n8n workflows via webhook. Dry-run safe."""
from src.real_world_actions.adapters import ActionAdapter, register_adapter


class N8nAdapter(ActionAdapter):
    """Thin wrapper for triggering n8n workflows."""

    @property
    def provider(self) -> str:
        return "n8n"

    @property
    def supported_actions(self) -> list[str]:
        return ["trigger_n8n_workflow"]

    def execute(self, action_name: str, params: dict) -> dict:
        if action_name != "trigger_n8n_workflow":
            return {"error": f"Unsupported action: {action_name}"}
        return {
            "status": "dry_run",
            "workflow_id": params.get("workflow_id", ""),
            "webhook_url": params.get("webhook_url", ""),
            "data": params.get("data", {}),
            "message": "[DRY-RUN] n8n workflow would be triggered",
        }

    def health_check(self) -> bool:
        return True

    def validate_params(self, action_name: str, params: dict) -> list[str]:
        errors = []
        if "workflow_id" not in params and "webhook_url" not in params:
            errors.append("Missing required field: workflow_id or webhook_url")
        return errors


def register() -> None:
    register_adapter(N8nAdapter())
