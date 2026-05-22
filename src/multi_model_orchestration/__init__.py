"""P25 Multi-Model Orchestration — routing tasks to the best available model."""
from src.multi_model_orchestration.models import (
    ModelConfig,
    TaskClass,
    RoutingRequest,
    RoutingDecision,
    COMPLEXITY_LOW,
    COMPLEXITY_MEDIUM,
    COMPLEXITY_HIGH,
    COMPLEXITY_CRITICAL,
    VALID_COMPLEXITIES,
    PROVIDER_ANTHROPIC,
    PROVIDER_OPENAI,
    PROVIDER_GROQ,
    PROVIDER_OLLAMA,
    PROVIDER_MOCK,
    CAPABILITY_TEXT,
    CAPABILITY_CODE,
    CAPABILITY_ANALYSIS,
    CAPABILITY_PLANNING,
)
from src.multi_model_orchestration.classifier import TaskClassifier
from src.multi_model_orchestration.registry import ModelRegistry
from src.multi_model_orchestration.router import ModelRouter
from src.multi_model_orchestration.fallback import FallbackChain
from src.multi_model_orchestration.cost_tracker import CostTracker
from src.multi_model_orchestration.errors import (
    MultiModelError,
    ProviderUnavailableError,
    RoutingError,
    CostLimitError,
    AllModelsExhaustedError,
    AdapterError,
    InvalidModelConfigError,
)

__all__ = [
    # Models
    "ModelConfig",
    "TaskClass",
    "RoutingRequest",
    "RoutingDecision",
    # Constants
    "COMPLEXITY_LOW",
    "COMPLEXITY_MEDIUM",
    "COMPLEXITY_HIGH",
    "COMPLEXITY_CRITICAL",
    "VALID_COMPLEXITIES",
    "PROVIDER_ANTHROPIC",
    "PROVIDER_OPENAI",
    "PROVIDER_GROQ",
    "PROVIDER_OLLAMA",
    "PROVIDER_MOCK",
    "CAPABILITY_TEXT",
    "CAPABILITY_CODE",
    "CAPABILITY_ANALYSIS",
    "CAPABILITY_PLANNING",
    # Core
    "TaskClassifier",
    "ModelRegistry",
    "ModelRouter",
    "FallbackChain",
    "CostTracker",
    # Errors
    "MultiModelError",
    "ProviderUnavailableError",
    "RoutingError",
    "CostLimitError",
    "AllModelsExhaustedError",
    "AdapterError",
    "InvalidModelConfigError",
]
