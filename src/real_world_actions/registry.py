"""P27 ActionRegistry — catalogue of available real-world actions."""
from typing import Optional

from src.real_world_actions.models import ActionDefinition
from src.real_world_actions.errors import UnknownActionError


class ActionRegistry:
    """Catalogue of available real-world actions."""

    def __init__(self):
        self._actions: dict[str, ActionDefinition] = {}
        self._by_name: dict[str, str] = {}  # name → action_id

    # ── CRUD ──────────────────────────────────────────────────────

    def register(self, action: ActionDefinition) -> None:
        self._actions[action.action_id] = action
        self._by_name[action.name] = action.action_id

    def unregister(self, action_id: str) -> None:
        action = self._actions.pop(action_id, None)
        if action and action.name in self._by_name:
            del self._by_name[action.name]

    def get(self, action_id: str) -> ActionDefinition:
        if action_id not in self._actions:
            raise UnknownActionError(f"Action not found: {action_id}")
        return self._actions[action_id]

    def find(self, name: str) -> ActionDefinition:
        """Find by name. Raises UnknownActionError if not found."""
        action_id = self._by_name.get(name)
        if action_id is None:
            raise UnknownActionError(f"Action not found: {name}")
        return self._actions[action_id]

    def find_by_name(self, name: str) -> Optional[ActionDefinition]:
        """Look up by name. Returns None if not found."""
        action_id = self._by_name.get(name)
        if action_id is None:
            return None
        return self._actions.get(action_id)

    # ── Listing ───────────────────────────────────────────────────

    def list_all(self) -> list[ActionDefinition]:
        return list(self._actions.values())

    def list_enabled(self) -> list[ActionDefinition]:
        return [a for a in self._actions.values() if a.enabled]

    def list_by_provider(self, provider: str) -> list[ActionDefinition]:
        return [a for a in self._actions.values() if a.provider == provider]

    def list_by_risk(self, risk_level: str) -> list[ActionDefinition]:
        return [a for a in self._actions.values() if a.risk_level == risk_level]

    def list_by_type(self, action_type: str) -> list[ActionDefinition]:
        return [a for a in self._actions.values() if a.action_type == action_type]

    # ── Enable / disable ──────────────────────────────────────────

    def enable(self, action_id: str) -> None:
        self.get(action_id).enabled = True

    def disable(self, action_id: str) -> None:
        self.get(action_id).enabled = False

    # ── Query ─────────────────────────────────────────────────────

    @property
    def count(self) -> int:
        return len(self._actions)

    @property
    def enabled_count(self) -> int:
        return sum(1 for a in self._actions.values() if a.enabled)

    def provider_names(self) -> list[str]:
        return sorted(set(a.provider for a in self._actions.values()))

    def action_names(self) -> list[str]:
        return sorted(self._by_name.keys())

    # ── Seed defaults ─────────────────────────────────────────────

    def seed_defaults(self) -> None:
        """Register the standard action catalogue."""
        defaults = [
            ActionDefinition.new("send_email", "gmail", "send", description="Send email via Gmail SMTP"),
            ActionDefinition.new("post_instagram", "instagram", "send", description="Publish post to Instagram via Graph API"),
            ActionDefinition.new("call_webhook", "webhook", "send", description="POST to an external webhook URL"),
            ActionDefinition.new("git_push", "github", "deploy", description="Push commits to a GitHub repository"),
            ActionDefinition.new("create_pr", "github", "deploy", description="Create a GitHub pull request"),
            ActionDefinition.new("trigger_n8n_workflow", "n8n", "send", description="Trigger an n8n workflow via webhook"),
            ActionDefinition.new("send_slack_message", "slack", "send", description="Post message to Slack channel"),
            ActionDefinition.new("health_check", "mock", "read", description="Read-only health check — safe by default"),
        ]
        for action in defaults:
            self.register(action)

    def to_dict(self) -> dict:
        return {"actions": {k: v.to_dict() for k, v in self._actions.items()}}

    @classmethod
    def from_dict(cls, d: dict) -> "ActionRegistry":
        registry = cls()
        for action_data in d.get("actions", {}).values():
            registry.register(ActionDefinition.from_dict(action_data))
        return registry
