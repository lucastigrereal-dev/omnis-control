"""P25 TaskClassifier — deterministic task classification for routing."""
from __future__ import annotations

from src.multi_model_orchestration.models import (
    CAPABILITY_ANALYSIS,
    CAPABILITY_CLASSIFICATION,
    CAPABILITY_CODE,
    CAPABILITY_PLANNING,
    CAPABILITY_SUMMARIZATION,
    CAPABILITY_TEXT,
    COMPLEXITY_CRITICAL,
    COMPLEXITY_HIGH,
    COMPLEXITY_LOW,
    COMPLEXITY_MEDIUM,
    TaskClass,
)

# ── Mapping: OMNIS intent → capability requirements ────────────────────────

_INTENT_CAPABILITY_MAP: dict[str, dict] = {
    # Classification / routing
    "classify_intent": {
        "complexity": COMPLEXITY_LOW,
        "capabilities": [CAPABILITY_CLASSIFICATION],
        "requires_precision": True,
    },
    "classify_sector": {
        "complexity": COMPLEXITY_LOW,
        "capabilities": [CAPABILITY_CLASSIFICATION],
        "requires_precision": True,
    },
    # Content generation
    "generate_caption": {
        "complexity": COMPLEXITY_MEDIUM,
        "capabilities": [CAPABILITY_TEXT, CAPABILITY_CLASSIFICATION],
        "requires_creativity": True,
    },
    "generate_hook": {
        "complexity": COMPLEXITY_MEDIUM,
        "capabilities": [CAPABILITY_TEXT, CAPABILITY_CLASSIFICATION],
        "requires_creativity": True,
    },
    # Summarization
    "summarize_mission": {
        "complexity": COMPLEXITY_LOW,
        "capabilities": [CAPABILITY_SUMMARIZATION, CAPABILITY_TEXT],
        "requires_precision": True,
    },
    "summarize_feedback": {
        "complexity": COMPLEXITY_LOW,
        "capabilities": [CAPABILITY_SUMMARIZATION],
    },
    # Analysis
    "analyze_lead": {
        "complexity": COMPLEXITY_MEDIUM,
        "capabilities": [CAPABILITY_ANALYSIS, CAPABILITY_TEXT],
        "requires_precision": True,
    },
    "analyze_metrics": {
        "complexity": COMPLEXITY_MEDIUM,
        "capabilities": [CAPABILITY_ANALYSIS, CAPABILITY_TEXT],
        "requires_precision": True,
    },
    "detect_trends": {
        "complexity": COMPLEXITY_MEDIUM,
        "capabilities": [CAPABILITY_ANALYSIS, CAPABILITY_TEXT],
        "requires_precision": True,
    },
    # Planning
    "plan_mission": {
        "complexity": COMPLEXITY_HIGH,
        "capabilities": [CAPABILITY_PLANNING, CAPABILITY_TEXT],
        "requires_precision": True,
    },
    "plan_campaign": {
        "complexity": COMPLEXITY_HIGH,
        "capabilities": [CAPABILITY_PLANNING, CAPABILITY_TEXT],
        "requires_precision": True,
    },
    "design_blueprint": {
        "complexity": COMPLEXITY_HIGH,
        "capabilities": [CAPABILITY_PLANNING, CAPABILITY_CODE],
        "requires_precision": True,
    },
    # Code generation
    "generate_code": {
        "complexity": COMPLEXITY_HIGH,
        "capabilities": [CAPABILITY_CODE, CAPABILITY_PLANNING],
        "requires_precision": True,
        "requires_creativity": True,
    },
    "scaffold_skill": {
        "complexity": COMPLEXITY_MEDIUM,
        "capabilities": [CAPABILITY_CODE],
        "requires_precision": True,
    },
    "generate_tests": {
        "complexity": COMPLEXITY_MEDIUM,
        "capabilities": [CAPABILITY_CODE, CAPABILITY_TEXT],
        "requires_precision": True,
    },
    # Critical actions
    "execute_financial": {
        "complexity": COMPLEXITY_CRITICAL,
        "capabilities": [CAPABILITY_ANALYSIS, CAPABILITY_TEXT],
        "requires_precision": True,
    },
    "send_communication": {
        "complexity": COMPLEXITY_MEDIUM,
        "capabilities": [CAPABILITY_TEXT, CAPABILITY_CLASSIFICATION],
        "requires_precision": True,
    },
}


class TaskClassifier:
    """Deterministic task → TaskClass mapping based on OMNIS intents."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    def classify(self, intent: str, risk_level: str = "low") -> TaskClass:
        """Map an OMNIS intent string to a TaskClass for routing."""
        mapping = _INTENT_CAPABILITY_MAP.get(intent)
        if mapping is None:
            return TaskClass.new(
                task_type=intent,
                complexity=COMPLEXITY_MEDIUM,
                risk_level=risk_level,
                min_capabilities=[CAPABILITY_TEXT],
            )

        return TaskClass.new(
            task_type=intent,
            complexity=mapping.get("complexity", COMPLEXITY_MEDIUM),
            risk_level=risk_level,
            requires_creativity=mapping.get("requires_creativity", False),
            requires_precision=mapping.get("requires_precision", False),
            min_capabilities=mapping.get("capabilities", [CAPABILITY_TEXT]),
        )

    def classify_batch(self, intents: list[str], risk_level: str = "low") -> list[TaskClass]:
        """Classify multiple intents at once."""
        return [self.classify(intent, risk_level) for intent in intents]

    def get_complexity(self, intent: str) -> str:
        """Quick lookup: return complexity for an intent without full TaskClass."""
        mapping = _INTENT_CAPABILITY_MAP.get(intent)
        return mapping["complexity"] if mapping else COMPLEXITY_MEDIUM

    def get_capabilities(self, intent: str) -> list[str]:
        """Quick lookup: return required capabilities for an intent."""
        mapping = _INTENT_CAPABILITY_MAP.get(intent)
        return mapping["capabilities"] if mapping else [CAPABILITY_TEXT]

    @property
    def known_intents(self) -> list[str]:
        """List all intents the classifier knows about."""
        return sorted(_INTENT_CAPABILITY_MAP.keys())
