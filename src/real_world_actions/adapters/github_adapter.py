"""P27 GitHubAdapter — git operations via gh CLI. Dry-run safe."""
from src.real_world_actions.adapters import ActionAdapter, register_adapter


class GitHubAdapter(ActionAdapter):
    """Thin wrapper for GitHub operations (push, PR). Uses gh CLI under the hood."""

    @property
    def provider(self) -> str:
        return "github"

    @property
    def supported_actions(self) -> list[str]:
        return ["git_push", "create_pr"]

    def execute(self, action_name: str, params: dict) -> dict:
        if action_name == "git_push":
            return {
                "status": "dry_run",
                "branch": params.get("branch", ""),
                "remote": params.get("remote", "origin"),
                "message": "[DRY-RUN] Git push would execute via gh CLI",
            }
        if action_name == "create_pr":
            return {
                "status": "dry_run",
                "title": params.get("title", ""),
                "base": params.get("base", "main"),
                "head": params.get("head", ""),
                "message": "[DRY-RUN] PR would be created via gh CLI",
            }
        return {"error": f"Unsupported action: {action_name}"}

    def health_check(self) -> bool:
        return True

    def validate_params(self, action_name: str, params: dict) -> list[str]:
        errors = []
        if action_name == "git_push" and "branch" not in params:
            errors.append("Missing required field: branch")
        if action_name == "create_pr" and "title" not in params:
            errors.append("Missing required field: title")
        return errors


def register() -> None:
    register_adapter(GitHubAdapter())
