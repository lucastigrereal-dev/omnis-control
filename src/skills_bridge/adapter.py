from abc import ABC, abstractmethod

from src.skills_bridge.models import SkillCall, SkillIntent
from src.skills_bridge.selection import SkillSelector
from src.skills_bridge.dryrun import DryRunEngine

from src.multi_model_orchestration.models import (
    CAPABILITY_TEXT,
    CAPABILITY_CODE,
    CAPABILITY_ANALYSIS,
    COMPLEXITY_MEDIUM,
    COMPLEXITY_HIGH,
    ModelConfig,
    TaskClass,
    RoutingRequest,
)
from src.multi_model_orchestration.errors import AllModelsExhaustedError


def _capabilities_for_intent(intent: SkillIntent | str) -> list[str]:
    """Map SkillIntent to required model capabilities."""
    intent_val = intent.value if hasattr(intent, "value") else str(intent)
    mapping = {
        "create": [CAPABILITY_TEXT, CAPABILITY_CODE],
        "generate": [CAPABILITY_TEXT, CAPABILITY_CODE],
        "analyze": [CAPABILITY_ANALYSIS, CAPABILITY_TEXT],
        "read": [CAPABILITY_TEXT],
        "update": [CAPABILITY_TEXT, CAPABILITY_CODE],
        "publish": [CAPABILITY_TEXT],
        "notify": [CAPABILITY_TEXT],
        "delete": [CAPABILITY_TEXT],
    }
    return mapping.get(intent_val, [CAPABILITY_TEXT])


class SkillAdapter(ABC):

    @abstractmethod
    def call_skill(self, call: SkillCall) -> dict[str, object]:
        ...

    @abstractmethod
    def health_check(self) -> bool:
        ...


class MockSkillAdapter(SkillAdapter):

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.selector = SkillSelector(dry_run=dry_run)
        self.dryrun_engine = DryRunEngine(dry_run=dry_run)
        self.calls: list[SkillCall] = []

    def call_skill(self, call: SkillCall) -> dict[str, object]:
        self.calls.append(call)
        selection = self.selector.select(call)

        if selection.requires_manual_review:
            return {
                "status": "needs_manual_review",
                "selection": selection.to_dict(),
                "output": f"Skill '{call.skill_id or call.intent.value}' "
                          f"requires manual review",
            }

        if call.dry_run:
            return self.dryrun_engine.execute(call)

        return {
            "status": "executed",
            "skill_id": call.skill_id,
            "selection": selection.to_dict(),
            "output": f"Skill '{call.skill_id}' executed successfully",
        }

    def health_check(self) -> bool:
        return True


class RealSkillAdapter(SkillAdapter):
    """Real adapter that routes skill calls through ModelRouter → LLM providers."""

    def __init__(self, registry: object | None = None, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.calls: list[SkillCall] = []

        if registry is None:
            from src.multi_model_orchestration.registry import ModelRegistry
            registry = ModelRegistry()
            if not registry.count:
                registry.seed_defaults()
        self._registry = registry

        from src.multi_model_orchestration.router import ModelRouter
        self._router = ModelRouter(registry=self._registry, dry_run=dry_run)

    def call_skill(self, call: SkillCall) -> dict[str, object]:
        self.calls.append(call)

        if call.dry_run or self.dry_run:
            return {
                "status": "dry_run",
                "skill_id": call.skill_id,
                "output": f"[DRY_RUN] Skill '{call.skill_id}' would execute "
                          f"with intent '{call.intent.value}'",
            }

        prompt = call.input_payload.get("prompt", call.input_payload.get("topic", ""))
        if not prompt:
            prompt = f"Execute skill: {call.skill_id}"

        task = TaskClass.new(
            task_type=call.skill_id or "general",
            complexity=COMPLEXITY_MEDIUM,
            min_capabilities=_capabilities_for_intent(call.intent),
        )

        request = RoutingRequest.new(
            task=task,
            prompt=prompt,
            context=call.input_payload,
            dry_run=False,
        )

        try:
            result = self._router.execute(request)
        except AllModelsExhaustedError as e:
            return {
                "status": "failed",
                "skill_id": call.skill_id,
                "output": "",
                "error": str(e),
            }

        content = result.get("content", "")
        if isinstance(content, list):
            content = "\n".join(str(c) for c in content)

        return {
            "status": result.get("status", "failed"),
            "skill_id": call.skill_id,
            "output": content,
            "model_used": result.get("model", ""),
            "provider": result.get("provider", ""),
        }

    def health_check(self) -> bool:
        return self._registry.enabled_count > 0
